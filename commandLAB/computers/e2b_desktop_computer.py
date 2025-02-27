import base64
import io
import os
import datetime
from typing import Union, Optional, Literal


try:
    from e2b_desktop import Sandbox
    from PIL import Image
except ImportError:
    raise ImportError(
        "The E2B Desktop dependencies are not installed. Please install commandLAB with the e2b_desktop extra:\n\npip install commandLAB[e2b_desktop]"
    )

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    ClickAction,
    CommandAction,
    DoubleClickAction,
    KeyboardKey,
    KeyboardKeyPressAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
    TypeAction,
)
from commandLAB._utils.config import APPDIR
from commandLAB._utils.screenshot import process_screenshot


# E2B Desktop-specific mappings
def mouse_button_to_e2b(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to E2B Desktop button name.

    E2B Desktop uses the following button names:
    'left' = left button
    'middle' = middle button
    'right' = right button
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # E2B Desktop mouse button mapping
    e2b_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right",
    }

    return e2b_button_mapping.get(button, "left")  # Default to left button if not found


def keyboard_key_to_e2b(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to E2B Desktop key name.

    E2B Desktop uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # E2B Desktop key mappings
    e2b_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "return",  # E2B uses "return" not "enter"
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "esc",  # E2B uses "esc" not "escape"
        KeyboardKey.HOME: "home",
        KeyboardKey.END: "end",
        KeyboardKey.PAGE_UP: "pageup",
        KeyboardKey.PAGE_DOWN: "pagedown",
        # Arrow keys
        KeyboardKey.UP: "up",
        KeyboardKey.DOWN: "down",
        KeyboardKey.LEFT: "left",
        KeyboardKey.RIGHT: "right",
        # Modifier keys
        KeyboardKey.SHIFT: "shift",
        KeyboardKey.CTRL: "ctrl",
        KeyboardKey.LCTRL: "ctrl",  # E2B may not distinguish left/right
        KeyboardKey.RCTRL: "ctrl",  # E2B may not distinguish left/right
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # E2B may not distinguish left/right
        KeyboardKey.RALT: "alt",  # E2B may not distinguish left/right
        KeyboardKey.META: "win",  # Windows key
        KeyboardKey.LMETA: "win",  # E2B may not distinguish left/right
        KeyboardKey.RMETA: "win",  # E2B may not distinguish left/right
        # Function keys
        KeyboardKey.F1: "f1",
        KeyboardKey.F2: "f2",
        KeyboardKey.F3: "f3",
        KeyboardKey.F4: "f4",
        KeyboardKey.F5: "f5",
        KeyboardKey.F6: "f6",
        KeyboardKey.F7: "f7",
        KeyboardKey.F8: "f8",
        KeyboardKey.F9: "f9",
        KeyboardKey.F10: "f10",
        KeyboardKey.F11: "f11",
        KeyboardKey.F12: "f12",
    }

    # For letter keys and number keys, use the value directly
    return e2b_key_mapping.get(key, key.value)


