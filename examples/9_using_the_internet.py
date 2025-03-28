#!/usr/bin/env python3
"""
commandAGI Web Automation Example

This example demonstrates how to use commandAGI for web automation tasks,
such as opening a browser, navigating to a website, and interacting with web elements.

Status: ⚠️ Works with minor issues
- Successfully opens a browser, navigates to a website, and takes a screenshot
- Encounters an error when closing the browser
"""

import time
import os

try:
    from commandAGI.computers.local_pynput_computer import LocalPynputComputer
    from commandAGI.types import (
        ShellCommandAction,
        ClickAction,
        TypeAction,
        KeyboardHotkeyAction,
        KeyboardKey,
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

        # Open a web browser
        print("Opening a web browser...")
        if os.name == "nt":  # Windows
            browser_cmd = "start chrome"
        elif os.uname().sysname == "Darwin":  # macOS
            browser_cmd = "open -a 'Google Chrome'"
        else:  # Linux
            browser_cmd = "google-chrome"

        result = computer.shell(ShellCommandAction(command=browser_cmd, timeout=10))

        print(f"Browser launch {'succeeded' if result else 'failed'}")
        print("Waiting for the browser to open...")
        time.sleep(5)

        # Navigate to a website by typing in the address bar
        print("Navigating to a website...")

        # Press Ctrl+L to focus the address bar
        computer.hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.L])
        )
        time.sleep(0.5)

        # Type the URL
        computer.type(TypeAction(text="example.com"))
        time.sleep(0.5)

        # Press Enter to navigate
        computer.hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.ENTER]))

        print("Waiting for the page to load...")
        time.sleep(3)

        # Take a screenshot of the page
        print("Taking a screenshot of the page...")
        screenshot = computer.get_screenshot()

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

        # Save the screenshot
        import base64
        from PIL import Image
        import io

        img_data = base64.b64decode(screenshot.screenshot)
        img = Image.open(io.BytesIO(img_data))
        screenshot_path = "output/web_screenshot.png"
        img.save(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        # Demonstrate clicking on a link (approximate position for example.com's "More information" link)
        print("Clicking on a link...")
        computer.click(ClickAction(x=400, y=400, button=MouseButton.LEFT))

        print("Waiting for the new page to load...")
        time.sleep(3)

        # Close the browser
        print("Closing the browser...")
        computer.hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.ALT, KeyboardKey.F4])
        )

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
