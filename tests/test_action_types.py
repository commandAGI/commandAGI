import unittest

from commandAGI.types import (
    ClickAction,
    ShellCommandAction,
    DoubleClickAction,
    DragAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysDownAction,
    KeyboardKeysPressAction,
    KeyboardKeysReleaseAction,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    TypeAction,
    KeyboardKey,
    ComputerAction,
)


class TestCommandAction(unittest.TestCase):
    def test_command_action_creation(self):
        # Test creating a CommandAction
        action = ShellCommandAction(command="ls -la")

        # Check attributes
        self.assertEqual(action.command, "ls -la")
        self.assertIsNone(action.timeout)

        # Test with timeout
        action_with_timeout = ShellCommandAction(command="sleep 5", timeout=10.0)
        self.assertEqual(action_with_timeout.command, "sleep 5")
        self.assertEqual(action_with_timeout.timeout, 10.0)

    def test_command_action_validation(self):
        # Test validation of command
        with self.assertRaises(ValueError):
            ShellCommandAction(command="")  # Empty command should fail


class TestKeyboardActions(unittest.TestCase):
    def test_keyboard_key_press_action(self):
        # Test creating a KeyboardKeyPressAction
        action = KeyboardKeyPressAction(key=KeyboardKey.ENTER)

        # Check attributes
        self.assertEqual(action.key, KeyboardKey.ENTER)
        self.assertEqual(action.duration, 0.1)  # Default duration

        # Test with custom duration
        action_custom_duration = KeyboardKeyPressAction(
            key=KeyboardKey.SPACE, duration=0.5
        )
        self.assertEqual(action_custom_duration.key, KeyboardKey.SPACE)
        self.assertEqual(action_custom_duration.duration, 0.5)

    def test_keyboard_keys_press_action(self):
        # Test creating a KeyboardKeysPressAction
        action = KeyboardKeysPressAction(keys=[KeyboardKey.CTRL, KeyboardKey.C])

        # Check attributes
        self.assertEqual(action.keys, [KeyboardKey.CTRL, KeyboardKey.C])
        self.assertEqual(action.duration, 0.1)  # Default duration

    def test_keyboard_key_down_action(self):
        # Test creating a KeyboardKeyDownAction
        action = KeyboardKeyDownAction(key=KeyboardKey.SHIFT)

        # Check attributes
        self.assertEqual(action.key, KeyboardKey.SHIFT)

    def test_keyboard_keys_down_action(self):
        # Test creating a KeyboardKeysDownAction
        action = KeyboardKeysDownAction(keys=[KeyboardKey.CTRL, KeyboardKey.ALT])

        # Check attributes
        self.assertEqual(action.keys, [KeyboardKey.CTRL, KeyboardKey.ALT])

    def test_keyboard_key_release_action(self):
        # Test creating a KeyboardKeyReleaseAction
        action = KeyboardKeyReleaseAction(key=KeyboardKey.SHIFT)

        # Check attributes
        self.assertEqual(action.key, KeyboardKey.SHIFT)

    def test_keyboard_keys_release_action(self):
        # Test creating a KeyboardKeysReleaseAction
        action = KeyboardKeysReleaseAction(keys=[KeyboardKey.CTRL, KeyboardKey.ALT])

        # Check attributes
        self.assertEqual(action.keys, [KeyboardKey.CTRL, KeyboardKey.ALT])

    def test_keyboard_hotkey_action(self):
        # Test creating a KeyboardHotkeyAction
        action = KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S])

        # Check attributes
        self.assertEqual(action.keys, [KeyboardKey.CTRL, KeyboardKey.S])

    def test_type_action(self):
        # Test creating a TypeAction
        action = TypeAction(text="Hello, commandAGI!")

        # Check attributes
        self.assertEqual(action.text, "Hello, commandAGI!")


