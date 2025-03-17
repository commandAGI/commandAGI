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

    def _keydown(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        pyautogui_key = keyboard_key_to_pyautogui(key)
        self.logger.debug(f"Pressing key down: {key} (PyAutoGUI key: {pyautogui_key})")
        pyautogui.keyDown(pyautogui_key)

    def _keyup(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        pyautogui_key = keyboard_key_to_pyautogui(key)
        self.logger.debug(f"Releasing key: {key} (PyAutoGUI key: {pyautogui_key})")
        pyautogui.keyUp(pyautogui_key)

    def _type(self, text: str):
        """Type text using PyAutoGUI."""
        self.logger.debug(f"Typing text: {text}")
        pyautogui.write(text)

    def _move(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to specified coordinates using PyAutoGUI."""
        self.logger.debug(f"Moving mouse to: ({x}, {y}) with duration {move_duration}")
        pyautogui.moveTo(x, y, duration=move_duration)

    def _scroll(self, amount: float):
        """Scroll mouse using PyAutoGUI."""
        self.logger.debug(f"Scrolling mouse by: {amount}")
        pyautogui.scroll(amount)

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using PyAutoGUI."""
        pyautogui_button = mouse_button_to_pyautogui(button)
        self.logger.debug(
            f"Pressing mouse button down: {button} (PyAutoGUI button: {pyautogui_button})"
        )
        pyautogui.mouseDown(button=pyautogui_button)

    def _mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using PyAutoGUI."""
        pyautogui_button = mouse_button_to_pyautogui(button)
        self.logger.debug(
            f"Releasing mouse button: {button} (PyAutoGUI button: {pyautogui_button})"
        )
        pyautogui.mouseUp(button=pyautogui_button)
