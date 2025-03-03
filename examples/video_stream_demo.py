#!/usr/bin/env python
"""
Video Stream Demo

This script demonstrates the video streaming functionality of the LocalComputer class.
It starts a local computer, starts the video stream, and then waits for the user to press Enter to stop.
"""

import time
import logging
import webbrowser
from commandAGI2.computers import LocalPynputComputer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Create and start a local computer
    logger.info("Creating and starting local computer...")
    computer = LocalPynputComputer()
    computer.start()

    try:
        # Start the video stream
        logger.info("Starting video stream...")
        success = computer.start_video_stream()

        if success:
            # Open the video stream in a web browser
            stream_url = computer.video_stream_url
            logger.info(f"Video stream started at: {stream_url}")
            webbrowser.open(stream_url)

            # Wait for user to press Enter to stop
            input("Press Enter to stop the video stream and exit...\n")
        else:
            logger.error("Failed to start video stream")

    finally:
        # Stop the video stream and computer
        logger.info("Stopping video stream...")
        computer.stop_video_stream()

        logger.info("Stopping computer...")
        computer.stop()

        logger.info("Done!")


if __name__ == "__main__":
    main()
