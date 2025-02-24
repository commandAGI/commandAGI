from typing import ClassVar, Dict, Callable, Any, TypeVar, Generic, Optional

from pydantic import BaseModel, Field

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.lxde_vnc_docker_computer import LXDEVNCDockerComputer
from commandLAB.gym.environments.base_env import BaseEnv
from commandLAB.gym.environments.multimodal_env import MultiModalEnv
from commandLAB.types import CommandAction, ComputerAction, ComputerObservation
from rich.console import Console


class ComputerEnvConfig(BaseModel):
    """Configuration for the computer environment."""

    computer_cls_name: str = LXDEVNCDockerComputer.__name__
    computer_cls_kwargs: dict = {}

    # NOTE: we might not be able to run this if the daemon is not running
    on_start_python: str = ""
    on_start_timeout: float = 10.0
    on_reset_python: str = ""
    on_reset_timeout: float = 10.0
    on_stop_python: str = ""
    on_stop_timeout: float = 10.0


class ComputerEnv(MultiModalEnv[ComputerObservation, ComputerAction]):
    """Base class for computer environments with standard actions"""

    name: str = "computer_env"
    config: ComputerEnvConfig

    _computer: BaseComputer
    _console: Console

    def __init__(self, config: ComputerEnvConfig, computer: BaseComputer = None):

        self.config = config

        if computer is None:
            computer_classes = BaseComputer.__subclasses__()
            computer_class = next(
                (
                    c
                    for c in computer_classes
                    if c.__name__ == self.config.computer_cls_name
                ),
                None,
            )
            if computer_class is None:
                raise ValueError(
                    f"Computer class {self.config.computer_cls_name} not found"
                )
            computer = computer_class(**self.config.computer_cls_kwargs)

        self._console = Console()
        self._computer = computer
        observation_fns = {
            "screenshot": self._computer.get_screenshot,
            "mouse_state": self._computer.get_mouse_state,
            "keyboard_state": self._computer.get_keyboard_state,
        }

        action_fns = {
            "command": lambda x: self._computer.execute_command(x.command, x.timeout),
            "keyboard_keys_press": lambda x: self._computer.execute_keyboard_keys_press(
                x.keys
            ),
            "keyboard_keys_down": lambda x: self._computer.execute_keyboard_keys_down(
                x.keys
            ),
            "keyboard_keys_release": lambda x: self._computer.execute_keyboard_keys_release(
                x.keys
            ),
            "keyboard_hotkey": lambda x: self._computer.execute_keyboard_hotkey(x.keys),
            "type": lambda x: self._computer.execute_type(x.text),
            "mouse_move": lambda x: self._computer.execute_mouse_move(
                x.x, x.y, x.move_duration
            ),
            "mouse_scroll": lambda x: self._computer.execute_mouse_scroll(x.amount),
            "mouse_button_down": lambda x: self._computer.execute_mouse_button_down(
                x.button
            ),
            "mouse_button_up": lambda x: self._computer.execute_mouse_button_up(
                x.button
            ),
            "click": lambda x: self._computer.execute_click(x),
            "double_click": lambda x: self._computer.execute_double_click(x),
            "drag": lambda x: self._computer.execute_drag(x),
        }

        super().__init__(
            observation_fns=observation_fns,
            action_fns=action_fns,
            observation_type=ComputerObservation,
        )

        if self.config.on_start_python:
            self._computer.execute_command(
                CommandAction(
                    command=self.config.on_start_python,
                    timeout=self.config.on_start_timeout,
                )
            )

    def reset(self) -> ComputerObservation:
        if self.config.on_reset_python:
            self._computer.execute_command(
                CommandAction(
                    command=self.config.on_reset_python,
                    timeout=self.config.on_reset_timeout,
                )
            )
        return self._computer.reset()

    def close(self):
        if self.config.on_stop_python:
            self._computer.execute_command(
                CommandAction(
                    command=self.config.on_stop_python,
                    timeout=self.config.on_stop_timeout,
                )
            )
        self._computer.close()

    def get_reward(self, action: ComputerAction) -> float:
        return 0

    def get_done(self, action: ComputerAction) -> bool:
        return False

    def render(self, mode="human"):
        if mode == "human":
            try:
                from commandLAB.utils.viewer import EnvironmentViewer
            except ImportError:
                self._console.print(
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
            obs = self._computer.get_screenshot()
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
            self._console.print(f"❌ [red]Unsupported render mode:[/] {mode}")
            raise ValueError("Unsupported render mode: " + mode)
