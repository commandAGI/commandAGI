import base64
import io
import os
import datetime
import subprocess
import tempfile
import time
from typing import Union, Optional, Literal

try:
    import mss
    import pyautogui
    from PIL import Image
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandLAB with the local extra:\n\npip install commandLAB[local]"
    )

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
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
    TypeAction,
)
from commandLAB._utils.config import APPDIR
from commandLAB._utils.screenshot import process_screenshot


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
        MouseButton.RIGHT: "right"
    }
    
    return pyautogui_button_mapping.get(button, "left")  # Default to left button if not found

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


class LocalPyAutoGUIComputer(BaseComputer):
    def __init__(self):
        super().__init__()
        self._sct = None
        self._temp_dir = None

    def _start(self):
        """Start the local computer environment."""
        if not self._sct:
            self.logger.info("Initializing MSS screen capture")
            self._sct = mss.mss()
        if not self._temp_dir:
            self.logger.info("Creating temporary directory")
            self._temp_dir = tempfile.mkdtemp()
        self.logger.info("Local PyAutoGUI computer started")
        return True

    def _stop(self):
        """Stop the local computer environment."""
        if self._sct:
            self.logger.info("Closing MSS screen capture")
            self._sct.close()
            self._sct = None
        if self._temp_dir:
            self.logger.info("Cleaning up temporary directory")
            self._temp_dir = None
        self.logger.info("Local PyAutoGUI computer stopped")
        return True

    def reset_state(self):
        """Reset environment and return initial observation"""
        self.logger.info("Resetting environment state (showing desktop)")
        # Show desktop to reset the environment state
        pyautogui.hotkey("win", "d")
        time.sleep(1)  # Give windows time to minimize

    def _get_screenshot(self, display_id: int = 0, format: Literal['base64', 'PIL', 'path'] = 'PIL') -> ScreenshotObservation:
        """Return a screenshot of the current state in the specified format.
        
        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        # Capture screenshot using mss
        self.logger.debug(f"Capturing screenshot of display {display_id}")
        monitor = self._sct.monitors[display_id + 1]  # mss uses 1-based indexing
        screenshot = self._sct.grab(monitor)
        
        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=screenshot,
            output_format=format,
            input_format='PIL',
            computer_name="pyautogui"
        )

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return dummy mouse state using pyautogui (pyautogui doesn't provide state, so we return a default value)."""
        self.logger.debug("PyAutoGUI does not support getting mouse state")
        raise NotImplementedError(
            "LocalComputeEnv does not support mouse state observation"
        )

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return dummy keyboard state as pyautogui doesn't track key states."""
        self.logger.debug("PyAutoGUI does not support getting keyboard state")
        raise NotImplementedError(
            "LocalComputeEnv does not support keyboard state observation"
        )

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command using subprocess."""
        try:
            self.logger.info(f"Executing command: {action.command}")
            result = subprocess.run(
                action.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=action.timeout if action.timeout is not None else 10,
            )
            if result.returncode == 0:
                self.logger.info("Command executed successfully")
            else:
                self.logger.warning(f"Command returned non-zero exit code: {result.returncode}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {action.timeout} seconds")
            return False
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key."""
        try:
            pyautogui_key = keyboard_key_to_pyautogui(action.key)
            self.logger.debug(f"Pressing key down: {action.key} (PyAutoGUI key: {pyautogui_key})")
            pyautogui.keyDown(pyautogui_key)
            return True
        except Exception as e:
            self.logger.error(f"Error executing key down: {e}")
            return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key."""
        try:
            pyautogui_key = keyboard_key_to_pyautogui(action.key)
            self.logger.debug(f"Releasing key: {action.key} (PyAutoGUI key: {pyautogui_key})")
            pyautogui.keyUp(pyautogui_key)
            return True
        except Exception as e:
            self.logger.error(f"Error executing key release: {e}")
            return False

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using PyAutoGUI."""
        try:
            self.logger.debug(f"Typing text: {action.text}")
            pyautogui.write(action.text)
            return True
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using PyAutoGUI."""
        try:
            self.logger.debug(f"Moving mouse to: ({action.x}, {action.y}) with duration {action.move_duration}")
            pyautogui.moveTo(action.x, action.y, duration=action.move_duration)
            return True
        except Exception as e:
            self.logger.error(f"Error moving mouse: {e}")
            return False

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using PyAutoGUI."""
        try:
            self.logger.debug(f"Scrolling mouse by: {action.amount}")
            pyautogui.scroll(action.amount)
            return True
        except Exception as e:
            self.logger.error(f"Error scrolling mouse: {e}")
            return False

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using PyAutoGUI."""
        try:
            pyautogui_button = mouse_button_to_pyautogui(action.button)
            self.logger.debug(f"Pressing mouse button down: {action.button} (PyAutoGUI button: {pyautogui_button})")
            pyautogui.mouseDown(button=pyautogui_button)
            return True
        except Exception as e:
            self.logger.error(f"Error pressing mouse button: {e}")
            return False

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using PyAutoGUI."""
        try:
            pyautogui_button = mouse_button_to_pyautogui(action.button)
            self.logger.debug(f"Releasing mouse button: {action.button} (PyAutoGUI button: {pyautogui_button})")
            pyautogui.mouseUp(button=pyautogui_button)
            return True
        except Exception as e:
            self.logger.error(f"Error releasing mouse button: {e}")
            return False
