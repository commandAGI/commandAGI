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

    Examples:
        >>> # Create a test image
        >>> from PIL import Image
        >>> test_img = Image.new('RGB', (300, 200), color='white')
        >>> # Apply grid overlay
        >>> result = overlay_grid(test_img, grid_px_size=100)
        >>> # Check that result is an Image
        >>> isinstance(result, Image.Image)
        True
        >>> # Check that dimensions are preserved
        >>> result.size
        (300, 200)
        >>> # Check that it's a different image object (copy was made)
        >>> result is not test_img
        True

        >>> # Test with different grid size
        >>> small_grid = overlay_grid(test_img, grid_px_size=50)
        >>> small_grid.size
        (300, 200)
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
