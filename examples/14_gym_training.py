#!/usr/bin/env python3
"""
CommandLAB Gym Training Example

This example demonstrates how to use the CommandLAB gym framework to train an agent
over multiple episodes. It shows how to collect episodes, evaluate performance,
and save/load trained agents.

Status: Not tested
- Requires additional dependencies (matplotlib)
- Modified to use a mock agent but still needs dependencies
- Test attempted: 2024-07-12
"""

import time
import os
import json
import pickle
import traceback
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import numpy as np

try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
    from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandLAB.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent
    from commandLAB.gym.drivers import SimpleDriver
    from commandLAB.gym.trainer import OnlineTrainer
    from commandLAB.gym.schema import Episode, Step
    from commandLAB.types import (
        CommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
        ComputerAction,
        MouseMoveAction,
        MouseClickAction,
        MouseButton,
    )
except ImportError:
    print("Error: Required modules not found. Make sure CommandLAB is installed with the required extras:")
    print("pip install commandlab[local,gym]")
    print("pip install matplotlib numpy")  # For plotting
    exit(1)


class SimpleTaskEnv(ComputerEnv):
    """Simple environment for training an agent on basic tasks."""

    def __init__(self, config: ComputerEnvConfig):
        super().__init__(config)
        self.task_completed = False
        self.steps_taken = 0
        self.max_steps = 15  # Maximum number of steps before ending the episode
        self.task_description = "Open a text editor and type a simple message."
        self.editor_opened = False
        self.text_typed = False
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        os.makedirs("output/training", exist_ok=True)

    def get_reward(self, action: ComputerAction) -> float:
        """Define a reward function for the simple task."""
        # Small negative reward for each step to encourage efficiency
        reward = -0.1
        
        # Check if the action is executing a command (opening a text editor)
        if action.command is not None and not self.editor_opened:
            if "notepad" in action.command.command.lower() or "gedit" in action.command.command.lower():
                reward += 2.0
                self.editor_opened = True
                print("Text editor opened! +2.0 reward")
        
        # Check if the action is typing text
        if action.type is not None and self.editor_opened and not self.text_typed:
            if len(action.type.text) > 5:  # Require a meaningful amount of text
                reward += 3.0
                self.text_typed = True
                self.task_completed = True
                print("Text typed! +3.0 reward")
        
        # Increment step counter
        self.steps_taken += 1
        
        return reward

    def get_done(self, action: ComputerAction) -> bool:
        """Determine if the episode is done."""
        return self.task_completed or self.steps_taken >= self.max_steps

    def reset(self):
        """Reset the environment."""
        self.task_completed = False
        self.steps_taken = 0
        self.editor_opened = False
        self.text_typed = False
        return super().reset()

    def get_info(self) -> Dict[str, Any]:
        """Get additional information about the environment state."""
        return {
            "task_completed": self.task_completed,
            "steps_taken": self.steps_taken,
            "editor_opened": self.editor_opened,
            "text_typed": self.text_typed,
            "task_description": self.task_description,
        }


