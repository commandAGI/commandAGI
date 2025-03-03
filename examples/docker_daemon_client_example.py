#!/usr/bin/env python3
"""
Docker Daemon Client Example

This example demonstrates how to use the Docker provisioner to create a daemon computer client
and send various commands to it. The Docker provisioner will automatically start a container
with the commandAGI2 daemon running, and the client will connect to it.

Note: This example requires Docker to be installed and running on your system.

Usage:
    python docker_daemon_client_example.py
"""

import time
import random
import logging
import traceback
import sys
import os
from pathlib import Path
from typing import Optional

from commandAGI2.computers.daemon_client_computer import DaemonClientComputer
from commandAGI2.computers.provisioners.docker_provisioner import (
    DockerProvisioner,
    DockerPlatform,
)
from commandAGI2.computers.provisioners.base_provisioner import BaseComputerProvisioner
from commandAGI2.version import get_container_version
from commandAGI2.types import (
    KeyboardKey,
    MouseButton,
    TypeAction,
    MouseMoveAction,
    ClickAction,
    KeyboardHotkeyAction,
    ShellCommandAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseScrollAction,
    DragAction,
    DoubleClickAction,
    KeyboardKeyPressAction,
)


def main():
    # Setup logging to file
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "docker_daemon_client_example.log"

    # Configure logging to both console and file
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("daemon_client_example")
    logger.info("=== Docker Daemon Client Example ===")
    logger.info("Starting Docker daemon client example")

    # Create a Docker provisioner
    try:
        logger.info("Creating Docker provisioner...")
        container_version = get_container_version()
        logger.info(f"Using container version: {container_version}")

        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.LOCAL,
            container_name="commandagi2-daemon-example",
            version=container_version,  # Use the default container version
            max_retries=3,
            timeout=60,  # 1 minute timeout
        )
        logger.info("Docker provisioner created successfully")
    except Exception as e:
        logger.error(f"Error creating Docker provisioner: {e}")
        logger.error(traceback.format_exc())
        return

    # Create a daemon client computer with the Docker provisioner
    computer = None
    try:
        logger.info("Initializing DaemonClientComputer with Docker provisioner...")
        computer = DaemonClientComputer(
            daemon_base_url="http://localhost",
            daemon_port=8000,
            daemon_token="my-token",  # This should match the token used in the daemon
            provisioner=provisioner,
        )

        logger.info("Docker container started successfully!")
        logger.info("Waiting for daemon to be ready...")
        time.sleep(3)  # Give the daemon time to start

        # Example 1: Get system information
        logger.info("\n=== Example 1: Get System Information ===")
        command_action = ShellCommandAction(command="uname -a")
        success = computer.shell(command=command_action.command)
        logger.info(f"Command execution success: {success}")

        # Example 2: Type some text
        logger.info("\n=== Example 2: Typing Text ===")
        success = computer.execute_type(text="Hello from commandAGI2 Docker!")
        logger.info(f"Type action success: {success}")

        # Example 3: Move the mouse
        logger.info("\n=== Example 3: Moving Mouse ===")
        # Get the display information first
        displays = computer.get_displays()
        if displays and displays.displays:
            display = displays.displays[0]
            width, height = display.width, display.height
            logger.info(f"Display dimensions: {width}x{height}")

            # Move to a random position within the display
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            success = computer.execute_mouse_move(x=x, y=y, move_duration=0.5)
            logger.info(f"Mouse moved to ({x}, {y}), success: {success}")
        else:
            logger.info("No display information available")

        # Example 4: Take a screenshot
        logger.info("\n=== Example 4: Taking Screenshot ===")
        screenshot = computer.get_screenshot(format="path")
        if screenshot and screenshot.path:
            logger.info(f"Screenshot saved to: {screenshot.path}")
        else:
            logger.info("Failed to take screenshot")

        # Example 5: Press keyboard keys
        logger.info("\n=== Example 5: Keyboard Actions ===")
        # Press a single key
        success = computer.execute_keyboard_key_press(key=KeyboardKey.A)
        logger.info(f"Key press (A) success: {success}")

        # Press a hotkey combination (Ctrl+C)
        success = computer.execute_keyboard_hotkey(
            keys=[KeyboardKey.CTRL, KeyboardKey.C]
        )
        logger.info(f"Hotkey (Ctrl+C) success: {success}")

        # Example 6: Mouse actions
        logger.info("\n=== Example 6: Mouse Actions ===")
        if displays and displays.displays:
            # Click at a position
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            success = computer.execute_click(
                x=x, y=y, move_duration=0.3, press_duration=0.1, button=MouseButton.LEFT
            )
            logger.info(f"Click at ({x}, {y}) success: {success}")

            # Double click
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            success = computer.execute_double_click(
                x=x, y=y, move_duration=0.3, button=MouseButton.LEFT
            )
            logger.info(f"Double click at ({x}, {y}) success: {success}")

            # Drag operation
            start_x, start_y = random.randint(0, width - 1), random.randint(
                0, height - 1
            )
            end_x, end_y = random.randint(0, width - 1), random.randint(0, height - 1)
            success = computer.execute_drag(
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                move_duration=0.5,
                button=MouseButton.LEFT,
            )
            logger.info(
                f"Drag from ({start_x}, {start_y}) to ({end_x}, {end_y}) success: {success}"
            )

        # Example 7: Run a process
        logger.info("\n=== Example 7: Running a Process ===")
        success = computer.run_process(command="ls", args=["-la", "/"], timeout=5)
        logger.info(f"Process execution success: {success}")

        # Example 8: Get observation
        logger.info("\n=== Example 8: Getting Observation ===")
        observation = computer.get_observation()
        logger.info(
            "Observation keys: %s",
            list(observation.keys()) if observation else "No observation data",
        )

        # Example 9: Get mouse and keyboard state
        logger.info("\n=== Example 9: Getting Input Device States ===")
        mouse_state = computer.get_mouse_state()
        logger.info(f"Mouse position: {mouse_state.position}")
        logger.info(f"Mouse buttons: {mouse_state.buttons}")

        keyboard_state = computer.get_keyboard_state()
        logger.info(f"Number of keyboard keys tracked: {len(keyboard_state.keys)}")
        logger.info(
            f"Keys currently pressed: {[k for k, v in keyboard_state.keys.items() if v]}"
        )

        logger.info("\nAll examples completed successfully!")

    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Clean up resources
        if computer:
            logger.info("\nCleaning up resources...")
            try:
                computer.stop()
                logger.info("Docker container stopped and removed.")
            except Exception as e:
                logger.error(f"Error stopping computer: {e}")
                logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
