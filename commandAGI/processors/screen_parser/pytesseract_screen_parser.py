try:
    import pytesseract
except ImportError:
    raise ImportError(
        "pytesseract is not installed. Please install commandAGI with the pytesseract extra:\n\npip install commandAGI[pytesseract]"
    )

from commandAGI.utils.image import b64ToImage
from commandAGI.processors.screen_parser.types import ParsedScreenshot, ParsedElement


def parse_screenshot(screenshot_b64: str) -> ParsedScreenshot:
    """
    Parse a screenshot using Tesseract OCR.

    Args:
        screenshot_b64: Base64 encoded screenshot image

    Returns:
        ParsedScreenshot containing the detected text elements and their bounding boxes

    Examples:
        >>> # This example demonstrates the expected pattern but won't run in doctest
        >>> # Create a mock base64 image with text
        >>> import base64
        >>> from PIL import Image, ImageDraw, ImageFont
        >>> import io
        >>> # Create a blank image
        >>> img = Image.new('RGB', (200, 50), color='white')
        >>> # Add text to the image
        >>> draw = ImageDraw.Draw(img)
        >>> draw.text((10, 10), "Hello commandAGI", fill='black')
        >>> # Convert to base64
        >>> buffer = io.BytesIO()
        >>> img.save(buffer, format="PNG")
        >>> b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        >>>
        >>> # Parse the screenshot (this would be the actual test)
        >>> # result = parse_screenshot(b64_str)
        >>> # Check that we get a ParsedScreenshot
        >>> # isinstance(result, ParsedScreenshot)
        >>> # True
        >>> # Check that we found some text
        >>> # len(result.elements) > 0
        >>> # True
        >>> # Check that the first element contains our text
        >>> # "Hello" in result.elements[0].text
        >>> # True
    """
    image = b64ToImage(screenshot_b64)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    elements = []
    for i in range(len(data["text"])):
        if data["text"][i].strip():  # Only include non-empty text
            element = ParsedElement(
                text=data["text"][i],
                bounding_box=[
                    data["left"][i],
                    data["top"][i],
                    data["left"][i] + data["width"][i],
                    data["top"][i] + data["height"][i],
                ],
            )
            elements.append(element)

    return ParsedScreenshot(elements=elements)
