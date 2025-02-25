#!/usr/bin/env python3
"""
CommandLAB Gym Multi-Episode Training Example

This example demonstrates how to train an agent over multiple episodes using the CommandLAB gym framework.
It shows how to collect episodes, evaluate performance, and track training progress.

Status: not tested
"""

import time
import os
import json
import pickle
from typing import Dict, Any, List
import traceback

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Warning: matplotlib and numpy are required for plotting. Install with:")
    print("pip install matplotlib numpy")

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
except ImportError as e:
    print(f"Detailed import error: {e}")
    print("Traceback:")
    traceback.print_exc()
    print("Error: Required modules not found. Make sure CommandLAB is installed with the required extras:")
    print("pip install commandlab[local,gym]")
    exit(1)


class SimpleTaskEnv(ComputerEnv):
    """Simple environment for training an agent on basic tasks."""

    def __init__(self, config: ComputerEnvConfig, computer=None):
        super().__init__(config, computer=computer)
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
            cmd = action.command.command.lower()
            if "notepad" in cmd or "gedit" in cmd or "textedit" in cmd:
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


class TrackingAgent(NaiveComputerAgent):
    """Agent that tracks training progress."""
    
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
    
    def save_history(self, path: str) -> None:
        """Save the training history to a file."""
        # Save as JSON for easier inspection
        with open(path, "w") as f:
            json.dump({
                "training_history": self.training_history,
                "episode_rewards": self.episode_rewards,
                "completion_rate": self.completion_rate,
                "episodes_seen": self.episodes_seen,
            }, f, indent=2)
        
        print(f"Training history saved to {path}")
    
    def plot_training_progress(self, save_path: str) -> None:
        """Plot the training progress."""
        if not self.episode_rewards:
            print("No training data to plot.")
            return
        
        try:
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
        except Exception as e:
            print(f"Error plotting training progress: {e}")
            print("Make sure matplotlib and numpy are installed.")


def main():
    print("CommandLAB Gym Multi-Episode Training Example")
    print("============================================")
    print("This example demonstrates how to train an agent over multiple episodes")
    print("using the CommandLAB gym framework.")
    print()

    try:
        # Create a computer instance directly
        print("Creating a computer instance...")
        computer = LocalPynputComputer()

        # Configure the environment
        print("Configuring the environment...")
        config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
        )

        # Create the environment with the computer instance
        print("Creating the environment...")
        env = SimpleTaskEnv(config, computer=computer)

        # Create a tracking agent
        print("Creating the tracking agent...")
        agent = TrackingAgent(chat_model_options={
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
            
            # Save the training history
            history_path = "output/training/training_history.json"
            agent.save_history(history_path)
            
            # Plot training progress
            plot_path = "output/training/training_progress.png"
            agent.plot_training_progress(plot_path)
            
        except KeyboardInterrupt:
            print("\nTraining interrupted by user.")
            if agent.episodes_seen > 0:
                # Save the training history
                history_path = "output/training/partial_training_history.json"
                agent.save_history(history_path)
                
                # Plot training progress
                plot_path = "output/training/partial_training_progress.png"
                agent.plot_training_progress(plot_path)

    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
    finally:
        # Clean up resources
        if "driver" in locals():
            driver.close()
            print("Resources cleaned up.")


if __name__ == "__main__":
    main() 