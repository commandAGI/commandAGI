#!/usr/bin/env python3
"""
CommandLAB Automating Computer Interactions Example

This example demonstrates how to use the grid overlay utility to help with positioning
when automating computer interactions.
"""

import os
import time
import base64
from PIL import Image
import io

try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
    from commandLAB.processors.grid_overlay import overlay_grid
    from commandLAB.types import (
        ClickAction,
        MouseButton,
        MouseMoveAction
    )
except ImportError:
    print("Error: Required modules not found. Make sure CommandLAB is installed with the local extra:")
    print("pip install commandlab[local]")
    exit(1)

def main():
    print("Creating a LocalPynputComputer instance...")
    
    try:
        # Create a computer instance
        computer = LocalPynputComputer()
        
        # Take a screenshot
        print("Taking a screenshot...")
        screenshot = computer.get_screenshot()
        
        # Convert base64 to image
        img_data = base64.b64decode(screenshot.screenshot)
        img = Image.open(io.BytesIO(img_data))
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        # Apply grid overlay
        print("Applying grid overlay...")
        grid_img = overlay_grid(img, grid_px_size=100)
        
        # Save the grid image
        grid_path = "output/grid_overlay.png"
        grid_img.save(grid_path)
        
        print(f"Grid overlay image saved to {grid_path}")
        print(f"Image size: {grid_img.width}x{grid_img.height} pixels")
        
        # Open the grid image to help with positioning
        print(f"Opening the grid image to help with positioning...")
        if os.name == 'nt':  # Windows
            os.system(f"start {grid_path}")
        elif os.uname().sysname == 'Darwin':  # macOS
            os.system(f"open {grid_path}")
        else:  # Linux
            os.system(f"xdg-open {grid_path}")
        
        print("\nThe grid overlay image shows coordinates at 100-pixel intervals.")
        print("You can use these coordinates to position mouse clicks and movements.")
        print("For example, to click at position (300, 200):")
        
        # Wait for the user to view the grid
        print("\nPress Enter to continue with a demonstration...")
        input()
        
        # Demonstrate mouse movement to a grid position
        print("Moving mouse to position (300, 200)...")
        computer.execute_mouse_move(MouseMoveAction(
            x=300,
            y=200,
            move_duration=1.0  # Move slowly so it's visible
        ))
        time.sleep(1)
        
        # Demonstrate clicking at a grid position
        print("Clicking at position (300, 200)...")
        computer.execute_click(ClickAction(
            x=300,
            y=200,
            button=MouseButton.LEFT
        ))
        
        print("\nExample completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if 'computer' in locals():
            computer.close()
            print("Computer resources cleaned up.")

if __name__ == "__main__":
    main()
