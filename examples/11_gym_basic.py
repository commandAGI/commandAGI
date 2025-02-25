#!/usr/bin/env python3
"""
CommandLAB Gym Basic Example

This example demonstrates how to use the CommandLAB gym framework to create an environment,
agent, and collect an episode. It shows the basic structure of a reinforcement learning
setup with CommandLAB.

Status: not tested
"""

import time
import os
import traceback

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
    )
except ImportError as e:
    print(f"Detailed import error: {e}")
    print("Traceback:")
    traceback.print_exc()
    print("Error: Required modules not found. Make sure CommandLAB is installed with the required extras:")
    print("pip install commandlab[local,gym]")
    exit(1)


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

        # Create an agent
        print("Creating the agent...")
        # Note: This requires an OpenAI API key or other LLM provider
        # You can set OPENAI_API_KEY environment variable or pass it directly
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