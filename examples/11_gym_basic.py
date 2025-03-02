#!/usr/bin/env python3
"""
CommandLAB Gym Basic Example

This example demonstrates how to use the CommandLAB gym framework to create an environment,
agent, and collect an episode. It shows the basic structure of a reinforcement learning
setup with CommandLAB.

Status: Working but doesn't stop
- Successfully initializes the environment, agent, and driver
- Successfully moves the mouse to the specified position (100, 100)
- Demonstrates basic gym framework functionality
- Test Date: 2024-07-12
"""

import time
import os
import traceback
import random
from typing import List, Optional

try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
    from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandLAB.gym.agents.base_agent import BaseAgent
    from commandLAB.gym.drivers import SimpleDriver
    from commandLAB.types import (
        ShellCommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
        ComputerAction,
        ComputerObservation,
        MouseMoveAction,
    )
    from commandLAB.gym.schema import Episode
    from pydantic import Field
except ImportError as e:
    print(f"Detailed import error: {e}")
    print("Traceback:")
    traceback.print_exc()
    print(
        "Error: Required modules not found. Make sure CommandLAB is installed with the required extras:"
    )
    print("pip install commandlab[local,gym]")
    exit(1)


# Create a simple mock agent for testing
class MockAgent(BaseAgent[ComputerObservation, ComputerAction]):
    """A simple mock agent that returns random actions for testing."""

    total_reward: float = Field(default=0.0)

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        """Reset the agent's internal state."""
        self.total_reward = 0.0

    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Given an observation, determine the next action."""
        # Use a mouse move action that should work
        return ComputerAction(
            mouse_move=MouseMoveAction(x=100, y=100, move_duration=0.5)
        )

    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the reward."""
        self.total_reward += reward

    def train(self, episodes: list[Episode]) -> None:
        """Train the agent on an episode."""
        pass


def main():
    print("CommandLAB Gym Basic Example")
    print("============================")
    print("This example demonstrates how to use the CommandLAB gym framework.")
    print("It will create an environment, agent, and collect an episode.")
    print()

    try:
        # Configure the environment with explicit LocalPynputComputer
        print("Configuring the environment...")
        config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
            # You can add on_reset_python, on_start_python, etc. here
        )

        # Create the environment with an explicit computer instance
        print("Creating the environment...")
        computer = LocalPynputComputer()
        env = ComputerEnv(config, computer=computer)

        # Enable logging of modality errors for debugging
        from commandLAB.gym.environments.multimodal_env import MultiModalEnv

        MultiModalEnv._LOG_MODALITY_ERRORS = True

        # Create a mock agent instead of the NaiveComputerAgent
        print("Creating the agent...")
        agent = MockAgent()

        # Create a driver
        print("Creating the driver...")
        driver = SimpleDriver(env=env, agent=agent)

        # Collect an episode
        print("Collecting an episode...")
        print("This will take a screenshot and use the agent to decide on actions.")
        print("Press Ctrl+C to stop the episode collection.")
        print()
        print("Starting in 1 second...")
        time.sleep(1)

        # Collect the episode
        episode = driver.collect_episode()

        # Print episode statistics
        print("\nEpisode collection complete!")
        print(f"Episode length: {episode.num_steps} steps")
        print(f"Total reward: {sum(step.reward for step in episode)}")

        # Print the actions taken
        print("\nActions taken:")
        for i, step in enumerate(episode):
            print(f"Step {i+1}: {step.action}")

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
