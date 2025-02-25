#!/usr/bin/env python3
"""
CommandLAB Gym Text Editing Example

This example demonstrates how to use the CommandLAB gym framework to automate a text editing task.
It creates a custom environment that rewards the agent for successfully completing text editing tasks.

Status: not tested
"""

import time
import os
from typing import Dict, Any

try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
    from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandLAB.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent
    from commandLAB.gym.drivers import SimpleDriver
    from commandLAB.types import (
        CommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
        KeyboardKeyPressAction,
        ComputerAction,
    )
except ImportError:
    print("Error: Required modules not found. Make sure CommandLAB is installed with the required extras:")
    print("pip install commandlab[local,gym]")
    exit(1)


class TextEditingEnv(ComputerEnv):
    """Custom environment for text editing tasks."""

    def __init__(self, config: ComputerEnvConfig):
        super().__init__(config)
        self.task_completed = False
        self.steps_taken = 0
        self.max_steps = 20  # Maximum number of steps before ending the episode
        self.task_description = "Open a text editor, type 'Hello, CommandLAB!', and save the file."

    def get_reward(self, action: ComputerAction) -> float:
        """
        Define a reward function for text editing tasks.
        
        Rewards:
        - Small positive reward for each action (encourages exploration)
        - Large positive reward for completing the task
        - Small negative reward for each step (encourages efficiency)
        """
        # Small negative reward for each step to encourage efficiency
        reward = -0.1
        
        # Check if the action is typing text
        if action.type is not None:
            # Reward for typing text
            reward += 0.5
            
            # Extra reward if the text contains the target phrase
            if "Hello, CommandLAB!" in action.type.text:
                reward += 2.0
        
        # Reward for using keyboard shortcuts (like Ctrl+S for saving)
        if action.keyboard_hotkey is not None:
            keys = action.keyboard_hotkey.keys
            if KeyboardKey.CTRL in keys and KeyboardKey.S in keys:
                reward += 3.0
                self.task_completed = True
        
        # Increment step counter
        self.steps_taken += 1
        
        return reward

    def get_done(self, action: ComputerAction) -> bool:
        """
        Determine if the episode is done.
        
        The episode is done if:
        - The task is completed (file saved)
        - The maximum number of steps is reached
        """
        return self.task_completed or self.steps_taken >= self.max_steps

    def reset(self):
        """Reset the environment."""
        self.task_completed = False
        self.steps_taken = 0
        return super().reset()

    def get_info(self) -> Dict[str, Any]:
        """Get additional information about the environment state."""
        return {
            "task_completed": self.task_completed,
            "steps_taken": self.steps_taken,
            "task_description": self.task_description,
        }


def main():
    print("CommandLAB Gym Text Editing Example")
    print("===================================")
    print("This example demonstrates how to use the CommandLAB gym framework")
    print("to automate a text editing task.")
    print()
    print("Task: Open a text editor, type 'Hello, CommandLAB!', and save the file.")
    print()

    try:
        # Configure the environment
        print("Configuring the environment...")
        config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
        )

        # Create the custom text editing environment
        print("Creating the text editing environment...")
        env = TextEditingEnv(config)

        # Create an agent
        print("Creating the agent...")
        # Note: This requires an OpenAI API key or other LLM provider
        agent = NaiveComputerAgent(chat_model_options={
            "model_provider": "openai",
            "model": "gpt-4-vision-preview",
            # Add your API key here if not set as environment variable
            # "api_key": "your-api-key",
        })

        # Create a driver
        print("Creating the driver...")
        driver = SimpleDriver(env=env, agent=agent)

        # Collect an episode
        print("Collecting an episode...")
        print("This will take a screenshot and use the agent to decide on actions.")
        print("The agent will try to complete the text editing task.")
        print("Press Ctrl+C to stop the episode collection.")
        print()
        print("Starting in 3 seconds...")
        time.sleep(3)

        # Open a text editor before starting the episode
        print("Opening a text editor...")
        if os.name == "nt":  # Windows
            env._computer.execute_command(CommandAction(command="notepad", timeout=5))
        elif os.uname().sysname == "Darwin":  # macOS
            env._computer.execute_command(CommandAction(command="open -a TextEdit", timeout=5))
        else:  # Linux
            env._computer.execute_command(CommandAction(command="gedit", timeout=5))
        
        time.sleep(2)  # Wait for the editor to open

        # Collect the episode
        episode = driver.collect_episode()

        # Print episode statistics
        print("\nEpisode collection complete!")
        print(f"Episode length: {episode.num_steps} steps")
        print(f"Total reward: {sum(step.reward for step in episode)}")
        print(f"Task completed: {env.task_completed}")

        # Print the actions taken
        print("\nActions taken:")
        for i, step in enumerate(episode):
            print(f"Step {i+1}: {step.action}")
            print(f"  Reward: {step.reward}")

    except KeyboardInterrupt:
        print("\nEpisode collection interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Clean up resources
        if "driver" in locals():
            driver.close()
            print("Resources cleaned up.")


if __name__ == "__main__":
    main() 