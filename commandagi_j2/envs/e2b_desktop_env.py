import os
import tempfile
from e2b_desktop import Sandbox
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
from commandagi_j2.envs.computer_actions import ComputerAction


class E2BDesktopEnv(BaseComputerEnv):
    """Environment that uses E2B Desktop Sandbox for secure computer interactions"""

    def __init__(self, video_stream=False):
        super().__init__()
        self.desktop = Sandbox(video_stream=video_stream)
        self.action_space = {
            ComputerAction.CLICK.value: lambda x, y: self.desktop.mouse_move(x, y)
            and self.desktop.left_click(),
            ComputerAction.TYPE.value: lambda text: self.desktop.write(text),
            ComputerAction.PRESS.value: lambda key: self.desktop.pyautogui(
                f"pyautogui.press('{key}')"
            ),
            ComputerAction.HOTKEY.value: lambda *keys: self.desktop.hotkey(*keys),
        }

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

    def _get_observation(self):
        """Get the current observation (screenshot) of the environment"""
        screenshot = self.desktop.take_screenshot()
        # Save screenshot to temporary file and return path
        output_path = os.path.join(tempfile.gettempdir(), "e2b_screenshot.png")
        with open(output_path, "wb") as f:
            f.write(screenshot)
        return output_path
