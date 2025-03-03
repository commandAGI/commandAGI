import unittest
from pynput.keyboard import Key as PynputKey
from pynput.mouse import Button as PynputButton

from commandAGI2.types import MouseButton, KeyboardKey


class TestMouseButton(unittest.TestCase):
    def test_mouse_button_values(self):
        # Test that the enum has the expected values
        self.assertEqual(MouseButton.LEFT, "left")
        self.assertEqual(MouseButton.RIGHT, "right")
        self.assertEqual(MouseButton.MIDDLE, "middle")

    def test_to_vnc(self):
        # Test conversion to VNC button codes
        self.assertEqual(MouseButton.to_vnc(MouseButton.LEFT), 1)
        self.assertEqual(MouseButton.to_vnc(MouseButton.MIDDLE), 2)
        self.assertEqual(MouseButton.to_vnc(MouseButton.RIGHT), 3)

        # Test with string values
        self.assertEqual(MouseButton.to_vnc("left"), 1)
        self.assertEqual(MouseButton.to_vnc("middle"), 2)
        self.assertEqual(MouseButton.to_vnc("right"), 3)

    def test_to_pyautogui(self):
        # Test conversion to PyAutoGUI button names
        self.assertEqual(MouseButton.to_pyautogui(MouseButton.LEFT), "left")
        self.assertEqual(MouseButton.to_pyautogui(MouseButton.MIDDLE), "middle")
        self.assertEqual(MouseButton.to_pyautogui(MouseButton.RIGHT), "right")

        # Test with string values
        self.assertEqual(MouseButton.to_pyautogui("left"), "left")
        self.assertEqual(MouseButton.to_pyautogui("middle"), "middle")
        self.assertEqual(MouseButton.to_pyautogui("right"), "right")

    def test_to_pynput(self):
        # Test conversion to pynput button objects
        self.assertEqual(MouseButton.to_pynput(MouseButton.LEFT), PynputButton.left)
        self.assertEqual(MouseButton.to_pynput(MouseButton.MIDDLE), PynputButton.middle)
        self.assertEqual(MouseButton.to_pynput(MouseButton.RIGHT), PynputButton.right)

        # Test with string values
        self.assertEqual(MouseButton.to_pynput("left"), PynputButton.left)
        self.assertEqual(MouseButton.to_pynput("middle"), PynputButton.middle)
        self.assertEqual(MouseButton.to_pynput("right"), PynputButton.right)

    def test_from_pynput(self):
        # Test conversion from pynput button objects
        self.assertEqual(MouseButton.from_pynput(PynputButton.left), MouseButton.LEFT)
        self.assertEqual(
            MouseButton.from_pynput(PynputButton.middle), MouseButton.MIDDLE
        )
        self.assertEqual(MouseButton.from_pynput(PynputButton.right), MouseButton.RIGHT)

    def test_is_valid_button(self):
        # Test validation of button names
        self.assertTrue(MouseButton.is_valid_button("left"))
        self.assertTrue(MouseButton.is_valid_button("middle"))
        self.assertTrue(MouseButton.is_valid_button("right"))

        # Test with invalid button names
        self.assertFalse(MouseButton.is_valid_button("invalid"))
        self.assertFalse(MouseButton.is_valid_button(""))
        self.assertFalse(MouseButton.is_valid_button(None))


class TestKeyboardKey(unittest.TestCase):
    def test_keyboard_key_values(self):
        # Test a sample of the enum values
        self.assertEqual(KeyboardKey.ENTER, "enter")
        self.assertEqual(KeyboardKey.TAB, "tab")
        self.assertEqual(KeyboardKey.SPACE, "space")
        self.assertEqual(KeyboardKey.CTRL, "ctrl")
        self.assertEqual(KeyboardKey.A, "a")
        self.assertEqual(KeyboardKey.NUM_1, "1")

    def test_to_vnc(self):
        # Test conversion to VNC key codes for a sample of keys
        self.assertEqual(KeyboardKey.to_vnc(KeyboardKey.ENTER), "enter")
        self.assertEqual(KeyboardKey.to_vnc(KeyboardKey.SPACE), "space")
        self.assertEqual(KeyboardKey.to_vnc(KeyboardKey.A), "a")

        # Test with string values
        self.assertEqual(KeyboardKey.to_vnc("enter"), "enter")
        self.assertEqual(KeyboardKey.to_vnc("space"), "space")
        self.assertEqual(KeyboardKey.to_vnc("a"), "a")

    def test_to_pyautogui(self):
        # Test conversion to PyAutoGUI key names for a sample of keys
        self.assertEqual(KeyboardKey.to_pyautogui(KeyboardKey.ENTER), "enter")
        self.assertEqual(KeyboardKey.to_pyautogui(KeyboardKey.SPACE), "space")
        self.assertEqual(KeyboardKey.to_pyautogui(KeyboardKey.A), "a")

        # Test with string values
        self.assertEqual(KeyboardKey.to_pyautogui("enter"), "enter")
        self.assertEqual(KeyboardKey.to_pyautogui("space"), "space")
        self.assertEqual(KeyboardKey.to_pyautogui("a"), "a")

    def test_to_pynput(self):
        # Test conversion to pynput key objects for a sample of keys
        self.assertEqual(KeyboardKey.to_pynput(KeyboardKey.ENTER), PynputKey.enter)
        self.assertEqual(KeyboardKey.to_pynput(KeyboardKey.SPACE), PynputKey.space)
        # For letter keys, pynput uses KeyCode objects which we can't directly compare

        # Test with string values
        self.assertEqual(KeyboardKey.to_pynput("enter"), PynputKey.enter)
        self.assertEqual(KeyboardKey.to_pynput("space"), PynputKey.space)

    def test_from_pynput(self):
        # Test conversion from pynput key objects for a sample of keys
        self.assertEqual(KeyboardKey.from_pynput(PynputKey.enter), KeyboardKey.ENTER)
        self.assertEqual(KeyboardKey.from_pynput(PynputKey.space), KeyboardKey.SPACE)
        self.assertEqual(KeyboardKey.from_pynput(PynputKey.shift), KeyboardKey.SHIFT)

    def test_is_valid_key(self):
        # Test validation of key names
        self.assertTrue(KeyboardKey.is_valid_key("enter"))
        self.assertTrue(KeyboardKey.is_valid_key("space"))
        self.assertTrue(KeyboardKey.is_valid_key("a"))
        self.assertTrue(KeyboardKey.is_valid_key("1"))

        # Test with invalid key names
        self.assertFalse(KeyboardKey.is_valid_key("invalid_key"))
        self.assertFalse(KeyboardKey.is_valid_key(""))
        self.assertFalse(KeyboardKey.is_valid_key(None))


if __name__ == "__main__":
    unittest.main()
