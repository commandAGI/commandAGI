import time
from abc import abstractmethod

from commandAGI_LAB.types import (ClickAction, CommandAction,
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
                                                    TypeAction)
from pydantic import BaseModel


class BaseComputer(BaseModel):
    @abstractmethod
    def get_screenshot(self) -> ScreenshotObservation:
        """Return a ScreenshotObservation containing the screenshot encoded as a base64 string."""

    @abstractmethod
    def get_mouse_state(self) -> MouseStateObservation:
        """Return a MouseStateObservation containing the current mouse button states and position."""

    @abstractmethod
    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return a KeyboardStateObservation with the current keyboard keys mapped to their states."""

    @abstractmethod
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the environment and return True if successful.

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """

    def execute_keyboard_keys_press(self, action: KeyboardKeysPressAction):
        """Execute pressing keyboard keys."""
        self.execute_keyboard_keys_down(action.keys)
        self.execute_keyboard_keys_release(action.keys)

    def execute_keyboard_keys_down(self, action: KeyboardKeysDownAction):
        """Execute key down for each keyboard key."""
        for key in action.keys:
            self.execute_keyboard_key_down(key)

    def execute_keyboard_keys_release(self, action: KeyboardKeysReleaseAction):
        """Execute key release for each keyboard key."""
        success = True
        for key in action.keys:
            success_i = self.execute_keyboard_key_release(key)
            if not success_i:
                success = False
        return success

    def execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key with a specified duration."""
        self.execute_keyboard_key_down(KeyboardKeyDownAction(key=action.key))
        time.sleep(action.duration)
        self.execute_keyboard_key_release(KeyboardKeyReleaseAction(key=action.key))
        return True

    @abstractmethod
    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        """Execute key down for a keyboard key."""

    @abstractmethod
    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        """Execute key release for a keyboard key."""

    def execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        success = True
        for key in action.keys:
            success_i = self.execute_keyboard_key_down(key)
            if not success_i:
                success = False
        for key in reversed(action.keys):
            success_i = self.execute_keyboard_key_release(key)
            if not success_i:
                success = False
        return success

    def execute_type(self, action: TypeAction):
        """Execute typing the given text."""
        for char in action.text:
            self.execute_keyboard_key_press(KeyboardKeyPressAction(key=char))
        return True

    @abstractmethod
    def execute_mouse_move(self, action: MouseMoveAction):
        """Execute moving the mouse to (x, y) over the move duration."""

    @abstractmethod
    def execute_mouse_scroll(self, action: MouseScrollAction):
        """Execute mouse scroll by a given amount."""

    @abstractmethod
    def execute_mouse_button_down(self, action: MouseButtonDownAction):
        """Execute mouse button down action."""

    @abstractmethod
    def execute_mouse_button_up(self, action: MouseButtonUpAction):
        """Execute mouse button up action."""

    def execute_click(self, action: ClickAction) -> bool:
        """Execute a click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        move_action = MouseMoveAction(
            x=action.x, y=action.y, move_duration=action.move_duration
        )
        self.execute_mouse_move(move_action)
        down_action = MouseButtonDownAction(button=action.button)
        self.execute_mouse_button_down(down_action)
        time.sleep(action.press_duration)
        up_action = MouseButtonUpAction(button=action.button)
        self.execute_mouse_button_up(up_action)
        return True

    def execute_double_click(self, action: DoubleClickAction):
        # TODO: define DoubleClickAction and add to ComputerAction
        """Execute a double click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        self.execute_click(ClickAction(x=action.x, y=action.y, move_duration=action.move_duration, press_duration=action.press_duration, button=action.button))
        time.sleep(action.double_click_interval_seconds)
        self.execute_click(ClickAction(x=action.x, y=action.y, move_duration=action.move_duration, press_duration=action.press_duration, button=action.button))
        return True

    def execute_drag(self, action: DragAction):
        """Execute a drag action using the primitive mouse operations."""
        # Move to the starting position
        self.execute_mouse_move(
            x=action.start_x, y=action.start_y, move_duration=action.move_duration
        )
        # Press the mouse button down
        self.execute_mouse_button_down(button=action.button)
        # Move to the ending position while holding down the mouse button
        self.execute_mouse_move(
            x=action.end_x, y=action.end_y, move_duration=action.move_duration
        )
        # Release the mouse button
        self.execute_mouse_button_up(button=action.button)
        return True
