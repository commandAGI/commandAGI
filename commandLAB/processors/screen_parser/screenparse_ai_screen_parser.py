import base64
import requests
from typing import Dict, Any

from commandLAB.processors.screen_parser.base_screen_parser import (
    BaseScreenParser,
    ComputerObservationWithParsedScreenshot,
    ParsedElement,
    ParsedScreenshot,
)
from commandLAB.types import ComputerObservation

class ScreenParseAIParser(BaseScreenParser):
    def __init__(self, api_key: str, api_url: str = "https://api.screenparse.ai/v1/parse"):
        self.api_key = api_key
        self.api_url = api_url

    def parse_observation(self, observation: ComputerObservation) -> ComputerObservationWithParsedScreenshot:
        # The screenshot is already in base64 format in observation.screenshot.screenshot
        response = self._call_api(observation.screenshot.screenshot)
        
        # Convert API response elements to ParsedElement objects
        elements = [
            ParsedElement(
                text=elem["content"] if "content" in elem else "",
                bounding_box=self._convert_bbox_to_pixels(elem["bbox"])
            )
            for elem in response["elements"]
            if elem["type"] == "text"  # Only process text elements
        ]

        parsed_screenshot = ParsedScreenshot(elements=elements)
        return ComputerObservationWithParsedScreenshot(
            parsed_screenshot=parsed_screenshot,
            **observation.model_dump()
        )

    def _call_api(self, base64_image: str) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "base64_image": base64_image
        }

        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for non-200 status codes
        return response.json()

    def _convert_bbox_to_pixels(self, bbox: list[float]) -> list[int]:
        """Convert normalized coordinates (0-1) to pixel coordinates"""
        # Assuming the image dimensions are available or standardized
        # You might need to adjust this based on your actual image dimensions
        IMAGE_WIDTH = 1920  # Example width
        IMAGE_HEIGHT = 1080  # Example height
        
        return [
            int(bbox[0] * IMAGE_WIDTH),   # x1
            int(bbox[1] * IMAGE_HEIGHT),  # y1
            int(bbox[2] * IMAGE_WIDTH),   # x2
            int(bbox[3] * IMAGE_HEIGHT)   # y2
        ]
