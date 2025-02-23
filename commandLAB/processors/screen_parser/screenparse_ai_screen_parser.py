import requests
from commandLAB.processors.screen_parser.types import ParsedScreenshot, ParsedElement


def parse_screenshot(
    base64_image: str,
    api_key: str,
    api_url: str = "https://api.screenparse.ai/v1/parse",
) -> ParsedScreenshot:
    """
    Parse a screenshot using the ScreenParse.ai API.

    Args:
        base64_image: Base64 encoded image string
        api_key: ScreenParse.ai API key
        api_url: ScreenParse.ai API endpoint URL

    Returns:
        ParsedScreenshot containing the detected text elements and their bounding boxes
    """
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {"base64_image": base64_image}

    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    elements = []
    for element in data["elements"]:
        parsed_element = ParsedElement(
            text=element["text"],
            bounding_box=[
                element["bbox"]["x"],
                element["bbox"]["y"],
                element["bbox"]["x"] + element["bbox"]["width"],
                element["bbox"]["y"] + element["bbox"]["height"],
            ],
        )
        elements.append(parsed_element)

    return ParsedScreenshot(elements=elements)