class TestMouseActions(unittest.TestCase):
    def test_mouse_move_action(self):
        # Test creating a MouseMoveAction
        action = MouseMoveAction(x=100, y=200)

        # Check attributes
        self.assertEqual(action.x, 100)
        self.assertEqual(action.y, 200)
        self.assertEqual(action.move_duration, 0.5)  # Default duration

        # Test with custom duration
        action_custom_duration = MouseMoveAction(x=300, y=400, move_duration=1.0)
        self.assertEqual(action_custom_duration.x, 300)
        self.assertEqual(action_custom_duration.y, 400)
        self.assertEqual(action_custom_duration.move_duration, 1.0)

    def test_mouse_scroll_action(self):
        # Test creating a MouseScrollAction
        action = MouseScrollAction(amount=10)

        # Check attributes
        self.assertEqual(action.amount, 10)

        # Test with negative amount (scroll down)
        action_negative = MouseScrollAction(amount=-5)
        self.assertEqual(action_negative.amount, -5)

    def test_mouse_down_action(self):
        # Test creating a MouseButtonDownAction
        action = MouseButtonDownAction()  # Default is LEFT

        # Check attributes
        self.assertEqual(action.button, MouseButton.LEFT)

        # Test with different button
        action_right = MouseButtonDownAction(button=MouseButton.RIGHT)
        self.assertEqual(action_right.button, MouseButton.RIGHT)

    def test_mouse_button_up_action(self):
        # Test creating a MouseButtonUpAction
        action = MouseButtonUpAction()  # Default is LEFT

        # Check attributes
        self.assertEqual(action.button, MouseButton.LEFT)

        # Test with different button
        action_middle = MouseButtonUpAction(button=MouseButton.MIDDLE)
        self.assertEqual(action_middle.button, MouseButton.MIDDLE)

    def test_click_action(self):
        # Test creating a ClickAction
        action = ClickAction(x=100, y=200)

        # Check attributes
        self.assertEqual(action.x, 100)
        self.assertEqual(action.y, 200)
        self.assertEqual(action.move_duration, 0.5)  # Default move duration
        self.assertEqual(action.press_duration, 0.1)  # Default press duration
        self.assertEqual(action.button, MouseButton.LEFT)  # Default button

        # Test with custom values
        action_custom = ClickAction(
            x=300,
            y=400,
            move_duration=1.0,
            press_duration=0.2,
            button=MouseButton.RIGHT,
        )
        self.assertEqual(action_custom.x, 300)
        self.assertEqual(action_custom.y, 400)
        self.assertEqual(action_custom.move_duration, 1.0)
        self.assertEqual(action_custom.press_duration, 0.2)
        self.assertEqual(action_custom.button, MouseButton.RIGHT)

    def test_double_click_action(self):
        # Test creating a DoubleClickAction
        action = DoubleClickAction(x=100, y=200)

        # Check attributes
        self.assertEqual(action.x, 100)
        self.assertEqual(action.y, 200)
        self.assertEqual(action.move_duration, 0.5)  # Default move duration
        self.assertEqual(action.press_duration, 0.1)  # Default press duration
        self.assertEqual(action.button, MouseButton.LEFT)  # Default button
        self.assertEqual(action.double_click_interval_seconds, 0.1)  # Default interval

        # Test with custom values
        action_custom = DoubleClickAction(
            x=300,
            y=400,
            move_duration=1.0,
            press_duration=0.2,
            button=MouseButton.RIGHT,
            double_click_interval_seconds=0.3,
        )
        self.assertEqual(action_custom.x, 300)
        self.assertEqual(action_custom.y, 400)
        self.assertEqual(action_custom.move_duration, 1.0)
        self.assertEqual(action_custom.press_duration, 0.2)
        self.assertEqual(action_custom.button, MouseButton.RIGHT)
        self.assertEqual(action_custom.double_click_interval_seconds, 0.3)

    def test_drag_action(self):
        # Test creating a DragAction
        action = DragAction(start_x=100, start_y=200, end_x=300, end_y=400)

        # Check attributes
        self.assertEqual(action.start_x, 100)
        self.assertEqual(action.start_y, 200)
        self.assertEqual(action.end_x, 300)
        self.assertEqual(action.end_y, 400)
        self.assertEqual(action.move_duration, 0.5)  # Default move duration
        self.assertEqual(action.button, MouseButton.LEFT)  # Default button

        # Test with custom values
        action_custom = DragAction(
            start_x=50,
            start_y=60,
            end_x=250,
            end_y=260,
            move_duration=1.0,
            button=MouseButton.RIGHT,
        )
        self.assertEqual(action_custom.start_x, 50)
        self.assertEqual(action_custom.start_y, 60)
        self.assertEqual(action_custom.end_x, 250)
        self.assertEqual(action_custom.end_y, 260)
        self.assertEqual(action_custom.move_duration, 1.0)
        self.assertEqual(action_custom.button, MouseButton.RIGHT)


