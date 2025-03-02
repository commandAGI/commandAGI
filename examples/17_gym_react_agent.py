#!/usr/bin/env python3
"""
CommandLAB Gym React Agent Example

This example demonstrates how to use the CommandLAB gym framework with the ReactComputerAgent.
It shows how to create an environment and agent, and collect an episode using the ReAct framework.

Status: not tested
"""

import time
import os
import traceback
from typing import Dict, Any

try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
    from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandLAB.gym.agents.react_vision_language_computer_agent import (
        ReactComputerAgent,
    )
    from commandLAB.gym.drivers import SimpleDriver
    from commandLAB.types import (
        ShellCommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
        ComputerAction,
    )
except ImportError as e:
    print(f"Detailed import error: {e}")
    print("Traceback:")
    traceback.print_exc()
    print(
        "Error: Required modules not found. Make sure CommandLAB is installed with the required extras:"
    )
    print("pip install commandlab[local,gym]")
    exit(1)


class TextEditingTask(ComputerEnv):
    """Custom environment for text editing tasks."""

    def __init__(self, config: ComputerEnvConfig, computer=None):
        super().__init__(config, computer=computer)
        self.task_completed = False
        self.steps_taken = 0
        self.max_steps = 20  # Maximum number of steps before ending the episode
        self.task_description = (
            "Open a text editor, type 'Hello from ReactAgent!', and save the file."
        )
        self.editor_opened = False
        self.text_typed = False
        self.file_saved = False

    def get_reward(self, action: ComputerAction) -> float:
        """Define a reward function for text editing tasks."""
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
            if "Hello from ReactAgent!" in action.type.text:
                reward += 3.0
                self.text_typed = True
                print("Target text typed! +3.0 reward")

        # Check if the action is saving the file (Ctrl+S)
        if (
            action.keyboard_hotkey is not None
            and self.text_typed
            and not self.file_saved
        ):
            keys = action.keyboard_hotkey.keys
            if KeyboardKey.CTRL in keys and KeyboardKey.S in keys:
                reward += 5.0
                self.file_saved = True
                self.task_completed = True
                print("File saved! +5.0 reward")

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
        self.file_saved = False
        return super().reset()

    def get_info(self) -> Dict[str, Any]:
        """Get additional information about the environment state."""
        return {
            "task_completed": self.task_completed,
            "steps_taken": self.steps_taken,
            "editor_opened": self.editor_opened,
            "text_typed": self.text_typed,
            "file_saved": self.file_saved,
            "task_description": self.task_description,
        }


def main():
    print("CommandLAB Gym React Agent Example")
    print("==================================")
    print(
        "This example demonstrates how to use the CommandLAB gym framework with the ReactComputerAgent."
    )
    print(
        "It will create an environment and agent, and collect an episode using the ReAct framework."
    )
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
        env = TextEditingTask(config, computer=computer)

        # Create a React agent
        print("Creating the React agent...")
        # Note: This requires a Hugging Face model
        agent = ReactComputerAgent(
            model="mistralai/Mistral-7B-Instruct-v0.2",  # Use an appropriate model
            device="cpu",  # Use "cuda" if you have a GPU
        )

        # Create a driver
        print("Creating the driver...")
        driver = SimpleDriver(env=env, agent=agent)

        # Collect an episode
        print("Collecting an episode...")
        print("This will take a screenshot and use the agent to decide on actions.")
        print("Press Ctrl+C to stop the episode collection.")
        print()
        print("Starting in 3 seconds...")
        time.sleep(3)

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
        traceback.print_exc()
    finally:
        # Clean up resources
        if "driver" in locals():
            driver.close()
            print("Resources cleaned up.")


if __name__ == "__main__":
    main()
