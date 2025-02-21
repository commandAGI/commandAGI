from commandAGI_LAB.processors.screen_parser.base_screen_parser import (
    BaseScreenParser,
    ComputerObservationWithParsedScreenshot,
    ParsedElement,
    ParsedScreenshot,
)
from commandAGI_LAB.types import ComputerObservation
import pytesseract
from commandAGI_LAB.utils.image import b64ToImage

class TesseractScreenParser(BaseScreenParser):
    def parse_observation(self, observation: ComputerObservation) -> ParsedScreenshot:
        image = b64ToImage(observation.screenshot.screenshot)
        items = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        elements = [
            ParsedElement(text=text, bounding_box=bounding_box)
            for text, bounding_box in items.items()
        ]
        parsed_screenshot = ParsedScreenshot(elements=elements)
        return ComputerObservationWithParsedScreenshot(
            parsed_screenshot=parsed_screenshot,
            **observation.model_dump()
        )
