import time
import mss
import io
from PIL import Image
import pyautogui
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
import tempfile
import os
from enum import Enum
from e2b_desktop import Sandbox


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

    def _get_observation(self):
        """Get the current observation of the environment"""
        return self._take_screenshot()

    def _take_screenshot(self):
        """Take a screenshot and return the path"""
        # Use a temporary file with a fixed path
        output_path = os.path.join(self.temp_dir, "screenshot.png")
        screenshot = self.sct.grab(self.sct.monitors[1])  # Primary monitor
        Image.frombytes("RGB", screenshot.size, screenshot.rgb).save(output_path)
        self.last_screenshot = output_path
        return self.last_screenshot
