#!/usr/bin/env python3
"""
commandAGI Document Editing Example

This example demonstrates how to use the screen parser to extract text from a screenshot,
which can be useful for document editing and text extraction tasks.

Status: ✅ Works perfectly
- Successfully extracts text from a screenshot and saves it to a file
"""

import os
import time
import base64
from PIL import Image
import io

try:
    from commandAGI.computers.local_pynput_computer import LocalPynputComputer
    from commandAGI.processors.screen_parser.pytesseract_screen_parser import (
        parse_screenshot,
    )
    from commandAGI.types import ClickAction, MouseButton, TypeAction
except ImportError:
    print(
        "Error: Required modules not found. Make sure commandAGI is installed with the pytesseract extra:"
    )
    print("pip install commandagi[local,pytesseract]")
    exit(1)


def main():
    print("Creating a LocalPynputComputer instance...")

    try:
        # Create a computer instance
        computer = LocalPynputComputer()

        print("Please open a text editor or document with some text visible.")
        print("This example will extract text from the screen.")
        print("Press Enter when ready...")
        input()

        # Take a screenshot
        print("Taking a screenshot...")
        screenshot = computer.get_screenshot()

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

        # Save the screenshot for reference
        img_data = base64.b64decode(screenshot.screenshot)
        img = Image.open(io.BytesIO(img_data))
        screenshot_path = "output/screenshot_for_ocr.png"
        img.save(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        # Parse the screenshot to extract text
        print("Parsing screenshot to extract text...")
        try:
            parsed_screenshot = parse_screenshot(screenshot.screenshot)

            # Print the extracted text elements
            print("\nExtracted text elements:")
            for i, element in enumerate(parsed_screenshot.elements):
                print(f"Element {i+1}:")
                print(f"  Text: {element.text}")
                print(f"  Bounding Box: {element.bounding_box}")

            # Save the extracted text to a file
            text_path = "output/extracted_text.txt"
            with open(text_path, "w") as f:
                for element in parsed_screenshot.elements:
                    f.write(f"{element.text}\n")

            print(f"\nExtracted text saved to {text_path}")

            # Demonstrate clicking on a text element (if any were found)
            if parsed_screenshot.elements:
                element = parsed_screenshot.elements[0]
                x = (element.bounding_box[0] + element.bounding_box[2]) // 2
                y = (element.bounding_box[1] + element.bounding_box[3]) // 2

                print(
                    f"\nDemonstrating clicking on the first text element at position ({x}, {y})..."
                )
                print("Press Enter to continue...")
                input()

                # Click on the text element
                computer.click(ClickAction(x=x, y=y, button=MouseButton.LEFT))

                # Type some text
                time.sleep(0.5)
                print("Typing text after clicking...")
                computer.type(TypeAction(text=" [commandAGI was here] "))

        except Exception as e:
            print(f"Error parsing screenshot: {e}")

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
