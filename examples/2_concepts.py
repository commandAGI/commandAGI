#!/usr/bin/env python3
"""
CommandLAB Concepts Example

This example demonstrates basic concepts of CommandLAB, including:
- Creating a computer instance
- Taking a screenshot
- Saving the screenshot to a file
"""

import os
import base64
from PIL import Image
import io

# Import the local computer implementation
try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
except ImportError:
    print("Error: LocalPynputComputer not found. Make sure CommandLAB is installed with the local extra:")
    print("pip install commandlab[local]")
    exit(1)

def main():
    print("Creating a LocalPynputComputer instance...")
    
    try:
        # Create a computer instance
        computer = LocalPynputComputer()
        
        print("Taking a screenshot...")
        # Take a screenshot
        screenshot = computer.get_screenshot()
        
        # The screenshot is returned as a base64-encoded string
        print(f"Screenshot obtained. Converting to image...")
        
        # Convert base64 to image
        img_data = base64.b64decode(screenshot.screenshot)
        img = Image.open(io.BytesIO(img_data))
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        # Save the image
        output_path = "output/screenshot.png"
        img.save(output_path)
        
        print(f"Screenshot saved to {output_path}")
        print(f"Image size: {img.width}x{img.height} pixels")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if 'computer' in locals():
            computer.close()
            print("Computer resources cleaned up.")

if __name__ == "__main__":
    main()
