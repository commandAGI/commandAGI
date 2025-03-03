import unittest
from unittest.mock import MagicMock, patch
import time

from commandAGI2.computers.base_computer import BaseComputer
from commandAGI2.types import (
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
    KeyboardStateObservation,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
    TypeAction,
    KeyboardKey,
    MouseButton,
)
from pydantic import Field


class MockComputer(BaseComputer):
    """Mock implementation of BaseComputer for testing."""

    # Define fields with default values
    get_screenshot_called: bool = Field(default=False)
    get_mouse_state_called: bool = Field(default=False)
    get_keyboard_state_called: bool = Field(default=False)
    execute_command_called: bool = Field(default=False)
    execute_keyboard_key_down_called: bool = Field(default=False)
    execute_keyboard_key_release_called: bool = Field(default=False)
    execute_mouse_move_called: bool = Field(default=False)
    execute_mouse_scroll_called: bool = Field(default=False)
    execute_mouse_button_down_called: bool = Field(default=False)
    execute_mouse_button_up_called: bool = Field(default=False)

    # Store the last action parameters
    last_command: ShellCommandAction = Field(default=None)
    last_key_down: KeyboardKeyDownAction = Field(default=None)
    last_key_release: KeyboardKeyReleaseAction = Field(default=None)
    last_mouse_move: MouseMoveAction = Field(default=None)
    last_mouse_scroll: MouseScrollAction = Field(default=None)
    last_mouse_button_down: MouseButtonDownAction = Field(default=None)
    last_mouse_button_up: MouseButtonUpAction = Field(default=None)

    model_config = {"arbitrary_types_allowed": True, "extra": "allow"}

    def get_screenshot(self) -> ScreenshotObservation:
        self.get_screenshot_called = True
        return ScreenshotObservation(screenshot="mock_screenshot_data")

    def get_mouse_state(self) -> MouseStateObservation:
        self.get_mouse_state_called = True
        return MouseStateObservation(
            buttons={
                MouseButton.LEFT: False,
                MouseButton.RIGHT: False,
                MouseButton.MIDDLE: False,
            },
            position=(100, 200),
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        self.get_keyboard_state_called = True
        return KeyboardStateObservation(
            keys={
                KeyboardKey.SHIFT: False,
                KeyboardKey.CTRL: False,
                KeyboardKey.ALT: False,
            }
        )

    def shell(self, action: ShellCommandAction) -> bool:
        self.execute_command_called = True
        self.last_command = action
        return True

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        self.execute_keyboard_key_down_called = True
        self.last_key_down = action
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        self.execute_keyboard_key_release_called = True
        self.last_key_release = action
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        self.execute_mouse_move_called = True
        self.last_mouse_move = action
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        self.execute_mouse_scroll_called = True
        self.last_mouse_scroll = action
        return True

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        self.execute_mouse_button_down_called = True
        self.last_mouse_button_down = action
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        self.execute_mouse_button_up_called = True
        self.last_mouse_button_up = action
        return True


class TestBaseComputer(unittest.TestCase):
    def setUp(self):
        self.computer = MockComputer()

    def test_get_screenshot(self):
        # Test that get_screenshot returns a ScreenshotObservation
        screenshot = self.computer.get_screenshot()
        self.assertTrue(self.computer.get_screenshot_called)
        self.assertIsInstance(screenshot, ScreenshotObservation)
        self.assertEqual(screenshot.screenshot, "mock_screenshot_data")

    def test_get_mouse_state(self):
        # Test that get_mouse_state returns a MouseStateObservation
        mouse_state = self.computer.get_mouse_state()
        self.assertTrue(self.computer.get_mouse_state_called)
        self.assertIsInstance(mouse_state, MouseStateObservation)
        self.assertEqual(mouse_state.position, (100, 200))

    def test_get_keyboard_state(self):
        # Test that get_keyboard_state returns a KeyboardStateObservation
        keyboard_state = self.computer.get_keyboard_state()
        self.assertTrue(self.computer.get_keyboard_state_called)
        self.assertIsInstance(keyboard_state, KeyboardStateObservation)
        self.assertFalse(keyboard_state.keys[KeyboardKey.SHIFT])

    def test_execute_command(self):
        # Test that execute_command calls the implementation
        command = ShellCommandAction(command="ls -la")
        result = self.computer.shell(command)
        self.assertTrue(self.computer.execute_command_called)
        self.assertEqual(self.computer.last_command, command)
        self.assertTrue(result)

    def test_execute_keyboard_key_press(self):
        # Test that execute_keyboard_key_press calls key_down and key_release
        with (
            patch.object(self.computer, "execute_keyboard_key_down") as mock_key_down,
            patch.object(
                self.computer, "execute_keyboard_key_release"
            ) as mock_key_release,
            patch("time.sleep") as mock_sleep,
        ):

            action = KeyboardKeyPressAction(key=KeyboardKey.ENTER, duration=0.5)
            result = self.computer.execute_keyboard_key_press(action)

            # Check that key_down was called with the right key
            mock_key_down.assert_called_once()
            key_down_arg = mock_key_down.call_args[0][0]
            self.assertEqual(key_down_arg.key, KeyboardKey.ENTER)

            # Check that sleep was called with the right duration
            mock_sleep.assert_called_once_with(0.5)

            # Check that key_release was called with the right key
            mock_key_release.assert_called_once()
            key_release_arg = mock_key_release.call_args[0][0]
            self.assertEqual(key_release_arg.key, KeyboardKey.ENTER)

            # Check that the method returned True
            self.assertTrue(result)

    def test_execute_keyboard_keys_press(self):
        # Test that execute_keyboard_keys_press calls keys_down and keys_release
        with (
            patch.object(self.computer, "execute_keyboard_keys_down") as mock_keys_down,
            patch.object(
                self.computer, "execute_keyboard_keys_release"
            ) as mock_keys_release,
        ):

            action = KeyboardKeysPressAction(
                keys=[KeyboardKey.CTRL, KeyboardKey.C], duration=0.5
            )
            result = self.computer.execute_keyboard_keys_press(action)

            # Check that keys_down was called with the right keys
            mock_keys_down.assert_called_once_with(action.keys)

            # Check that keys_release was called with the right keys
            mock_keys_release.assert_called_once_with(action.keys)

    def test_execute_keyboard_keys_down(self):
        # Test that execute_keyboard_keys_down calls key_down for each key
        with patch.object(self.computer, "execute_keyboard_key_down") as mock_key_down:
            action = KeyboardKeysDownAction(keys=[KeyboardKey.CTRL, KeyboardKey.ALT])
            self.computer.execute_keyboard_keys_down(action)

            # Check that key_down was called twice (once for each key)
            self.assertEqual(mock_key_down.call_count, 2)

            # Check that key_down was called with the right keys
            call_args_list = mock_key_down.call_args_list
            self.assertEqual(call_args_list[0][0][0].key, KeyboardKey.CTRL)
            self.assertEqual(call_args_list[1][0][0].key, KeyboardKey.ALT)

    def test_execute_keyboard_keys_release(self):
        # Test that execute_keyboard_keys_release calls key_release for each key
        with patch.object(
            self.computer, "execute_keyboard_key_release"
        ) as mock_key_release:
            # Make mock_key_release return True
            mock_key_release.return_value = True

            action = KeyboardKeysReleaseAction(keys=[KeyboardKey.CTRL, KeyboardKey.ALT])
            result = self.computer.execute_keyboard_keys_release(action)

            # Check that key_release was called twice (once for each key)
            self.assertEqual(mock_key_release.call_count, 2)

            # Check that key_release was called with the right keys
            call_args_list = mock_key_release.call_args_list
            self.assertEqual(call_args_list[0][0][0].key, KeyboardKey.CTRL)
            self.assertEqual(call_args_list[1][0][0].key, KeyboardKey.ALT)

            # Check that the method returned True
            self.assertTrue(result)

            # Test with one key_release failing
            mock_key_release.reset_mock()
            mock_key_release.side_effect = [True, False]

            result = self.computer.execute_keyboard_keys_release(action)

            # Check that the method returned False
            self.assertFalse(result)

    def test_execute_keyboard_hotkey(self):
        # Test that execute_keyboard_hotkey calls key_down and key_release in the right order
        with (
            patch.object(self.computer, "execute_keyboard_key_down") as mock_key_down,
            patch.object(
                self.computer, "execute_keyboard_key_release"
            ) as mock_key_release,
        ):

            # Make both mocks return True
            mock_key_down.return_value = True
            mock_key_release.return_value = True

            action = KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S])
            result = self.computer.execute_keyboard_hotkey(action)

            # Check that key_down was called twice (once for each key)
            self.assertEqual(mock_key_down.call_count, 2)

            # Check that key_release was called twice (once for each key)
            self.assertEqual(mock_key_release.call_count, 2)

            # Check that key_down was called with the right keys in the right order
            key_down_calls = mock_key_down.call_args_list
            self.assertEqual(key_down_calls[0][0][0].key, KeyboardKey.CTRL)
            self.assertEqual(key_down_calls[1][0][0].key, KeyboardKey.S)

            # Check that key_release was called with the right keys in reverse order
            key_release_calls = mock_key_release.call_args_list
            self.assertEqual(key_release_calls[0][0][0].key, KeyboardKey.S)
            self.assertEqual(key_release_calls[1][0][0].key, KeyboardKey.CTRL)

            # Check that the method returned True
            self.assertTrue(result)

            # Test with one key_down failing
            mock_key_down.reset_mock()
            mock_key_release.reset_mock()
            mock_key_down.side_effect = [True, False]

            result = self.computer.execute_keyboard_hotkey(action)

            # Check that the method returned False
            self.assertFalse(result)

    def test_execute_type(self):
        # Test that execute_type calls keyboard_key_press for each character
        with patch.object(
            self.computer, "execute_keyboard_key_press"
        ) as mock_key_press:
            action = TypeAction(text="Hello")
            result = self.computer.execute_type(action)

            # Check that key_press was called 5 times (once for each character)
            self.assertEqual(mock_key_press.call_count, 5)

            # Check that key_press was called with the right characters
            call_args_list = mock_key_press.call_args_list
            self.assertEqual(call_args_list[0][0][0].key, "H")
            self.assertEqual(call_args_list[1][0][0].key, "e")
            self.assertEqual(call_args_list[2][0][0].key, "l")
            self.assertEqual(call_args_list[3][0][0].key, "l")
            self.assertEqual(call_args_list[4][0][0].key, "o")

            # Check that the method returned True
            self.assertTrue(result)

    def test_execute_click(self):
        # Test that execute_click calls mouse_move, mouse_button_down, and mouse_button_up
        with (
            patch.object(self.computer, "execute_mouse_move") as mock_mouse_move,
            patch.object(
                self.computer, "execute_mouse_button_down"
            ) as mock_button_down,
            patch.object(self.computer, "execute_mouse_button_up") as mock_button_up,
            patch("time.sleep") as mock_sleep,
        ):

            action = ClickAction(
                x=100,
                y=200,
                move_duration=0.5,
                press_duration=0.3,
                button=MouseButton.LEFT,
            )
            result = self.computer.execute_click(action)

            # Check that mouse_move was called with the right parameters
            mock_mouse_move.assert_called_once()
            move_arg = mock_mouse_move.call_args[0][0]
            self.assertEqual(move_arg.x, 100)
            self.assertEqual(move_arg.y, 200)
            self.assertEqual(move_arg.move_duration, 0.5)

            # Check that mouse_button_down was called with the right button
            mock_button_down.assert_called_once()
            down_arg = mock_button_down.call_args[0][0]
            self.assertEqual(down_arg.button, MouseButton.LEFT)

            # Check that sleep was called with the right duration
            mock_sleep.assert_called_once_with(0.3)

            # Check that mouse_button_up was called with the right button
            mock_button_up.assert_called_once()
            up_arg = mock_button_up.call_args[0][0]
            self.assertEqual(up_arg.button, MouseButton.LEFT)

            # Check that the method returned True
            self.assertTrue(result)

    def test_execute_double_click(self):
        # Test that execute_double_click calls execute_click twice
        with (
            patch.object(self.computer, "execute_click") as mock_click,
            patch("time.sleep") as mock_sleep,
        ):

            action = DoubleClickAction(
                x=100,
                y=200,
                move_duration=0.5,
                press_duration=0.3,
                button=MouseButton.LEFT,
                double_click_interval_seconds=0.2,
            )
            result = self.computer.execute_double_click(action)

            # Check that click was called twice
            self.assertEqual(mock_click.call_count, 2)

            # Check that click was called with the right parameters
            click_args = mock_click.call_args_list
            for call in click_args:
                click_action = call[0][0]
                self.assertEqual(click_action.x, 100)
                self.assertEqual(click_action.y, 200)
                self.assertEqual(click_action.move_duration, 0.5)
                self.assertEqual(click_action.press_duration, 0.3)
                self.assertEqual(click_action.button, MouseButton.LEFT)

            # Check that sleep was called with the right duration
            mock_sleep.assert_called_once_with(0.2)

            # Check that the method returned True
            self.assertTrue(result)

    def test_execute_drag(self):
        # Test that execute_drag calls mouse_move, mouse_button_down, mouse_move, and mouse_button_up
        with (
            patch.object(self.computer, "execute_mouse_move") as mock_mouse_move,
            patch.object(
                self.computer, "execute_mouse_button_down"
            ) as mock_button_down,
            patch.object(self.computer, "execute_mouse_button_up") as mock_button_up,
        ):

            action = DragAction(
                start_x=100,
                start_y=200,
                end_x=300,
                end_y=400,
                move_duration=0.5,
                button=MouseButton.LEFT,
            )
            result = self.computer.execute_drag(action)

            # Check that mouse_move was called twice
            self.assertEqual(mock_mouse_move.call_count, 2)

            # Check that mouse_move was called with the right parameters
            move_args = mock_mouse_move.call_args_list
            self.assertEqual(
                move_args[0][1], {"x": 100, "y": 200, "move_duration": 0.5}
            )
            self.assertEqual(
                move_args[1][1], {"x": 300, "y": 400, "move_duration": 0.5}
            )

            # Check that mouse_button_down was called with the right button
            mock_button_down.assert_called_once_with(button=MouseButton.LEFT)

            # Check that mouse_button_up was called with the right button
            mock_button_up.assert_called_once_with(button=MouseButton.LEFT)

            # Check that the method returned True
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
