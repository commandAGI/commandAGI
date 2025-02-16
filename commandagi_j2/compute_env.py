import mss
import io
from PIL import Image
import pyautogui
from commandagi_j2.utils.gym2.env_base import Env
import tempfile
import os

class ComputeEnv(Env):
    def __init__(self):
        self.sct = mss.mss()
        self.last_screenshot = None
        self.temp_dir = tempfile.mkdtemp()
    
    def reset(self):
        """Reset environment and return initial observation"""
        return self._take_screenshot()
    
    def step(self, action):
        """Execute action and return (observation, reward, done, info)"""
        success = self._execute_action(action)
        observation = self._take_screenshot()
        
        # Simple reward structure
        reward = 1.0 if success else -1.0
        done = False  # In this case, episodes don't naturally terminate
        info = {"action_success": success}
        
        return observation, reward, done, info
    
    def close(self):
        """Clean up resources"""
        self.sct.close()
    
    def _take_screenshot(self):
        """Take a screenshot and return the path"""
        # Use a temporary file with a fixed path
        output_path = os.path.join(self.temp_dir, "screenshot.png")
        screenshot = self.sct.grab(self.sct.monitors[1])  # Primary monitor
        Image.frombytes('RGB', screenshot.size, screenshot.rgb).save(output_path)
        self.last_screenshot = output_path
        return self.last_screenshot
    
    def _execute_action(self, action):
        """Execute a given action on the computer"""
        try:
            if action.startswith('click'):
                x, y = map(int, action.split()[1].split(','))
                pyautogui.click(x, y)
            elif action.startswith('type'):
                text = action[5:].strip()
                pyautogui.write(text)
            return True
        except Exception as e:
            print(f"Error executing action: {e}")
            return False 