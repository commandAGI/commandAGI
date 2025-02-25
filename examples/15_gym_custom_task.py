#!/usr/bin/env python3
"""
CommandLAB Gym Custom Task Example

This example demonstrates how to create and use a custom task with the CommandLAB gym framework.
It shows how to define task-specific goals, rewards, and evaluation criteria.

Status: Not tested
- Requires modification to use a mock agent
- Likely requires additional dependencies
- Test attempted: 2024-07-12
"""

import time
import os
from typing import Dict, Any, List, Optional

try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
    from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandLAB.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent
    from commandLAB.gym.drivers import SimpleDriver
    from commandLAB.gym.tasks.base import BaseTask
    from commandLAB.gym.tasks.computer_task import ComputerTaskMixin
    from commandLAB.gym.schema import Episode
    from commandLAB.types import (
        CommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
        KeyboardKeyPressAction,
        ComputerAction,
        ComputerObservation,
    )
except ImportError:
    print("Error: Required modules not found. Make sure CommandLAB is installed with the required extras:")
    print("pip install commandlab[local,gym]")
    exit(1)


class CalculatorTask(ComputerTaskMixin):
    """
    A task that requires the agent to open the calculator app and perform a calculation.
    """
    
    def __init__(self, calculation: str, expected_result: str):
        super().__init__()
        self.description = f"Open the calculator app and calculate {calculation}."
        self.env_config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
        )
        self.calculation = calculation
        self.expected_result = expected_result
    
    def evaluate(self, env: ComputerEnv, episode: Episode[ComputerObservation, ComputerAction]) -> bool:
        """
        Evaluate if the task was completed successfully.
        
        Returns:
            bool: True if the task was completed successfully, False otherwise.
        """
        # Check if the calculator was opened
        calculator_opened = False
        calculation_performed = False
        
        # Analyze the actions taken
        for step in episode:
            action = step.action
            
            # Check if the calculator was opened
            if action.command is not None:
                cmd = action.command.command.lower()
                if "calc" in cmd or "calculator" in cmd:
                    calculator_opened = True
            
            # Check if the calculation was performed
            if action.type is not None and calculator_opened:
                text = action.type.text
                if self.calculation in text:
                    calculation_performed = True
        
        # Get the final state from the environment
        if hasattr(env, "result_found") and env.result_found:
            return True
        
        return calculator_opened and calculation_performed


class CalculatorEnv(ComputerEnv):
    """Custom environment for calculator tasks."""

    def __init__(self, config: ComputerEnvConfig, calculation: str, expected_result: str):
        super().__init__(config)
        self.task_completed = False
        self.steps_taken = 0
        self.max_steps = 20  # Maximum number of steps before ending the episode
        self.calculation = calculation
        self.expected_result = expected_result
        self.task_description = f"Open the calculator app and calculate {calculation}."
        self.calculator_opened = False
        self.calculation_performed = False
        self.result_found = False
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

    def get_reward(self, action: ComputerAction) -> float:
        """
        Define a reward function for calculator tasks.
        
        Rewards:
        - Small negative reward for each step (encourages efficiency)
        - Reward for opening the calculator
        - Reward for performing the calculation
        - Large reward for getting the correct result
        """
        # Small negative reward for each step to encourage efficiency
        reward = -0.1
        
        # Check if the action is executing a command (opening the calculator)
        if action.command is not None and not self.calculator_opened:
            cmd = action.command.command.lower()
            if "calc" in cmd or "calculator" in cmd:
                reward += 2.0
                self.calculator_opened = True
                print("Calculator opened! +2.0 reward")
        
        # Check if the action is typing the calculation
        if action.type is not None and self.calculator_opened and not self.calculation_performed:
            text = action.type.text
            if self.calculation in text:
                reward += 3.0
                self.calculation_performed = True
                print(f"Calculation '{self.calculation}' performed! +3.0 reward")
        
        # Check if the action is pressing Enter or = to get the result
        if self.calculation_performed and not self.result_found:
            if (action.keyboard_key_press is not None and 
                (action.keyboard_key_press.key == KeyboardKey.ENTER or 
                 action.keyboard_key_press.key == "=")):
                reward += 5.0
                self.result_found = True
                self.task_completed = True
                print("Result found! +5.0 reward")
        
        # Increment step counter
        self.steps_taken += 1
        
        return reward

    def get_done(self, action: ComputerAction) -> bool:
        """
        Determine if the episode is done.
        
        The episode is done if:
        - The task is completed (result found)
        - The maximum number of steps is reached
        """
        return self.task_completed or self.steps_taken >= self.max_steps

    def reset(self):
        """Reset the environment."""
        self.task_completed = False
        self.steps_taken = 0
        self.calculator_opened = False
        self.calculation_performed = False
        self.result_found = False
        return super().reset()

    def get_info(self) -> Dict[str, Any]:
        """Get additional information about the environment state."""
        return {
            "task_completed": self.task_completed,
            "steps_taken": self.steps_taken,
            "calculator_opened": self.calculator_opened,
            "calculation_performed": self.calculation_performed,
            "result_found": self.result_found,
            "task_description": self.task_description,
        }


def main():
    print("CommandLAB Gym Custom Task Example")
    print("==================================")
    print("This example demonstrates how to create and use a custom task")
    print("with the CommandLAB gym framework.")
    print()

    # Define the calculation task
    calculation = "2 + 2"
    expected_result = "4"
    
    print(f"Task: Open the calculator app and calculate {calculation}.")
    print(f"Expected result: {expected_result}")
    print()

    try:
        # Create the task
        print("Creating the calculator task...")
        task = CalculatorTask(calculation=calculation, expected_result=expected_result)
        
        # Configure the environment
        print("Configuring the environment...")
        config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
        )

        # Create the custom calculator environment
        print("Creating the calculator environment...")
        env = CalculatorEnv(config, calculation=calculation, expected_result=expected_result)

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
        print("The agent will try to complete the calculator task.")
        print("Press Ctrl+C to stop the episode collection.")
        print()
        print("Starting in 3 seconds...")
        time.sleep(3)

        # Collect the episode
        episode = driver.collect_episode()

        # Evaluate the task
        print("\nEvaluating task completion...")
        task_success = task.evaluate(env, episode)
        
        # Print episode statistics
        print("\nEpisode collection complete!")
        print(f"Episode length: {episode.num_steps} steps")
        print(f"Total reward: {sum(step.reward for step in episode)}")
        print(f"Task completed: {env.task_completed}")
        print(f"Task evaluation: {'Success' if task_success else 'Failure'}")

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