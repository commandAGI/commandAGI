import unittest
from commandLAB.processors.screen_parser.types import ParsedElement, ParsedScreenshot


class TestScreenParserTypes(unittest.TestCase):
    def test_parsed_element_creation(self):
        # Test creating a ParsedElement
        element = ParsedElement(text="Hello World", bounding_box=[10, 20, 110, 50])

        # Check attributes
        self.assertEqual(element.text, "Hello World")
        self.assertEqual(element.bounding_box, [10, 20, 110, 50])

    def test_parsed_element_validation(self):
        # Test validation of bounding box
        # Should have 4 elements: [left, top, right, bottom]
        with self.assertRaises(ValueError):
            ParsedElement(
                text="Invalid Box", bounding_box=[10, 20, 30]  # Missing bottom
            )

    def test_parsed_screenshot_creation(self):
        # Test creating a ParsedScreenshot with multiple elements
        element1 = ParsedElement(text="Hello", bounding_box=[10, 20, 50, 40])

        element2 = ParsedElement(text="World", bounding_box=[60, 20, 110, 40])

        screenshot = ParsedScreenshot(elements=[element1, element2])

        # Check attributes
        self.assertEqual(len(screenshot.elements), 2)
        self.assertEqual(screenshot.elements[0].text, "Hello")
        self.assertEqual(screenshot.elements[1].text, "World")

    def test_parsed_screenshot_empty(self):
        # Test creating a ParsedScreenshot with no elements
        screenshot = ParsedScreenshot(elements=[])

        # Check attributes
        self.assertEqual(len(screenshot.elements), 0)

    def test_parsed_element_serialization(self):
        # Test that ParsedElement can be serialized to dict
        element = ParsedElement(text="Test", bounding_box=[10, 20, 110, 50])

        # Convert to dict
        element_dict = element.model_dump()

        # Check dict values
        self.assertEqual(element_dict["text"], "Test")
        self.assertEqual(element_dict["bounding_box"], [10, 20, 110, 50])

    def test_parsed_screenshot_serialization(self):
        # Test that ParsedScreenshot can be serialized to dict
        element1 = ParsedElement(text="Hello", bounding_box=[10, 20, 50, 40])

        element2 = ParsedElement(text="World", bounding_box=[60, 20, 110, 40])

        screenshot = ParsedScreenshot(elements=[element1, element2])

        # Convert to dict
        screenshot_dict = screenshot.model_dump()

        # Check dict values
        self.assertEqual(len(screenshot_dict["elements"]), 2)
        self.assertEqual(screenshot_dict["elements"][0]["text"], "Hello")
        self.assertEqual(screenshot_dict["elements"][1]["text"], "World")


if __name__ == "__main__":
    unittest.main()
