from PIL import Image, ImageDraw
import io
import base64
from typing import Optional

def overlay_grid(img: Image.Image, grid_px_size: int = 100) -> Image.Image:
    """
    Overlay a grid on an image.
    
    Args:
        img: PIL Image to overlay grid on
        grid_px_size: Size of grid cells in pixels
        
    Returns:
        PIL Image with grid overlaid
    """
    # Create a copy of the image to draw on
    img = img.copy()
    
    # Create a drawing object
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Draw vertical lines
    for x in range(0, width, grid_px_size):
        draw.line([(x, 0), (x, height)], fill="red", width=1)

    # Draw horizontal lines 
    for y in range(0, height, grid_px_size):
        draw.line([(0, y), (width, y)], fill="red", width=1)

    # Add coordinates at grid intersections
    for x in range(0, width, grid_px_size):
        for y in range(0, height, grid_px_size):
            coordinate_text = f"({x},{y})"
            # Adjust text position so it does not overlap with grid lines
            text_position = (x + 5, y + 5)
            draw.text(text_position, coordinate_text, fill="red")

    return img
