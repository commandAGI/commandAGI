from typing import ClassVar, Dict, Callable, Any, TypeVar, Generic, Optional

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.gym.environments.base_env import BaseEnv
from commandLAB.gym.environments.multimodal_env import MultiModalEnv
from commandLAB.types import ComputerAction, ComputerObservation
from rich.console import Console

console = Console()


class BaseComputerEnv(MultiModalEnv[ComputerObservation, ComputerAction]):
    """Base class for computer environments with standard actions"""

    computer: BaseComputer

    def __init__(self, computer: BaseComputer):
        self.computer = computer
        observation_fns = {
            "screenshot": self.computer.get_screenshot,
            "mouse_state": self.computer.get_mouse_state,
            "keyboard_state": self.computer.get_keyboard_state,
        }

        action_fns = {
            "command": lambda x: self.computer.execute_command(x.command, x.timeout),
            "keyboard_keys_press": lambda x: self.computer.execute_keyboard_keys_press(
                x.keys
            ),
            "keyboard_keys_down": lambda x: self.computer.execute_keyboard_keys_down(
                x.keys
            ),
            "keyboard_keys_release": lambda x: self.computer.execute_keyboard_keys_release(
                x.keys
            ),
            "keyboard_hotkey": lambda x: self.computer.execute_keyboard_hotkey(x.keys),
            "type": lambda x: self.computer.execute_type(x.text),
            "mouse_move": lambda x: self.computer.execute_mouse_move(
                x.x, x.y, x.move_duration
            ),
            "mouse_scroll": lambda x: self.computer.execute_mouse_scroll(x.amount),
            "mouse_button_down": lambda x: self.computer.execute_mouse_button_down(
                x.button
            ),
            "mouse_button_up": lambda x: self.computer.execute_mouse_button_up(
                x.button
            ),
            "click": lambda x: self.computer.execute_click(x),
            "double_click": lambda x: self.computer.execute_double_click(x),
            "drag": lambda x: self.computer.execute_drag(x),
        }

        super().__init__(
            observation_fns=observation_fns,
            action_fns=action_fns,
            observation_type=ComputerObservation,
        )

    def reset(self) -> ComputerObservation:
        return self.computer.reset()

    def close(self):
        self.computer.close()

    def get_reward(self, action: ComputerAction) -> float:
        return 0

    def get_done(self, action: ComputerAction) -> bool:
        return False

    def render(self, mode="human"):
        if mode == "human":
            try:
                from commandLAB.utils.viewer import EnvironmentViewer
            except ImportError:
                console.print(
                    "❌ [red]TkRender is required for human rendering but is not installed.[/]"
                )
                raise ImportError(
                    "TkRender is required for human rendering but is not installed."
                )
            # Instantiate the TkRender with the current environment instance (self)
            self._env_viewer = EnvironmentViewer(
                self
            )  # This will open the window and block as mainloop runs
        elif mode == "rgb_array":
            obs = self.computer.get_screenshot()
            if not obs or not obs.screenshot:
                return None

            import numpy as np
            import base64
            import io
            from PIL import Image

            # Decode base64 string to bytes
            img_bytes = base64.b64decode(obs.screenshot)

            # Convert bytes to PIL Image
            img = Image.open(io.BytesIO(img_bytes))

            # Convert PIL Image to numpy array
            return np.array(img)
        else:
            console.print(f"❌ [red]Unsupported render mode:[/] {mode}")
            raise ValueError("Unsupported render mode: " + mode)
