#!/usr/bin/env python3
"""
Example of using the Computer with the generated OpenAPI client.
"""

from commandAGI.computers.remote_computer import (
    RemoteComputer,
    ProvisioningMethod,
)
from commandAGI.types import (
    TypeAction,
    MouseMoveAction,
    KeyboardHotkeyAction,
    ShellCommandAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseScrollAction,
)


def main():
    # Create a daemon client computer with the API token
    # This token should match what was used when starting the daemon
    api_token = "your_api_token_here"  # Replace with your actual token

    print("Initializing Computer...")
    # Connect to an existing daemon (no provisioning)
    computer = RemoteComputer(
        daemon_base_url="http://localhost", daemon_port=8000, daemon_token="my-token"
    )

    # Use with manual provisioning
    from commandAGI.computers.provisioners.manual_provisioner import ManualProvisioner

    provisioner = ManualProvisioner(port=8000)
    computer = RemoteComputer(daemon_port=8000, provisioner=provisioner)

    # Use with Docker provisioning
    from commandAGI.computers.provisioners.docker_provisioner import DockerProvisioner

    provisioner = DockerProvisioner(port=8000)
    computer = RemoteComputer(daemon_port=8000, provisioner=provisioner)

    try:
        # Example 1: Type some text
        print("\nExample 1: Typing text...")
        type_action = TypeAction(text="Hello, world!")
        success = computer.type(type_action)
        print(f"Type action success: {success}")

        # Example 2: Move the mouse
        print("\nExample 2: Moving mouse...")
        move_action = MouseMoveAction(x=500, y=300)
        success = computer.move(move_action)
        print(f"Mouse move success: {success}")

        # Example 3: Press a keyboard hotkey (Ctrl+C)
        print("\nExample 3: Pressing hotkey (Ctrl+C)...")
        hotkey_action = KeyboardHotkeyAction(keys=["ctrl", "c"])
        success = computer.hotkey(hotkey_action)
        print(f"Hotkey action success: {success}")

        # Example 4: Execute a command
        print("\nExample 4: Executing command...")
        command_action = ShellCommandAction(command="echo 'Hello from commandAGI'")
        success = computer.shell(command_action)
        print(f"Command execution success: {success}")

        # Example 5: Mouse click (down and up)
        print("\nExample 5: Performing mouse click...")
        # Move to position first
        computer.move(MouseMoveAction(x=400, y=400))
        # Perform click
        down_success = computer.mouse_down(
            MouseButtonDownAction(button="left")
        )
        up_success = computer.mouse_up(
            MouseButtonUpAction(button="left")
        )
        print(f"Mouse click success: {down_success and up_success}")

        # Example 6: Mouse scroll
        print("\nExample 6: Scrolling...")
        scroll_success = computer.scroll(MouseScrollAction(dx=0, dy=-3))
        print(f"Mouse scroll success: {scroll_success}")

        # Example 7: Get current observation
        print("\nExample 7: Getting observation...")
        observation = computer.get_observation()
        print(f"Current observation: {observation}")

        # Example 8: Reset the computer state
        print("\nExample 8: Resetting computer state...")
        reset_result = computer.reset_state()
        print(f"Reset completed: {reset_result}")

    finally:
        # Clean up resources
        print("\nCleaning up resources...")
        computer.close()


if __name__ == "__main__":
    main()
