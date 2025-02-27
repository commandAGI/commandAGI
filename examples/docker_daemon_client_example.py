#!/usr/bin/env python3
"""
Docker Daemon Client Example

This example demonstrates how to use the Docker provisioner to create a daemon computer client
and send various commands to it. The Docker provisioner will automatically start a container
with the CommandLAB daemon running, and the client will connect to it.

Note: This example requires Docker to be installed and running on your system.

Usage:
    python docker_daemon_client_example.py
"""

import time
import random
from pathlib import Path

from commandLAB.computers.daemon_client_computer import DaemonClientComputer
from commandLAB.computers.provisioners.docker_provisioner import DockerProvisioner, DockerPlatform
from commandLAB.version import get_container_version
from commandLAB.types import (
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
    print("=== Docker Daemon Client Example ===")
    print("Starting Docker container with CommandLAB daemon...")

    # Create a Docker provisioner
    provisioner = DockerProvisioner(
        port=8000,
        platform=DockerPlatform.LOCAL,
        container_name="commandlab-daemon-example",
        version=get_container_version(),  # Use the default container version
        max_retries=3,
        timeout=60,  # 1 minute timeout
    )

    # Create a daemon client computer with the Docker provisioner
    computer = None
    try:
        print("Initializing DaemonClientComputer with Docker provisioner...")
        computer = DaemonClientComputer(
            daemon_base_url="http://localhost",
            daemon_port=8000,
            daemon_token="my-token",  # This should match the token used in the daemon
            provisioner=provisioner,
        )
        
        print("Docker container started successfully!")
        print("Waiting for daemon to be ready...")
        time.sleep(3)  # Give the daemon time to start
        
        # Example 1: Get system information
        print("\n=== Example 1: Get System Information ===")
        command_action = ShellCommandAction(command="uname -a")
        success = computer.shell(command=command_action.command)
        print(f"Command execution success: {success}")
        
        # Example 2: Type some text
        print("\n=== Example 2: Typing Text ===")
        success = computer.execute_type(text="Hello from CommandLAB Docker!")
        print(f"Type action success: {success}")
        
        # Example 3: Move the mouse
        print("\n=== Example 3: Moving Mouse ===")
        # Get the display information first
        displays = computer.get_displays()
        if displays and displays.displays:
            display = displays.displays[0]
            width, height = display.width, display.height
            print(f"Display dimensions: {width}x{height}")
            
            # Move to a random position within the display
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            success = computer.execute_mouse_move(x=x, y=y, move_duration=0.5)
            print(f"Mouse moved to ({x}, {y}), success: {success}")
        else:
            print("No display information available")
        
        # Example 4: Take a screenshot
        print("\n=== Example 4: Taking Screenshot ===")
        screenshot = computer.get_screenshot(format="path")
        if screenshot and screenshot.path:
            print(f"Screenshot saved to: {screenshot.path}")
        else:
            print("Failed to take screenshot")
        
        # Example 5: Press keyboard keys
        print("\n=== Example 5: Keyboard Actions ===")
        # Press a single key
        success = computer.execute_keyboard_key_press(key=KeyboardKey.A)
        print(f"Key press (A) success: {success}")
        
        # Press a hotkey combination (Ctrl+C)
        success = computer.execute_keyboard_hotkey(keys=[KeyboardKey.CTRL, KeyboardKey.C])
        print(f"Hotkey (Ctrl+C) success: {success}")
        
        # Example 6: Mouse actions
        print("\n=== Example 6: Mouse Actions ===")
        if displays and displays.displays:
            # Click at a position
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            success = computer.execute_click(
                x=x, y=y, 
                move_duration=0.3, 
                press_duration=0.1, 
                button=MouseButton.LEFT
            )
            print(f"Click at ({x}, {y}) success: {success}")
            
            # Double click
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            success = computer.execute_double_click(
                x=x, y=y, 
                move_duration=0.3, 
                button=MouseButton.LEFT
            )
            print(f"Double click at ({x}, {y}) success: {success}")
            
            # Drag operation
            start_x, start_y = random.randint(0, width-1), random.randint(0, height-1)
            end_x, end_y = random.randint(0, width-1), random.randint(0, height-1)
            success = computer.execute_drag(
                start_x=start_x, start_y=start_y,
                end_x=end_x, end_y=end_y,
                move_duration=0.5,
                button=MouseButton.LEFT
            )
            print(f"Drag from ({start_x}, {start_y}) to ({end_x}, {end_y}) success: {success}")
        
        # Example 7: Run a process
        print("\n=== Example 7: Running a Process ===")
        success = computer.run_process(
            command="ls",
            args=["-la", "/"],
            timeout=5
        )
        print(f"Process execution success: {success}")
        
        # Example 8: Get observation
        print("\n=== Example 8: Getting Observation ===")
        observation = computer.get_observation()
        print("Observation keys:", list(observation.keys()) if observation else "No observation data")
        
        # Example 9: Get mouse and keyboard state
        print("\n=== Example 9: Getting Input Device States ===")
        mouse_state = computer.get_mouse_state()
        print(f"Mouse position: {mouse_state.position}")
        print(f"Mouse buttons: {mouse_state.buttons}")
        
        keyboard_state = computer.get_keyboard_state()
        print(f"Number of keyboard keys tracked: {len(keyboard_state.keys)}")
        print(f"Keys currently pressed: {[k for k, v in keyboard_state.keys.items() if v]}")
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if computer:
            print("\nCleaning up resources...")
            computer.stop()
            print("Docker container stopped and removed.")


if __name__ == "__main__":
    main() 