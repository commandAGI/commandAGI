try:
    import pytesseract
except ImportError:
    raise ImportError(
        "pytesseract is not installed. Please install commandLAB with the pytesseract extra:\n\npip install commandLAB[pytesseract]"
    )

from commandLAB.utils.image import b64ToImage
from commandLAB.processors.screen_parser.types import ParsedScreenshot, ParsedElement


def parse_screenshot(screenshot_b64: str) -> ParsedScreenshot:
    """
    Parse a screenshot using Tesseract OCR.

    Args:
        screenshot_b64: Base64 encoded screenshot image

    Returns:
        ParsedScreenshot containing the detected text elements and their bounding boxes
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
