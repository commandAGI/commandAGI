import base64
import io
import subprocess
import tempfile
import time

try:
    import mss
    import pyautogui
except ImportError:
    raise ImportError("pyautogui is not installed. Please install commandLAB with the local extra:\n\npip install commandLAB[local]")

from PIL import Image
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (CommandAction, KeyboardKey,
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
                                                    TypeAction)


class LocalPyAutoGUIComputer(BaseComputer):
    def __init__(self):
        super().__init__()
        self.sct = mss.mss()
        self.last_screenshot = None
        self.temp_dir = tempfile.mkdtemp()

    def reset(self):
        """Reset environment and return initial observation"""
        pyautogui.hotkey("win", "d")
        time.sleep(1)  # Give windows time to minimize

        return self.get_observation()

    def close(self):
        """Clean up resources"""
        self.sct.close()

    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        screenshot = self.sct.grab(self.sct.monitors[1])  # Primary monitor
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return ScreenshotObservation(screenshot=b64_screenshot)

    def get_mouse_state(self) -> MouseStateObservation:
        """Return dummy mouse state using pyautogui (pyautogui doesn't provide state, so we return a default value)."""
        raise NotImplementedError(
            "LocalComputeEnv does not support mouse state observation"
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return dummy keyboard state as pyautogui doesn't track key states."""
        raise NotImplementedError(
            "LocalComputeEnv does not support keyboard state observation"
        )

    def execute_command(self, action: CommandAction) -> bool:
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

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key."""
        pyautogui_key = KeyboardKey.to_pyautogui(action.key)
        pyautogui.keyDown(pyautogui_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key."""
        pyautogui_key = KeyboardKey.to_pyautogui(action.key)
        pyautogui.keyUp(pyautogui_key)
        return True

    def execute_type(self, action: TypeAction) -> bool:
        pyautogui.write(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        pyautogui.moveTo(action.x, action.y, duration=action.move_duration)
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        pyautogui.scroll(action.amount)
        return True

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        pyautogui_button = MouseButton.to_pyautogui(action.button)
        pyautogui.mouseDown(button=pyautogui_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        pyautogui_button = MouseButton.to_pyautogui(action.button)
        pyautogui.mouseUp(button=pyautogui_button)
        return True
