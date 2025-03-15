#!/usr/bin/env python3
"""
commandAGI Advanced Concepts Example

This example demonstrates advanced concepts of commandAGI, including:
- Mouse movement and clicking
- Keyboard typing
- Keyboard hotkeys
- Getting mouse and keyboard state

Status: ✅ Works perfectly
- Successfully performs mouse and keyboard actions
"""

import time

# Import the local computer implementation
try:
    from commandAGI.computers.local_pynput_computer import LocalPynputComputer
    from commandAGI.types import (
        MouseButton,
        KeyboardKey,
        ClickAction,
        TypeAction,
        KeyboardHotkeyAction,
        MouseMoveAction,
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

        # Give the user time to switch to a text editor or notepad
        print(
            "Please open a text editor (like Notepad) and bring it to the foreground."
        )
        print("This example will perform mouse and keyboard actions in 5 seconds...")
        for i in range(5, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        print("Starting!")

        # Get the current mouse state
        mouse_state = computer.get_mouse_state()
        print(f"Current mouse position: {mouse_state.position}")
        print(f"Mouse buttons: {mouse_state.buttons}")

        # Move the mouse to a position
        print("Moving mouse to position (500, 300)...")
        computer.move(
            MouseMoveAction(
                x=500, y=300, move_duration=1.0  # Move slowly so it's visible
            )
        )
        time.sleep(0.5)

        # Click at the current position
        print("Clicking at current position...")
        computer.click(ClickAction(x=500, y=300, button=MouseButton.LEFT))
        time.sleep(0.5)

        # Type some text
        print("Typing text...")
        computer.type(
            TypeAction(
                text="Hello from commandAGI!\n\nThis text was typed automatically."
            )
        )
        time.sleep(1)

        # Press a keyboard hotkey (Ctrl+A to select all)
        print("Pressing Ctrl+A to select all text...")
        computer.hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.A])
        )
        time.sleep(0.5)

        # Type more text (replacing the selected text)
        print("Typing more text...")
        computer.type(
            TypeAction(
                text="This text replaced the selected text.\n\ncommandAGI2 makes automation easy!"
            )
        )
        time.sleep(1)

        # Get the current keyboard state
        keyboard_state = computer.get_keyboard_state()
        print(f"Keyboard state: {keyboard_state.keys}")

        print("\nExample completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if "computer" in locals():
            computer.close()
            print("Computer resources cleaned up.")


if __name__ == "__main__":
    main()
