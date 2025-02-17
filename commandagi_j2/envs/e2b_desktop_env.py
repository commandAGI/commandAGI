import os
import tempfile
import time
from e2b_desktop import Sandbox
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
from commandagi_j2.envs.computer_types import (
    ComputerAction,
    KeyboardKey,
    MouseButton,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
)

class E2BDesktopEnv(BaseComputerEnv):
    """Environment that uses E2B Desktop Sandbox for secure computer interactions"""

    def __init__(self, video_stream=False):
        super().__init__()
        self.desktop = Sandbox(video_stream=video_stream)

    def reset(self):
        """Reset the desktop environment and return initial observation"""
        self.desktop.hotkey("win", "d")  # Show desktop
        return self._get_observation()

    def step(self, action):
        """Execute action and return (observation, reward, done, info)"""
        success = self._execute_action(action)
        observation = self._get_observation()

        reward = 1.0 if success else -1.0
        done = False
        info = {"action_success": success}

        return observation, reward, done, info

    def close(self):
        """Clean up resources"""
        self.desktop = None  # E2B sandbox automatically closes when object is destroyed

    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state using Sandbox."""
        import os, tempfile

        screenshot = self.desktop.take_screenshot()
        output_path = os.path.join(tempfile.gettempdir(), "e2b_screenshot.png")
        with open(output_path, "wb") as f:
            f.write(screenshot)
        return ScreenshotObservation(screenshot=output_path)

    def get_mouse_state(self) -> MouseStateObservation:
        """Return dummy mouse state as Sandbox does not provide real-time states."""
        return MouseStateObservation(
            buttons={
                MouseButton.LEFT: False,
                MouseButton.MIDDLE: False,
                MouseButton.RIGHT: False,
            },
            position=(0, 0),
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return dummy keyboard state as Sandbox does not track key states."""
        return KeyboardStateObservation(keys={})

    def execute_command(self, command: str) -> bool:
        """Execute a system command in the host environment using subprocess."""
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
        e2b_key = KeyboardKey.to_e2b(key)
        return self.desktop.pyautogui(f"pyautogui.press('{e2b_key}')")

    def execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        e2b_key = KeyboardKey.to_e2b(key)
        return self.desktop.pyautogui(f"pyautogui.keyDown('{e2b_key}')")

    def execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        e2b_key = KeyboardKey.to_e2b(key)
        return self.desktop.pyautogui(f"pyautogui.keyUp('{e2b_key}')")

    def execute_type(self, text):
        return self.desktop.write(text)

    def execute_mouse_move(self, x, y, move_duration: float = 0.5):
        return self.desktop.mouse_move(x, y)

    def execute_mouse_scroll(self, amount: float):
        return self.desktop.pyautogui(f"pyautogui.scroll({amount})")

    def execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        e2b_button = MouseButton.to_e2b(button)
        return self.desktop.pyautogui(f"pyautogui.mouseDown(button='{e2b_button}')")

    def execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        e2b_button = MouseButton.to_e2b(button)
        return self.desktop.pyautogui(f"pyautogui.mouseUp(button='{e2b_button}')")

    def execute_click(self, x, y, move_duration: float, button: MouseButton):
        self.execute_mouse_move(x, y, move_duration)
        e2b_button = MouseButton.to_e2b(button)
        return self.desktop.pyautogui(f"pyautogui.click(button='{e2b_button}')")
