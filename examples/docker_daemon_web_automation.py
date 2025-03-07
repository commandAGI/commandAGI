#!/usr/bin/env python3
"""
Docker Daemon Web Automation Example

This example demonstrates how to use the Docker-backed daemon computer client
for web automation tasks. It shows how to:
1. Start a browser
2. Navigate to websites
3. Interact with web elements
4. Take screenshots of web pages
5. Extract data from web pages

Note: This example requires Docker to be installed and running on your system.

Usage:
    python docker_daemon_web_automation.py
"""

import time
import os
from pathlib import Path

from commandAGI.computers.daemon_client_computer import DaemonClientComputer
from commandAGI.computers.provisioners.docker_provisioner import (
    DockerProvisioner,
    DockerPlatform,
)
from commandAGI.version import get_container_version
from commandAGI.types import (
    KeyboardKey,
    MouseButton,
    TypeAction,
    MouseMoveAction,
    ClickAction,
    KeyboardHotkeyAction,
    ShellCommandAction,
)


def main():
    print("=== Docker Daemon Web Automation Example ===")
    print("Starting Docker container with commandAGI daemon...")

    # Create a Docker provisioner
    provisioner = DockerProvisioner(
        port=8000,
        platform=DockerPlatform.LOCAL,
        container_name="commandagi-web-automation",
        version=get_container_version(),
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

        # Step 1: Install a browser if not already installed
        print("\n=== Step 1: Ensuring Browser is Installed ===")
        # Check if Firefox is installed
        success = computer.shell(command="which firefox")
        if not success:
            print("Firefox not found, installing...")
            computer.shell(command="apt-get update && apt-get install -y firefox-esr")
        else:
            print("Firefox is already installed")

        # Step 2: Start the browser
        print("\n=== Step 2: Starting Browser ===")
        # Start Firefox in headless mode
        success = computer.run_process(
            command="firefox",
            args=["--headless", "--no-remote", "--new-instance", "about:blank"],
            timeout=10,
        )
        print(f"Browser started: {success}")
        time.sleep(3)  # Wait for browser to initialize

        # Step 3: Navigate to a website
        print("\n=== Step 3: Navigating to a Website ===")
        # Open a new tab and navigate to example.com
        computer.shell(command="firefox --new-tab https://example.com")
        print("Navigated to example.com")
        time.sleep(5)  # Wait for page to load

        # Step 4: Take a screenshot of the page
        print("\n=== Step 4: Taking Screenshot of the Page ===")
        screenshot = computer.get_screenshot(format="path")
        if screenshot and screenshot.path:
            print(f"Screenshot saved to: {screenshot.path}")
        else:
            print("Failed to take screenshot")

        # Step 5: Interact with the page
        print("\n=== Step 5: Interacting with the Page ===")
        # Get the layout tree to find elements
        layout = computer.get_layout_tree()
        if layout and layout.tree:
            print("Got layout tree, searching for elements...")

            # Find elements by analyzing the layout tree
            # This is a simplified example - in a real scenario, you would
            # use more sophisticated methods to locate elements

            # Click on a link (simulated)
            print("Clicking on a link...")
            # Assuming the link is at position (300, 300)
            computer.execute_click(x=300, y=300)
            time.sleep(2)

            # Type in a search box (simulated)
            print("Typing in a search box...")
            # Assuming the search box is at position (500, 200)
            computer.execute_click(x=500, y=200)
            computer.execute_type(text="search query")
            time.sleep(1)

            # Press Enter to submit
            computer.execute_keyboard_key_press(key=KeyboardKey.ENTER)
            time.sleep(3)
        else:
            print("Failed to get layout tree")

        # Step 6: Extract data from the page
        print("\n=== Step 6: Extracting Data from the Page ===")
        # Use a shell command to extract the page title
        # This is a simplified example - in a real scenario, you would
        # use more sophisticated methods to extract data
        computer.shell(
            command="firefox --headless --screenshot /tmp/screenshot.png https://example.com"
        )
        time.sleep(2)

        # Step 7: Close the browser
        print("\n=== Step 7: Closing the Browser ===")
        computer.shell(command="pkill firefox")
        print("Browser closed")

        print("\nWeb automation example completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if computer:
            print("\nCleaning up resources...")
            # Make sure browser is closed
            try:
                computer.shell(command="pkill firefox")
            except:
                pass
            computer.stop()
            print("Docker container stopped and removed.")


def perform_web_search(
    computer, search_engine="https://www.google.com", query="commandAGI automation"
):
    """Perform a web search using the specified search engine and query."""
    print(f"\n=== Performing Web Search on {search_engine} ===")

    # Navigate to the search engine
    computer.shell(command=f"firefox --new-tab {search_engine}")
    print(f"Navigated to {search_engine}")
    time.sleep(5)  # Wait for page to load

    # Take a screenshot before search
    screenshot_before = computer.get_screenshot(format="path")
    print(
        f"Screenshot before search saved to: {screenshot_before.path if screenshot_before and screenshot_before.path else 'N/A'}"
    )

    # Find the search box and click on it
    # This is a simplified example - in a real scenario, you would
    # use more sophisticated methods to locate the search box

    # For Google, the search box is usually near the center of the page
    displays = computer.get_displays()
    if displays and displays.displays:
        display = displays.displays[0]
        width, height = display.width, display.height

        # Click in the approximate position of the search box
        search_box_x = width // 2
        search_box_y = height // 3
        computer.execute_click(x=search_box_x, y=search_box_y)
        time.sleep(1)

        # Type the search query
        computer.execute_type(text=query)
        time.sleep(1)

        # Press Enter to submit the search
        computer.execute_keyboard_key_press(key=KeyboardKey.ENTER)
        time.sleep(5)  # Wait for search results to load

        # Take a screenshot after search
        screenshot_after = computer.get_screenshot(format="path")
        print(
            f"Screenshot after search saved to: {screenshot_after.path if screenshot_after and screenshot_after.path else 'N/A'}"
        )

        # Scroll down to see more results
        for _ in range(3):
            computer.execute_mouse_scroll(amount=-5)  # Scroll down
            time.sleep(1)

        # Take a final screenshot after scrolling
        screenshot_scrolled = computer.get_screenshot(format="path")
        print(
            f"Screenshot after scrolling saved to: {screenshot_scrolled.path if screenshot_scrolled and screenshot_scrolled.path else 'N/A'}"
        )

        return True
    else:
        print("No display information available")
        return False


if __name__ == "__main__":
    main()
