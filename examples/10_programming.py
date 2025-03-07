#!/usr/bin/env python3
"""
commandAGI Programming Example

This example demonstrates how to use commandAGI for programming tasks,
such as opening a code editor, writing code, and running it.

Status: ⚠️ Works with limitations
- Successfully creates a Python script
- Encounters an error when trying to edit the script
- The script itself works correctly when run directly
"""

import time
import os

try:
    from commandAGI.computers.local_pynput_computer import LocalPynputComputer
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
    print(
        "Error: Required modules not found. Make sure commandAGI is installed with the local extra:"
    )
    print("pip install commandagi[local]")
    exit(1)


def main():
    print("Creating a LocalPynputComputer instance...")

    try:
        # Create a computer instance
        computer = LocalPynputComputer()

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

        # Create a simple Python script file
        script_path = "output/hello_world.py"
        with open(script_path, "w") as f:
            f.write(
                """#!/usr/bin/env python3
# This script was created by commandAGI

def greet(name):
    return f"Hello, {name}!"

def main():
    print(greet("World"))
    print("This script was created and run using commandAGI automation.")

if __name__ == "__main__":
    main()
"""
            )

        print(f"Created Python script at {script_path}")

        # Open a code editor or notepad
        print("Opening a text editor...")
        if os.name == "nt":  # Windows
            editor_cmd = "notepad"
        elif os.uname().sysname == "Darwin":  # macOS
            editor_cmd = "open -a TextEdit"
        else:  # Linux
            editor_cmd = "gedit"

        result = computer.shell(
            ShellCommandAction(command=f"{editor_cmd} {script_path}", timeout=10)
        )

        print(f"Editor launch {'succeeded' if result else 'failed'}")
        print("Waiting for the editor to open...")
        time.sleep(3)

        # Add a new function to the script
        print("Adding a new function to the script...")

        # Press Ctrl+End to go to the end of the file
        computer.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.END])
        )
        time.sleep(0.5)

        # Add a new line before the end
        computer.execute_keyboard_key_press(
            KeyboardKeyPressAction(key=KeyboardKey.UP, duration=0.1)
        )
        time.sleep(0.5)

        # Type the new function
        computer.execute_type(
            TypeAction(
                text="""
def calculate_sum(a, b):
    return a + b

"""
            )
        )
        time.sleep(1)

        # Modify the main function to use the new function
        # First, find the main function
        computer.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.HOME])
        )
        time.sleep(0.5)

        # Search for "def main"
        computer.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.F])
        )
        time.sleep(0.5)

        computer.execute_type(TypeAction(text="def main"))
        time.sleep(0.5)

        # Press Enter to search
        computer.execute_keyboard_key_press(
            KeyboardKeyPressAction(key=KeyboardKey.ENTER, duration=0.1)
        )
        time.sleep(0.5)

        # Close the search dialog if it's still open
        computer.execute_keyboard_key_press(
            KeyboardKeyPressAction(key=KeyboardKey.ESCAPE, duration=0.1)
        )
        time.sleep(0.5)

        # Move to the end of the main function
        computer.execute_keyboard_key_press(
            KeyboardKeyPressAction(key=KeyboardKey.DOWN, duration=0.1)
        )
        time.sleep(0.1)

        computer.execute_keyboard_key_press(
            KeyboardKeyPressAction(key=KeyboardKey.DOWN, duration=0.1)
        )
        time.sleep(0.1)

        computer.execute_keyboard_key_press(
            KeyboardKeyPressAction(key=KeyboardKey.END, duration=0.1)
        )
        time.sleep(0.5)

        # Add a new line and type the new code
        computer.execute_keyboard_key_press(
            KeyboardKeyPressAction(key=KeyboardKey.ENTER, duration=0.1)
        )
        time.sleep(0.1)

        computer.execute_type(
            TypeAction(text='    print(f"The sum of 5 and 7 is {calculate_sum(5, 7)}")')
        )
        time.sleep(1)

        # Save the file
        computer.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S])
        )
        time.sleep(1)

        # Close the editor
        computer.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.ALT, KeyboardKey.F4])
        )
        time.sleep(1)

        # Run the script
        print("Running the Python script...")
        result = computer.shell(
            ShellCommandAction(command=f"python {script_path}", timeout=10)
        )

        print(f"Script execution {'succeeded' if result else 'failed'}")

        print("\nExample completed successfully!")
        print(f"You can find the script at {script_path}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if "computer" in locals():
            computer.close()
            print("Computer resources cleaned up.")


if __name__ == "__main__":
    main()
