#!/usr/bin/env python3
"""
commandAGI Gym Simple Agent Example

This example demonstrates how to use the commandAGI gym framework with the built-in agents.
It shows how to create a simple environment and agent, and collect an episode.

Status: not tested
"""

import time
import os
import traceback

try:
    from commandAGI.computers.local_pynput_computer import LocalPynputComputer
    from commandAGI.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandAGI.gym.agents.naive_vision_language_computer_agent import (
        NaiveComputerAgent,
    )
    from commandAGI.gym.drivers import SimpleDriver
    from commandAGI.types import (
        ShellCommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
    )
except ImportError as e:
    print(f"Detailed import error: {e}")
    print("Traceback:")
    traceback.print_exc()
    print(
        "Error: Required modules not found. Make sure commandAGI is installed with the required extras:"
    )
    print("pip install commandagi[local,gym]")
    exit(1)


def main():
    print("commandAGI Gym Simple Agent Example")
    print("===================================")
    print(
        "This example demonstrates how to use the commandAGI gym framework with the built-in agents."
    )
    print("It will create a simple environment and agent, and collect an episode.")
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
        env = ComputerEnv(config, computer=computer)

        # Create an agent using the NaiveComputerAgent from the gym
        print("Creating the agent...")
        # Note: This requires an OpenAI API key or other LLM provider
        agent = NaiveComputerAgent(
            chat_model_options={
                "model_provider": "openai",
                "model": "gpt-4-vision-preview",
                # Add your API key here if not set as environment variable
                # "api_key": "your-api-key",
            }
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
