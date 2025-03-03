#!/usr/bin/env python3
"""
commandAGI2 Simple Gym Test

This is a simplified version of the gym example that uses the proper implementation classes.

Status: Working
- Successfully initializes the environment, agent, and driver
- Successfully moves the mouse to the specified position (100, 100)
- Demonstrates basic gym framework functionality
"""

import time
import os
import traceback

try:
    from commandAGI2.computers.local_pynput_computer import LocalPynputComputer
    from commandAGI2.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandAGI2.gym.agents.naive_vision_language_computer_agent import (
        NaiveComputerAgent,
    )
    from commandAGI2.gym.drivers import SimpleDriver
    from commandAGI2.types import (
        ShellCommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
        ComputerAction,
        ComputerObservation,
        MouseMoveAction,
    )
    from commandAGI2.gym.schema import Episode
except ImportError as e:
    print(f"Detailed import error: {e}")
    print("Traceback:")
    traceback.print_exc()
    print(
        "Error: Required modules not found. Make sure commandAGI2 is installed with the required extras:"
    )
    print("pip install commandagi2[local,gym]")
    exit(1)


# Create a simple mock agent that doesn't require OpenAI API
class SimpleMockAgent(NaiveComputerAgent):
    """A simple mock agent that doesn't require OpenAI API."""

    def __init__(self):
        # Initialize with dummy chat_model_options
        super().__init__(
            chat_model_options={
                "model_provider": "openai",  # Required by get_chat_model
                "model": "gpt-4o",  # Required by ChatOpenAI
                "api_key": "dummy-api-key",  # Dummy API key
            }
        )
        # Override the chat_model and str_output_parser to avoid API calls
        self.chat_model = None
        self.str_output_parser = None

    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Given an observation, determine the next action."""
        # Just return a simple mouse move action
        return ComputerAction(
            mouse_move=MouseMoveAction(x=100, y=100, move_duration=0.5)
        )


def main():
    print("commandAGI2 Simple Gym Test")
    print("==========================")
    print("This is a simplified version of the gym example.")
    print()

    try:
        # Create the environment with an explicit computer instance
        print("Creating the environment...")
        computer = LocalPynputComputer()
        config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
        )
        env = ComputerEnv(config, computer=computer)

        # Enable logging of modality errors for debugging
        from commandAGI2.gym.environments.multimodal_env import MultiModalEnv

        MultiModalEnv._LOG_MODALITY_ERRORS = True

        # Create a mock agent
        print("Creating the agent...")
        agent = SimpleMockAgent()

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
