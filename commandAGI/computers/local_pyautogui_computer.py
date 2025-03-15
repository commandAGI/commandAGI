import base64
import datetime
import io
import os
import subprocess
import tempfile
import time
from typing import Literal, Optional, Union

try:
    import mss
    import pyautogui
    from PIL import Image
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandAGI with the local extra:\n\npip install commandAGI[local]"
    )

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI.computers.local_computer import LocalComputer
from commandAGI.types import (
    KeyboardKey,
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
    ShellCommandAction,
    TypeAction,
)


# PyAutoGUI-specific mappings
def mouse_button_to_pyautogui(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to PyAutoGUI button name.

    PyAutoGUI uses string names for mouse buttons:
    'left' = left button
    'middle' = middle button
    'right' = right button
    'primary' = primary button (usually left)
    'secondary' = secondary button (usually right)
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # PyAutoGUI mouse button mapping
    pyautogui_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right",
    }

    return pyautogui_button_mapping.get(
        button, "left"
    )  # Default to left button if not found


def keyboard_key_to_pyautogui(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to PyAutoGUI key name.

    PyAutoGUI uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # PyAutoGUI-specific key mappings
    pyautogui_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "enter",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "esc",
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
        KeyboardKey.LCTRL: "ctrlleft",
        KeyboardKey.RCTRL: "ctrlright",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "altleft",
        KeyboardKey.RALT: "altright",
        KeyboardKey.META: "win",  # Windows key
        KeyboardKey.LMETA: "winleft",
        KeyboardKey.RMETA: "winright",
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
    return pyautogui_key_mapping.get(key, key.value)


class LocalPyAutoGUIComputer(LocalComputer):
    def __init__(self):
        super().__init__()

    def reset_state(self):
        """Reset environment and return initial observation"""
        self.logger.info("Resetting environment state (showing desktop)")
        # Show desktop to reset the environment state
        pyautogui.hotkey("win", "d")
        time.sleep(1)  # Give windows time to minimize

    def _get_mouse_position(self) -> tuple[int, int]:
        """Return current mouse position."""
        x, y = pyautogui.position()
        self.logger.debug(f"Getting mouse position: ({x}, {y})")
        return (x, y)

    def _get_mouse_button_states(self) -> dict[str, bool]:
        """Return states of mouse buttons."""
        self.logger.debug("PyAutoGUI does not support getting mouse button states")
        raise NotImplementedError(
            "PyAutoGUI does not support getting mouse button states"
        )

    def _get_keyboard_key_states(self) -> dict[str, bool]:
        """Return states of keyboard keys."""
        self.logger.debug("PyAutoGUI does not support getting keyboard key states")
        raise NotImplementedError(
            "PyAutoGUI does not support getting keyboard key states"
        )

    def _execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        pyautogui_key = keyboard_key_to_pyautogui(key)
        self.logger.debug(f"Pressing key down: {key} (PyAutoGUI key: {pyautogui_key})")
        pyautogui.keyDown(pyautogui_key)

    def _execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        pyautogui_key = keyboard_key_to_pyautogui(key)
        self.logger.debug(f"Releasing key: {key} (PyAutoGUI key: {pyautogui_key})")
        pyautogui.keyUp(pyautogui_key)

    def _execute_type(self, text: str):
        """Type text using PyAutoGUI."""
        self.logger.debug(f"Typing text: {text}")
        pyautogui.write(text)

    def _execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5):
        """Move mouse to specified coordinates using PyAutoGUI."""
        self.logger.debug(f"Moving mouse to: ({x}, {y}) with duration {move_duration}")
        pyautogui.moveTo(x, y, duration=move_duration)

    def _execute_mouse_scroll(self, amount: float):
        """Scroll mouse using PyAutoGUI."""
        self.logger.debug(f"Scrolling mouse by: {amount}")
        pyautogui.scroll(amount)

    def _execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using PyAutoGUI."""
        pyautogui_button = mouse_button_to_pyautogui(button)
        self.logger.debug(
            f"Pressing mouse button down: {button} (PyAutoGUI button: {pyautogui_button})"
        )
        pyautogui.mouseDown(button=pyautogui_button)

    def _execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using PyAutoGUI."""
        pyautogui_button = mouse_button_to_pyautogui(button)
        self.logger.debug(
            f"Releasing mouse button: {button} (PyAutoGUI button: {pyautogui_button})"
        )
        pyautogui.mouseUp(button=pyautogui_button)
