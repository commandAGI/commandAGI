import time
from typing import List
import mss
import io
from PIL import Image
import pyautogui
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
import tempfile
import os
from enum import Enum
from e2b_desktop import Sandbox
from commandagi_j2.envs.computer_types import KeyboardKey, ScreenshotObservation, MouseStateObservation, KeyboardStateObservation, MouseButton


class LocalComputeEnv(BaseComputerEnv):
    def __init__(self):
        super().__init__()
        self.sct = mss.mss()
        self.last_screenshot = None
        self.temp_dir = tempfile.mkdtemp()

    def reset(self):
        """Reset environment and return initial observation"""
        pyautogui.hotkey("win", "d")
        time.sleep(1)  # Give windows time to minimize

        return self._get_observation()

    def step(self, action):
        """Execute action and return (observation, reward, done, info)"""
        success = self._execute_action(action)
        observation = self._get_observation()

        # Simple reward structure
        reward = 1.0 if success else -1.0
        done = False  # In this case, episodes don't naturally terminate
        info = {"action_success": success}

        return observation, reward, done, info

    def close(self):
        """Clean up resources"""
        self.sct.close()

    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state using mss."""
        output_path = os.path.join(self.temp_dir, "screenshot.png")
        screenshot = self.sct.grab(self.sct.monitors[1])  # Primary monitor
        Image.frombytes("RGB", screenshot.size, screenshot.rgb).save(output_path)
        self.last_screenshot = output_path
        return ScreenshotObservation(screenshot=output_path)

    def get_mouse_state(self) -> MouseStateObservation:
        """Return dummy mouse state using pyautogui (pyautogui doesn't provide state, so we return a default value)."""
        return MouseStateObservation(
            position=pyautogui.position(),
            buttons={
                MouseButton.LEFT: False,
                MouseButton.MIDDLE: False,
                MouseButton.RIGHT: False
            }
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return dummy keyboard state as pyautogui doesn't track key states."""
        return KeyboardStateObservation(keys={})

    def execute_command(self, command: str) -> bool:
        """Execute a system command using subprocess."""
        try:
            import subprocess

            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error executing command: {e}")
            return False

    def execute_keyboard_key_press(self, key: KeyboardKey):
        """Execute pressing a keyboard key."""
        pyautogui_key = KeyboardKey.to_pyautogui(key)
        pyautogui.press(pyautogui_key)
        return True

    def execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        pyautogui_key = KeyboardKey.to_pyautogui(key)
        pyautogui.keyDown(pyautogui_key)
        return True

    def execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        pyautogui_key = KeyboardKey.to_pyautogui(key)
        pyautogui.keyUp(pyautogui_key)
        return True

    def execute_type(self, text):
        pyautogui.write(text)
        return True

    def execute_mouse_move(self, x, y, move_duration: float = 0.5):
        pyautogui.moveTo(x, y, duration=move_duration)
        return True

    def execute_mouse_scroll(self, amount: float):
        pyautogui.scroll(amount)
        return True

    def execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        pyautogui_button = MouseButton.to_pyautogui(button)
        pyautogui.mouseDown(button=pyautogui_button)
        return True

    def execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        pyautogui_button = MouseButton.to_pyautogui(button)
        pyautogui.mouseUp(button=pyautogui_button)
        return True

    def execute_click(self, x, y, move_duration: float, button: MouseButton):
        self.execute_mouse_move(x, y, move_duration)
        pyautogui_button = MouseButton.to_pyautogui(button)
        pyautogui.click(button=pyautogui_button)
        return True