class E2BDesktopComputer(BaseComputer):
    """Environment that uses E2B Desktop Sandbox for secure computer interactions"""

    def __init__(self, video_stream=False):
        super().__init__()
        self.video_stream = video_stream
        self.desktop = None

    def _start(self):
        """Start the E2B desktop environment."""
        if not self.desktop:
            self.logger.info("Initializing E2B Desktop Sandbox")
            self.desktop = Sandbox(video_stream=self.video_stream)
            self.logger.info("E2B Desktop Sandbox initialized successfully")
        return True

    def _stop(self):
        """Stop the E2B desktop environment."""
        if self.desktop:
            self.logger.info("Closing E2B Desktop Sandbox")
            # E2B sandbox automatically closes when object is destroyed
            self.desktop = None
            self.logger.info("E2B Desktop Sandbox closed successfully")
        return True

    def reset_state(self):
        """Reset the desktop environment and return initial observation"""
        self.logger.info("Resetting E2B Desktop environment state")
        # Show desktop to reset the environment state
        if self.desktop:
            self.logger.debug("Showing desktop with Win+D hotkey")
            self.desktop.hotkey("win", "d")
        else:
            self.logger.debug("Desktop not initialized, starting it")
            self._start()

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> ScreenshotObservation:
        """Return a screenshot of the current state in the specified format.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        # Create a temporary file to store the screenshot
        temp_screenshot_path = self._new_screenshot_name

        # Take the screenshot using E2B Desktop
        self.desktop.screenshot(temp_screenshot_path)

        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=temp_screenshot_path,
            output_format=format,
            input_format="path",
            computer_name="e2b",
            cleanup_temp_file=True,
        )

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from E2B Desktop."""
        self.logger.debug("E2B Desktop does not support getting mouse state")
        raise NotImplementedError("E2B Desktop does not support getting mouse state")

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from E2B Desktop."""
        self.logger.debug("E2B Desktop does not support getting keyboard state")
        raise NotImplementedError("E2B Desktop does not support getting keyboard state")

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the E2B Desktop VM."""
        try:
            self.desktop.commands.run(action.command)
            return True
        except Exception as e:
            self.logger.error(f"Error executing command via E2B Desktop: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using action signature."""
        # E2B Desktop doesn't have direct key_down method, use PyAutoGUI
        e2b_key = keyboard_key_to_e2b(action.key)
        try:
            self.desktop.pyautogui(f"pyautogui.keyDown('{e2b_key}')")
            return True
        except Exception as e:
            self.logger.error(f"Error executing key down via E2B Desktop: {e}")
            return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using action signature."""
        # E2B Desktop doesn't have direct key_up method, use PyAutoGUI
        e2b_key = keyboard_key_to_e2b(action.key)
        try:
            self.desktop.pyautogui(f"pyautogui.keyUp('{e2b_key}')")
            return True
        except Exception as e:
            self.logger.error(f"Error executing key release via E2B Desktop: {e}")
            return False

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using E2B Desktop."""
        try:
            self.desktop.write(action.text)
            return True
        except Exception as e:
            self.logger.error(f"Error typing text via E2B Desktop: {e}")
            return False

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using E2B Desktop."""
        try:
            self.logger.debug(f"Moving mouse to: ({action.x}, {action.y})")
            # E2B Desktop doesn't have a direct move duration parameter
            self.desktop.mouse_move(action.x, action.y)
            return True
        except Exception as e:
            self.logger.error(f"Error moving mouse via E2B Desktop: {e}")
            return False

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using E2B Desktop."""
        try:
            # E2B Desktop scroll takes an integer amount
            self.desktop.scroll(int(action.amount))
            return True
        except Exception as e:
            self.logger.error(f"Error scrolling mouse via E2B Desktop: {e}")
            return False

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using PyAutoGUI through E2B Desktop."""
        e2b_button = mouse_button_to_e2b(action.button)
        try:
            self.desktop.pyautogui(f"pyautogui.mouseDown(button='{e2b_button}')")
            return True
        except Exception as e:
            self.logger.error(f"Error pressing mouse button via E2B Desktop: {e}")
            return False

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using PyAutoGUI through E2B Desktop."""
        e2b_button = mouse_button_to_e2b(action.button)
        try:
            self.desktop.pyautogui(f"pyautogui.mouseUp(button='{e2b_button}')")
            return True
        except Exception as e:
            self.logger.error(f"Error releasing mouse button via E2B Desktop: {e}")
            return False

    def _execute_click(self, action: ClickAction) -> bool:
        """Execute a click action using E2B Desktop's click methods."""
        try:
            # Move to position first
            self.desktop.mouse_move(action.x, action.y)

            # Then click using the appropriate method
            e2b_button = mouse_button_to_e2b(action.button)
            if e2b_button == "left":
                self.desktop.left_click()
            elif e2b_button == "right":
                self.desktop.right_click()
            elif e2b_button == "middle":
                self.desktop.middle_click()
            return True
        except Exception as e:
            self.logger.error(f"Error clicking: {e}")
            return False

    def _execute_double_click(self, action: DoubleClickAction) -> bool:
        """Execute a double click action using E2B Desktop's double_click method."""
        try:
            # Move to position first
            self.desktop.mouse_move(action.x, action.y)

            # Then double click (E2B only supports left double click)
            self.desktop.double_click()
            return True
        except Exception as e:
            self.logger.error(f"Error double clicking: {e}")
            return False

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key."""
        e2b_key = keyboard_key_to_e2b(action.key)
        try:
            # E2B doesn't have a direct press method, use PyAutoGUI
            self.desktop.pyautogui(f"pyautogui.press('{e2b_key}')")
            return True
        except Exception as e:
            self.logger.error(f"Error pressing key: {e}")
            return False

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey using E2B Desktop's hotkey method."""
        # Convert keys to E2B format
        e2b_keys = [keyboard_key_to_e2b(key) for key in action.keys]

        try:
            # E2B Desktop's hotkey method takes individual arguments, not a list
            self.desktop.hotkey(*e2b_keys)
            return True
        except Exception as e:
            self.logger.error(f"Error executing hotkey: {e}")
            return False

    def locate_on_screen(self, text):
        """Find text on screen and return coordinates.

        This is a direct wrapper for E2B Desktop's locate_on_screen method.
        """
        try:
            return self.desktop.locate_on_screen(text)
        except Exception as e:
            self.logger.error(f"Error locating text on screen: {e}")
            return None

    def open_file(self, file_path):
        """Open a file with the default application.

        This is a direct wrapper for E2B Desktop's open method.
        """
        try:
            self.desktop.open(file_path)
            return True
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            return False

    def get_video_stream_url(self) -> str:
        """Get the URL for the video stream of the E2B Desktop instance."""
        if not self.video_stream:
            self.logger.warning(
                "Warning: Video stream was not enabled during initialization"
            )
            return ""

        try:
            # The method name might be different based on the API
            # Check if the method exists
            if hasattr(self.desktop, "get_video_stream_url"):
                return self.desktop.get_video_stream_url()
            else:
                self.logger.warning(
                    "Warning: get_video_stream_url method not found in E2B Desktop API"
                )
                return ""
        except Exception as e:
            self.logger.error(f"Error getting video stream URL: {e}")
            return ""
