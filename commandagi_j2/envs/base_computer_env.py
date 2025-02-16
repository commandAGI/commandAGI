import pyautogui
from commandagi_j2.utils.gym2.env_base import Env
from commandagi_j2.envs.computer_actions import ComputerAction


class BaseComputerEnv(Env):
    """Base class for computer environments with standard actions"""

    def __init__(self):
        self.action_space = {
            ComputerAction.CLICK.value: lambda x, y: pyautogui.click(x, y),
            ComputerAction.TYPE.value: lambda text: pyautogui.write(text),
            ComputerAction.PRESS.value: lambda key: pyautogui.press(key),
            ComputerAction.HOTKEY.value: lambda *keys: pyautogui.hotkey(*keys),
        }

    def _parse_action(self, action_str):
        """Parse action string into action type and parameters"""
        parts = action_str.split(maxsplit=1)
        action_type = parts[0]
        params = parts[1] if len(parts) > 1 else None
        return action_type, params

    def _execute_action(self, action):
        """Execute a given action using the standard action space"""
        try:
            action_type, params = self._parse_action(action)

            if action_type not in self.action_space:
                raise ValueError(f"Unknown action type: {action_type}")

            if action_type == ComputerAction.CLICK.value:
                x, y = map(int, params.split(","))
                self.action_space[action_type](x, y)
            elif action_type == ComputerAction.TYPE.value:
                self.action_space[action_type](params)
            elif action_type == ComputerAction.PRESS.value:
                self.action_space[action_type](params)
            elif action_type == ComputerAction.HOTKEY.value:
                keys = params.split(",")
                self.action_space[action_type](*keys)

            return True
        except Exception as e:
            print(f"Error executing action: {e}")
            return False
