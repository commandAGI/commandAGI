#!/usr/bin/env python3
"""
commandAGI Scripting Computer Interactions Example

This example demonstrates how to use the manual provisioner to script computer interactions.
The manual provisioner is the simplest way to get started with commandAGI.

Status: ⚠️ Requires manual setup
- Needs the daemon to be running in a separate terminal
"""

import time
import os

try:
    from commandAGI.computers.computer import (
        Computer,
        ProvisioningMethod,
    )
    from commandAGI.types import (
        ShellCommandAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKeyPressAction,
        KeyboardKey,
        ClickAction,
        MouseButton,
    )
except ImportError:
    print("Error: Required modules not found. Make sure commandAGI is installed:")
    print("pip install commandagi")
    exit(1)


def main():
    print("Creating a Computer with Manual provisioning...")

    try:
        # Create a computer with Manual provisioning
        computer = Computer(provisioning_method=ProvisioningMethod.MANUAL)

        print("\nManual provisioning instructions:")
        print("1. Open a new terminal window")
        print("2. Run the following command to start the daemon:")
        print("   pip install commandagi[local,daemon]")
        print("   python -m commandagi.daemon.daemon --port 8000 --backend pynput")
        print("3. Once the daemon is running, press Enter to continue...")
        input()

        # Give the daemon time to start if it was just started
        print("Waiting for daemon to be ready...")
        time.sleep(2)

        # Execute a command
        print(
            "Executing a command to open Notepad (on Windows) or TextEdit (on macOS)..."
        )
        if os.name == "nt":  # Windows
            result = computer.shell(ShellCommandAction(command="notepad", timeout=5))
        else:  # macOS or Linux
            result = computer.shell(
                ShellCommandAction(
                    command=(
                        "open -a TextEdit"
                        if os.uname().sysname == "Darwin"
                        else "gedit"
                    ),
                    timeout=5,
                )
            )

        print(f"Command execution {'succeeded' if result else 'failed'}")
        print("Waiting for the application to open...")
        time.sleep(3)

        # Type some text
        print("Typing text...")
        computer.type(
            TypeAction(
                text="Hello from commandAGI!\n\nThis is an example of scripting computer interactions."
            )
        )
        time.sleep(1)

        # Press a keyboard hotkey (Ctrl+S to save)
        print("Pressing Ctrl+S to save...")
        computer.hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S])
        )
        time.sleep(1)

        # Type a filename
        print("Typing filename...")
        computer.type(TypeAction(text="commandAGI2_example.txt"))
        time.sleep(1)

        # Press Enter to save
        print("Pressing Enter to save...")
        computer.keypress(
            KeyboardKeyPressAction(key=KeyboardKey.ENTER, duration=0.1)
        )
        time.sleep(1)

        # Close the application (Alt+F4)
        print("Pressing Alt+F4 to close the application...")
        computer.hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.ALT, KeyboardKey.F4])
        )

        print("\nExample completed successfully!")
        print("A file named 'commandAGI2_example.txt' should have been created.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if "computer" in locals():
            computer.close()
            print("Resources cleaned up.")
            print("Note: The daemon is still running. You can stop it manually.")


if __name__ == "__main__":
    main()
