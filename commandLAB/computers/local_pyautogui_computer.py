import base64
import io
import subprocess
import tempfile
import time
from typing import Union, Optional

try:
    import mss
    import pyautogui
except ImportError:
    raise ImportError(
        "pyautogui is not installed. Please install commandLAB with the local extra:\n\npip install commandLAB[local]"
    )

from PIL import Image
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
            self._sct = mss.mss()
        if not self._temp_dir:
            self._temp_dir = tempfile.mkdtemp()
        return True

    def _stop(self):
        """Stop the local computer environment."""
        if self._sct:
            self._sct.close()
            self._sct = None
        if self._temp_dir:
            self._temp_dir = None
        return True

    def reset_state(self):
        """Reset environment and return initial observation"""
        # Show desktop to reset the environment state
        pyautogui.hotkey("win", "d")
        time.sleep(1)  # Give windows time to minimize

    def _get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        screenshot = self._sct.grab(self._sct.monitors[1])  # Primary monitor
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return ScreenshotObservation(screenshot=b64_screenshot)

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return dummy mouse state using pyautogui (pyautogui doesn't provide state, so we return a default value)."""
        raise NotImplementedError(
            "LocalComputeEnv does not support mouse state observation"
        )

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return dummy keyboard state as pyautogui doesn't track key states."""
        raise NotImplementedError(
            "LocalComputeEnv does not support keyboard state observation"
        )

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command using subprocess."""
        try:
            result = subprocess.run(
                action.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=action.timeout if action.timeout is not None else 10,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error executing command: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key."""
        pyautogui_key = keyboard_key_to_pyautogui(action.key)
        pyautogui.keyDown(pyautogui_key)
        return True

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key."""
        pyautogui_key = keyboard_key_to_pyautogui(action.key)
        pyautogui.keyUp(pyautogui_key)
        return True

    def _execute_type(self, action: TypeAction) -> bool:
        pyautogui.write(action.text)
        return True

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        pyautogui.moveTo(action.x, action.y, duration=action.move_duration)
        return True

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        pyautogui.scroll(action.amount)
        return True

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        pyautogui_button = mouse_button_to_pyautogui(action.button)
        pyautogui.mouseDown(button=pyautogui_button)
        return True

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        pyautogui_button = mouse_button_to_pyautogui(action.button)
        pyautogui.mouseUp(button=pyautogui_button)
        return True
