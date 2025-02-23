from PIL import Image, ImageDraw
import io
import base64
from typing import Optional

from commandLAB.processors.base_processor import ObservationProcessor
from commandLAB.types import ComputerObservation, ScreenshotObservation


class GridOverlayProcessor(ObservationProcessor[ComputerObservation, ComputerObservation]):
    
    grid_px_size: int = 100
    
    def __init__(self, grid_px_size: int = 100):
        """
        Initialize the grid overlay processor.
        
        Args:
            grid_px_size: Size of grid cells in pixels
        """
        self.grid_px_size = grid_px_size

    def process_observation(self, observation: ComputerObservation) -> ComputerObservation:
        if observation.screenshot is None:
            return observation

        # Decode base64 screenshot
        img_data = base64.b64decode(observation.screenshot.screenshot)
        img = Image.open(io.BytesIO(img_data))
        
        # Create a drawing object
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Draw vertical lines
        for x in range(0, width, self.grid_px_size):
            draw.line([(x, 0), (x, height)], fill="red", width=1)

        # Draw horizontal lines
        for y in range(0, height, self.grid_px_size):
            draw.line([(0, y), (width, y)], fill="red", width=1)

        # Add coordinates at grid intersections
        for x in range(0, width, self.grid_px_size):
            for y in range(0, height, self.grid_px_size):
                coordinate_text = f"({x},{y})"
                # Adjust text position so it does not overlap with grid lines
                text_position = (x + 5, y + 5)
                draw.text(text_position, coordinate_text, fill="red")

        # Convert back to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Update the screenshot in the observation
        observation.screenshot.screenshot = img_str
        return observation