# Create a simple mock agent that doesn't require OpenAI API
class SimpleMockTrainableAgent(NaiveComputerAgent):
    """A simple mock trainable agent that doesn't require OpenAI API."""
    
    def __init__(self):
        # Initialize with dummy chat_model_options
        super().__init__(chat_model_options={
            "model_provider": "openai",  # Required by get_chat_model
            "model": "gpt-4o",  # Required by ChatOpenAI
            "api_key": "dummy-api-key"  # Dummy API key
        })
        # Override the chat_model and str_output_parser to avoid API calls
        self.chat_model = None
        self.str_output_parser = None
        
        # Training metrics
        self.training_history = {
            "episode_rewards": [],
            "episode_lengths": [],
            "task_completion_rate": []
        }
        self.steps_taken = 0
        
    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Given an observation, determine the next action."""
        # Simulate text editing by moving the mouse and typing
        if self.steps_taken == 0:
            # First action: Move mouse to text area
            return ComputerAction(
                mouse_move=MouseMoveAction(x=300, y=300, move_duration=0.5)
            )
        elif self.steps_taken == 1:
            # Second action: Click on text area
            return ComputerAction(
                mouse_click=MouseClickAction(
                    x=300, y=300, 
                    button=MouseButton.LEFT,
                    move_duration=0.5
                )
            )
        elif self.steps_taken == 2:
            # Third action: Type some text
            return ComputerAction(
                type=TypeAction(text="Hello from training agent!")
            )
        else:
            # Default action: Move mouse around
            return ComputerAction(
                mouse_move=MouseMoveAction(x=400, y=300, move_duration=0.5)
            )
            
    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the reward."""
        if not hasattr(self, 'steps_taken'):
            self.steps_taken = 0
        self.steps_taken += 1
        
    def reset(self) -> None:
        """Reset the agent's internal state."""
        self.steps_taken = 0
        
    def train(self, episodes: List[Episode]) -> None:
        """Train the agent on episodes."""
        print(f"Training on {len(episodes)} episodes...")
        
        # Extract metrics from episodes
        total_reward = sum(sum(step.reward for step in episode) for episode in episodes)
        avg_episode_length = sum(len(episode) for episode in episodes) / len(episodes)
        
        # Update training history
        self.training_history["episode_rewards"].append(total_reward / len(episodes))
        self.training_history["episode_lengths"].append(avg_episode_length)
        
        # Calculate task completion rate
        completion_rate = sum(1 for episode in episodes if any(step.info.get("task_completed", False) for step in episode)) / len(episodes)
        self.training_history["task_completion_rate"].append(completion_rate)
        
        print(f"Average reward: {total_reward / len(episodes):.2f}")
        print(f"Average episode length: {avg_episode_length:.2f}")
        print(f"Task completion rate: {completion_rate:.2f}")
        
    def save(self, path: str) -> None:
        """Save the agent's training history."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.training_history, f)
        print(f"Agent saved to {path}")
        
    def load(self, path: str) -> None:
        """Load the agent's training history."""
        with open(path, "rb") as f:
            self.training_history = pickle.load(f)
        print(f"Agent loaded from {path}")
        
    def plot_training_progress(self, save_path: str) -> None:
        """Plot the agent's training progress."""
        if not self.training_history["episode_rewards"]:
            print("No training history to plot.")
            return
            
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))
        
        # Plot episode rewards
        ax1.plot(self.training_history["episode_rewards"])
        ax1.set_title("Average Episode Reward")
        ax1.set_xlabel("Training Iteration")
        ax1.set_ylabel("Reward")
        
        # Plot episode lengths
        ax2.plot(self.training_history["episode_lengths"])
        ax2.set_title("Average Episode Length")
        ax2.set_xlabel("Training Iteration")
        ax2.set_ylabel("Steps")
        
        # Plot task completion rate
        ax3.plot(self.training_history["task_completion_rate"])
        ax3.set_title("Task Completion Rate")
        ax3.set_xlabel("Training Iteration")
        ax3.set_ylabel("Completion Rate")
        
        plt.tight_layout()
        plt.savefig(save_path)
        print(f"Training progress plot saved to {save_path}")


def main():
    print("CommandLAB Gym Training Example")
    print("===============================")
    print("This example demonstrates how to use the CommandLAB gym framework")
    print("to train an agent over multiple episodes.")
    print()

    try:
        # Configure the environment
        print("Configuring the environment...")
        config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
        )

        # Create the training environment
        print("Creating the training environment...")
        env = SimpleTaskEnv(config)
        
        # Enable logging of modality errors for debugging
        from commandLAB.gym.environments.multimodal_env import MultiModalEnv
        MultiModalEnv._LOG_MODALITY_ERRORS = True

        # Create a mock trainable agent
        print("Creating the trainable agent...")
        agent = SimpleMockTrainableAgent()

        # Create a driver
        print("Creating the driver...")
        driver = SimpleDriver(env=env, agent=agent)

        # Create a trainer
        print("Creating the trainer...")
        trainer = OnlineTrainer(driver=driver, agent=agent)

        # Number of episodes to train for
        num_episodes = 3  # Adjust as needed
        
        print(f"Training for {num_episodes} episodes...")
        print("Press Ctrl+C to stop training.")
        print()
        print("Starting in 1 second...")
        time.sleep(1)
        
        try:
            # Train the agent
            episodes = trainer.train(num_episodes)
            
            # Print training statistics
            print("\nTraining complete!")
            print(f"Episodes trained: {len(episodes)}")
            print(f"Average episode length: {sum(ep.num_steps for ep in episodes) / len(episodes):.2f} steps")
            print(f"Average reward: {sum(agent.episode_rewards) / len(agent.episode_rewards):.2f}")
            print(f"Completion rate: {sum(agent.completion_rate) / len(agent.completion_rate):.2%}")
            
            # Save the trained agent
            agent_path = "output/training/trained_agent.pkl"
            agent.save(agent_path)
            print(f"Trained agent saved to {agent_path}")
            
            # Plot training progress
            plot_path = "output/training/training_progress.png"
            agent.plot_training_progress(plot_path)
            
        except KeyboardInterrupt:
            print("\nTraining interrupted by user.")
            if agent.episodes_seen > 0:
                # Save the partially trained agent
                agent_path = "output/training/partial_trained_agent.pkl"
                agent.save(agent_path)
                print(f"Partially trained agent saved to {agent_path}")
                
                # Plot training progress
                plot_path = "output/training/partial_training_progress.png"
                agent.plot_training_progress(plot_path)

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Clean up resources
        if "driver" in locals():
            driver.close()
            print("Resources cleaned up.")


if __name__ == "__main__":
    main() 