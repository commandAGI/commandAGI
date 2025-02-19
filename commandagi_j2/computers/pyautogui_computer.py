import subprocess
import time
import mss
from PIL import Image
import pyautogui
import io
import base64
from typing import Optional

from commandagi_j2.computers.base_computer import Computer
from commandagi_j2.envs.computer_types import (
    KeyboardKey,
    MouseButton,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)

class PyAutoGUIComputer(Computer):
    """Computer implementation using PyAutoGUI for local system control"""

    def __init__(self):
        self.sct = mss.mss()

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        """Capture screenshot using mss and return as base64 string"""
        screenshot = self.sct.grab(self.sct.monitors[1])  # Primary monitor
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_screenshot = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return ScreenshotObservation(screenshot=b64_screenshot)

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        """PyAutoGUI doesn't support mouse state observation"""
        return None

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        """PyAutoGUI doesn't support keyboard state observation"""
        return None

    def execute_command(self, action: CommandAction) -> bool:
        """Execute system command using subprocess"""
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

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Press down a keyboard key using PyAutoGUI"""
        pyautogui_key = KeyboardKey.to_pyautogui(action.key)
        pyautogui.keyDown(pyautogui_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Release a keyboard key using PyAutoGUI"""
        pyautogui_key = KeyboardKey.to_pyautogui(action.key)
        pyautogui.keyUp(pyautogui_key)
        return True

    def execute_type(self, action: TypeAction) -> bool:
        """Type text using PyAutoGUI"""
        pyautogui.write(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse cursor using PyAutoGUI"""
        pyautogui.moveTo(action.x, action.y, duration=action.move_duration)
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse wheel using PyAutoGUI"""
        pyautogui.scroll(action.amount)
        return True

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button using PyAutoGUI"""
        pyautogui_button = MouseButton.to_pyautogui(action.button)
        pyautogui.mouseDown(button=pyautogui_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using PyAutoGUI"""
        pyautogui_button = MouseButton.to_pyautogui(action.button)
        pyautogui.mouseUp(button=pyautogui_button)
        return True

    def close(self):
        """Clean up mss resources"""
        self.sct.close() 