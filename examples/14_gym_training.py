#!/usr/bin/env python3
"""
CommandLAB Gym Training Example

This example demonstrates how to use the CommandLAB gym framework to train an agent
over multiple episodes. It shows how to collect episodes, evaluate performance,
and save/load trained agents.

Status: not tested
"""

import time
import os
import json
import pickle
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


class TrainableAgent(NaiveComputerAgent):
    """Extended agent that can be trained on episodes."""
    
    def __init__(self, chat_model_options: dict):
        super().__init__(chat_model_options)
        self.training_history = []
        self.episode_rewards = []
        self.completion_rate = []
        self.episodes_seen = 0
    
    def train(self, episodes: List[Episode]) -> None:
        """Train the agent on a list of episodes."""
        for episode in episodes:
            # In a real implementation, this would update the agent's model
            # For this example, we just track statistics
            total_reward = sum(step.reward for step in episode)
            self.episode_rewards.append(total_reward)
            
            # Check if the task was completed
            last_info = episode[-1].info
            task_completed = last_info.get("task_completed", False)
            self.completion_rate.append(1.0 if task_completed else 0.0)
            
            self.episodes_seen += 1
            
            # Add to training history
            self.training_history.append({
                "episode": self.episodes_seen,
                "total_reward": total_reward,
                "steps": episode.num_steps,
                "task_completed": task_completed,
            })
    
    def save(self, path: str) -> None:
        """Save the agent to a file."""
        with open(path, "wb") as f:
            pickle.dump({
                "training_history": self.training_history,
                "episode_rewards": self.episode_rewards,
                "completion_rate": self.completion_rate,
                "episodes_seen": self.episodes_seen,
            }, f)
        
        # Also save as JSON for easier inspection
        with open(f"{path}.json", "w") as f:
            json.dump({
                "training_history": self.training_history,
                "episode_rewards": self.episode_rewards,
                "completion_rate": self.completion_rate,
                "episodes_seen": self.episodes_seen,
            }, f, indent=2)
    
    def load(self, path: str) -> None:
        """Load the agent from a file."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.training_history = data["training_history"]
            self.episode_rewards = data["episode_rewards"]
            self.completion_rate = data["completion_rate"]
            self.episodes_seen = data["episodes_seen"]
    
    def plot_training_progress(self, save_path: str) -> None:
        """Plot the training progress."""
        if not self.episode_rewards:
            print("No training data to plot.")
            return
        
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot episode rewards
        episodes = range(1, len(self.episode_rewards) + 1)
        ax1.plot(episodes, self.episode_rewards, 'b-')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Total Reward')
        ax1.set_title('Episode Rewards')
        ax1.grid(True)
        
        # Plot completion rate (moving average)
        window_size = min(10, len(self.completion_rate))
        if window_size > 0:
            moving_avg = np.convolve(self.completion_rate, np.ones(window_size)/window_size, mode='valid')
            ax2.plot(range(window_size, len(self.completion_rate) + 1), moving_avg, 'r-')
            ax2.set_xlabel('Episode')
            ax2.set_ylabel('Completion Rate (Moving Avg)')
            ax2.set_title(f'Task Completion Rate (Window Size: {window_size})')
            ax2.grid(True)
            ax2.set_ylim([0, 1.1])
        
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        
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

        # Create a trainable agent
        print("Creating the trainable agent...")
        agent = TrainableAgent(chat_model_options={
            "model_provider": "openai",
            "model": "gpt-4-vision-preview",
            # Add your API key here if not set as environment variable
            # "api_key": "your-api-key",
        })

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