class TestComputerAction(unittest.TestCase):
    def test_computer_action_with_command(self):
        # Test creating a ComputerAction with a CommandAction
        command = ShellCommandAction(command="ls -la")
        action = ComputerAction(command=command)

        # Check that only the command field is set
        self.assertEqual(action.get("command"), command)
        self.assertIsNone(action.get("click"))
        self.assertIsNone(action.get("type"))
        self.assertIsNone(action.get("double_click"))
        self.assertIsNone(action.get("drag"))
        self.assertIsNone(action.get("keyboard_hotkey"))
        self.assertIsNone(action.get("keyboard_key_down"))
        self.assertIsNone(action.get("keyboard_key_press"))
        self.assertIsNone(action.get("keyboard_key_release"))
        self.assertIsNone(action.get("keyboard_keys_down"))
        self.assertIsNone(action.get("keyboard_keys_press"))
        self.assertIsNone(action.get("keyboard_keys_release"))
        self.assertIsNone(action.get("mouse_down"))
        self.assertIsNone(action.get("mouse_button_up"))
        self.assertIsNone(action.get("mouse_move"))
        self.assertIsNone(action.get("mouse_scroll"))

    def test_computer_action_with_click(self):
        # Test creating a ComputerAction with a ClickAction
        click = ClickAction(x=100, y=200)
        action = ComputerAction(click=click)

        # Check that only the click field is set
        self.assertEqual(action.get("click"), click)
        self.assertIsNone(action.get("command"))
        self.assertIsNone(action.get("type"))
        self.assertIsNone(action.get("double_click"))
        self.assertIsNone(action.get("drag"))
        self.assertIsNone(action.get("keyboard_hotkey"))
        self.assertIsNone(action.get("keyboard_key_down"))
        self.assertIsNone(action.get("keyboard_key_press"))
        self.assertIsNone(action.get("keyboard_key_release"))
        self.assertIsNone(action.get("keyboard_keys_down"))
        self.assertIsNone(action.get("keyboard_keys_press"))
        self.assertIsNone(action.get("keyboard_keys_release"))
        self.assertIsNone(action.get("mouse_down"))
        self.assertIsNone(action.get("mouse_button_up"))
        self.assertIsNone(action.get("mouse_move"))
        self.assertIsNone(action.get("mouse_scroll"))

    def test_computer_action_with_type(self):
        # Test creating a ComputerAction with a TypeAction
        type_action = TypeAction(text="Hello")
        action = ComputerAction(type=type_action)

        # Check that only the type field is set
        self.assertEqual(action.get("type"), type_action)
        self.assertIsNone(action.get("command"))
        self.assertIsNone(action.get("click"))
        self.assertIsNone(action.get("double_click"))
        self.assertIsNone(action.get("drag"))
        self.assertIsNone(action.get("keyboard_hotkey"))
        self.assertIsNone(action.get("keyboard_key_down"))
        self.assertIsNone(action.get("keyboard_key_press"))
        self.assertIsNone(action.get("keyboard_key_release"))
        self.assertIsNone(action.get("keyboard_keys_down"))
        self.assertIsNone(action.get("keyboard_keys_press"))
        self.assertIsNone(action.get("keyboard_keys_release"))
        self.assertIsNone(action.get("mouse_down"))
        self.assertIsNone(action.get("mouse_button_up"))
        self.assertIsNone(action.get("mouse_move"))
        self.assertIsNone(action.get("mouse_scroll"))


if __name__ == "__main__":
    unittest.main()
