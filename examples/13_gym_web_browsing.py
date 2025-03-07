#!/usr/bin/env python3
"""
commandAGI Gym Web Browsing Example

This example demonstrates how to use the commandAGI gym framework to automate a web browsing task.
It creates a custom environment that rewards the agent for successfully completing web browsing tasks.

Status: Not tested
- Requires additional dependencies (pytesseract)
- Modified to use a mock agent but still needs dependencies
- Test attempted: 2024-07-12
"""

import time
import os
import base64
import io
import traceback
from typing import Dict, Any
from PIL import Image

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
        KeyboardKeyPressAction,
        ComputerAction,
        ClickAction,
        MouseMoveAction,
        MouseClickAction,
        MouseButton,
    )
    from commandAGI.processors.screen_parser.pytesseract_screen_parser import (
        parse_screenshot,
    )
except ImportError:
    print(
        "Error: Required modules not found. Make sure commandAGI is installed with the required extras:"
    )
    print("pip install commandagi[local,gym,pytesseract]")
    exit(1)


class WebBrowsingEnv(ComputerEnv):
    """Custom environment for web browsing tasks."""

    def __init__(self, config: ComputerEnvConfig):
        super().__init__(config)
        self.task_completed = False
        self.steps_taken = 0
        self.max_steps = 30  # Maximum number of steps before ending the episode
        self.task_description = "Open a web browser, navigate to example.com, and find the 'More information' link."
        self.browser_opened = False
        self.navigated_to_site = False
        self.found_target = False
        self.target_text = "More information"

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

    def get_reward(self, action: ComputerAction) -> float:
        """
        Define a reward function for web browsing tasks.

        Rewards:
        - Small negative reward for each step (encourages efficiency)
        - Reward for opening a browser
        - Reward for navigating to the target site
        - Large reward for finding the target element
        """
        # Small negative reward for each step to encourage efficiency
        reward = -0.1

        # Check if the action is executing a command (opening a browser)
        if action.command is not None and not self.browser_opened:
            if (
                "chrome" in action.command.command.lower()
                or "firefox" in action.command.command.lower()
            ):
                reward += 2.0
                self.browser_opened = True
                print("Browser opened! +2.0 reward")

        # Check if the action is typing a URL
        if action.type is not None and not self.navigated_to_site:
            if "example.com" in action.type.text:
                reward += 3.0
                self.navigated_to_site = True
                print("Navigated to example.com! +3.0 reward")

        # Check if the target text is visible on the screen
        if not self.found_target and self.navigated_to_site:
            # Get the screenshot
            screenshot = self._computer.get_screenshot()

            try:
                # Parse the screenshot to extract text
                parsed_screenshot = parse_screenshot(screenshot.screenshot)

                # Check if the target text is in any of the extracted elements
                for element in parsed_screenshot.elements:
                    if self.target_text.lower() in element.text.lower():
                        reward += 5.0
                        self.found_target = True
                        self.task_completed = True
                        print(f"Found target text '{self.target_text}'! +5.0 reward")

                        # Save the screenshot with the target highlighted
                        img_data = base64.b64decode(screenshot.screenshot)
                        img = Image.open(io.BytesIO(img_data))
                        screenshot_path = "output/web_target_found.png"
                        img.save(screenshot_path)
                        print(f"Screenshot saved to {screenshot_path}")

                        break
            except Exception as e:
                print(f"Error parsing screenshot: {e}")

        # Increment step counter
        self.steps_taken += 1

        return reward

    def get_done(self, action: ComputerAction) -> bool:
        """
        Determine if the episode is done.

        The episode is done if:
        - The task is completed (target found)
        - The maximum number of steps is reached
        """
        return self.task_completed or self.steps_taken >= self.max_steps

    def reset(self):
        """Reset the environment."""
        self.task_completed = False
        self.steps_taken = 0
        self.browser_opened = False
        self.navigated_to_site = False
        self.found_target = False
        return super().reset()

    def get_info(self) -> Dict[str, Any]:
        """Get additional information about the environment state."""
        return {
            "task_completed": self.task_completed,
            "steps_taken": self.steps_taken,
            "browser_opened": self.browser_opened,
            "navigated_to_site": self.navigated_to_site,
            "found_target": self.found_target,
            "task_description": self.task_description,
        }


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
        # Simulate web browsing by moving the mouse and typing a URL
        if self.steps_taken == 0:
            # First action: Move mouse to address bar area
            return ComputerAction(
                mouse_move=MouseMoveAction(x=300, y=50, move_duration=0.5)
            )
        elif self.steps_taken == 1:
            # Second action: Click on address bar
            return ComputerAction(
                mouse_click=MouseClickAction(
                    x=300, y=50, button=MouseButton.LEFT, move_duration=0.5
                )
            )
        elif self.steps_taken == 2:
            # Third action: Type a URL
            return ComputerAction(type=TypeAction(text="example.com"))
        else:
            # Default action: Move mouse around
            return ComputerAction(
                mouse_move=MouseMoveAction(x=400, y=300, move_duration=0.5)
            )

    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the reward."""
        if not hasattr(self, "steps_taken"):
            self.steps_taken = 0
        self.steps_taken += 1

    def reset(self) -> None:
        """Reset the agent's internal state."""
        self.steps_taken = 0


def main():
    print("commandAGI Gym Web Browsing Example")
    print("===================================")
    print("This example demonstrates how to use the commandAGI gym framework")
    print("to automate a web browsing task.")
    print()
    print(
        "Task: Open a web browser, navigate to example.com, and find the 'More information' link."
    )
    print()

    try:
        # Configure the environment
        print("Configuring the environment...")
        config = ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            computer_cls_kwargs={},
        )

        # Create the custom web browsing environment
        print("Creating the web browsing environment...")
        env = WebBrowsingEnv(config)

        # Enable logging of modality errors for debugging
        from commandAGI.gym.environments.multimodal_env import MultiModalEnv

        MultiModalEnv._LOG_MODALITY_ERRORS = True

        # Create a mock agent instead of the NaiveComputerAgent
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
        print(f"Task completed: {env.task_completed}")
        print(f"Browser opened: {env.browser_opened}")
        print(f"Navigated to site: {env.navigated_to_site}")
        print(f"Found target: {env.found_target}")

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
