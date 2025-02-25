import unittest

from commandLAB.types import (
    ComputerObservationType,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    MouseButton,
    KeyboardKey,
    ComputerObservation
)


class TestScreenshotObservation(unittest.TestCase):
    def test_screenshot_observation_creation(self):
        # Test creating a ScreenshotObservation
        observation = ScreenshotObservation(screenshot="base64_encoded_data")
        
        # Check attributes
        self.assertEqual(observation.screenshot, "base64_encoded_data")
        self.assertEqual(observation.observation_type, ComputerObservationType.SCREENSHOT)
        
    def test_screenshot_observation_validation(self):
        # Test validation of screenshot data
        with self.assertRaises(ValueError):
            ScreenshotObservation(screenshot="")  # Empty screenshot should fail


class TestMouseStateObservation(unittest.TestCase):
    def test_mouse_state_observation_creation(self):
        # Test creating a MouseStateObservation
        observation = MouseStateObservation(
            buttons={
                MouseButton.LEFT: False,
                MouseButton.RIGHT: False,
                MouseButton.MIDDLE: False
            },
            position=(100, 200)
        )
        
        # Check attributes
        self.assertEqual(observation.buttons[MouseButton.LEFT], False)
        self.assertEqual(observation.buttons[MouseButton.RIGHT], False)
        self.assertEqual(observation.buttons[MouseButton.MIDDLE], False)
        self.assertEqual(observation.position, (100, 200))
        self.assertEqual(observation.observation_type, ComputerObservationType.MOUSE_STATE)
        
        # Test with some buttons pressed
        observation_pressed = MouseStateObservation(
            buttons={
                MouseButton.LEFT: True,
                MouseButton.RIGHT: False,
                MouseButton.MIDDLE: True
            },
            position=(300, 400)
        )
        
        self.assertEqual(observation_pressed.buttons[MouseButton.LEFT], True)
        self.assertEqual(observation_pressed.buttons[MouseButton.RIGHT], False)
        self.assertEqual(observation_pressed.buttons[MouseButton.MIDDLE], True)
        self.assertEqual(observation_pressed.position, (300, 400))
        
    def test_mouse_state_observation_validation(self):
        # Test validation of buttons
        with self.assertRaises(ValueError):
            MouseStateObservation(
                buttons={},  # Empty buttons should fail
                position=(100, 200)
            )
            
        # Test validation of position
        with self.assertRaises(ValueError):
            MouseStateObservation(
                buttons={
                    MouseButton.LEFT: False,
                    MouseButton.RIGHT: False,
                    MouseButton.MIDDLE: False
                },
                position=()  # Empty position should fail
            )


class TestKeyboardStateObservation(unittest.TestCase):
    def test_keyboard_state_observation_creation(self):
        # Test creating a KeyboardStateObservation
        observation = KeyboardStateObservation(
            keys={
                KeyboardKey.SHIFT: False,
                KeyboardKey.CTRL: False,
                KeyboardKey.ALT: False,
                KeyboardKey.A: False,
                KeyboardKey.B: False
            }
        )
        
        # Check attributes
        self.assertEqual(observation.keys[KeyboardKey.SHIFT], False)
        self.assertEqual(observation.keys[KeyboardKey.CTRL], False)
        self.assertEqual(observation.keys[KeyboardKey.ALT], False)
        self.assertEqual(observation.keys[KeyboardKey.A], False)
        self.assertEqual(observation.keys[KeyboardKey.B], False)
        self.assertEqual(observation.observation_type, ComputerObservationType.KEYBOARD_STATE)
        
        # Test with some keys pressed
        observation_pressed = KeyboardStateObservation(
            keys={
                KeyboardKey.SHIFT: True,
                KeyboardKey.CTRL: True,
                KeyboardKey.ALT: False,
                KeyboardKey.A: True,
                KeyboardKey.B: False
            }
        )
        
        self.assertEqual(observation_pressed.keys[KeyboardKey.SHIFT], True)
        self.assertEqual(observation_pressed.keys[KeyboardKey.CTRL], True)
        self.assertEqual(observation_pressed.keys[KeyboardKey.ALT], False)
        self.assertEqual(observation_pressed.keys[KeyboardKey.A], True)
        self.assertEqual(observation_pressed.keys[KeyboardKey.B], False)
        
    def test_keyboard_state_observation_validation(self):
        # Test validation of keys
        with self.assertRaises(ValueError):
            KeyboardStateObservation(
                keys={}  # Empty keys should fail
            )


class TestComputerObservation(unittest.TestCase):
    def test_computer_observation_with_screenshot(self):
        # Test creating a ComputerObservation with a ScreenshotObservation
        screenshot = ScreenshotObservation(screenshot="base64_encoded_data")
        observation = ComputerObservation(screenshot=screenshot)
        
        # Check that only the screenshot field is set
        self.assertEqual(observation["screenshot"], screenshot)
        self.assertIsNone(observation["mouse_state"])
        self.assertIsNone(observation["keyboard_state"])
        
    def test_computer_observation_with_mouse_state(self):
        # Test creating a ComputerObservation with a MouseStateObservation
        mouse_state = MouseStateObservation(
            buttons={
                MouseButton.LEFT: False,
                MouseButton.RIGHT: False,
                MouseButton.MIDDLE: False
            },
            position=(100, 200)
        )
        observation = ComputerObservation(mouse_state=mouse_state)
        
        # Check that only the mouse_state field is set
        self.assertEqual(observation["mouse_state"], mouse_state)
        self.assertIsNone(observation["screenshot"])
        self.assertIsNone(observation["keyboard_state"])
        
    def test_computer_observation_with_keyboard_state(self):
        # Test creating a ComputerObservation with a KeyboardStateObservation
        keyboard_state = KeyboardStateObservation(
            keys={
                KeyboardKey.SHIFT: False,
                KeyboardKey.CTRL: False,
                KeyboardKey.ALT: False
            }
        )
        observation = ComputerObservation(keyboard_state=keyboard_state)
        
        # Check that only the keyboard_state field is set
        self.assertEqual(observation["keyboard_state"], keyboard_state)
        self.assertIsNone(observation["screenshot"])
        self.assertIsNone(observation["mouse_state"])
        
    def test_computer_observation_with_all_fields(self):
        # Test creating a ComputerObservation with all fields
        screenshot = ScreenshotObservation(screenshot="base64_encoded_data")
        mouse_state = MouseStateObservation(
            buttons={
                MouseButton.LEFT: False,
                MouseButton.RIGHT: False,
                MouseButton.MIDDLE: False
            },
            position=(100, 200)
        )
        keyboard_state = KeyboardStateObservation(
            keys={
                KeyboardKey.SHIFT: False,
                KeyboardKey.CTRL: False,
                KeyboardKey.ALT: False
            }
        )
        
        observation = ComputerObservation(
            screenshot=screenshot,
            mouse_state=mouse_state,
            keyboard_state=keyboard_state
        )
        
        # Check that all fields are set
        self.assertEqual(observation["screenshot"], screenshot)
        self.assertEqual(observation["mouse_state"], mouse_state)
        self.assertEqual(observation["keyboard_state"], keyboard_state)
        
    def test_computer_observation_empty(self):
        # Test creating an empty ComputerObservation
        observation = ComputerObservation()
        
        # Check that all fields are None
        self.assertIsNone(observation["screenshot"])
        self.assertIsNone(observation["mouse_state"])
        self.assertIsNone(observation["keyboard_state"])


if __name__ == '__main__':
    unittest.main() 