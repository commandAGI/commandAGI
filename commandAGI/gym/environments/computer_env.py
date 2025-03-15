from typing import Any, Callable, ClassVar, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field
from rich.console import Console

from commandAGI.computers.base_computer import BaseComputer
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.gym.environments.base_env import BaseEnv
from commandAGI.gym.environments.multimodal_env import MultiModalEnv
from commandAGI.types import ComputerAction, ComputerObservation, ShellCommandAction


class ComputerEnvConfig(BaseModel):
    """Configuration for the computer environment."""

    computer_cls_name: str = LocalPynputComputer.__name__
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
            "command": lambda x: self._computer.shell(x),
            "keyboard_keys_press": lambda x: self._computer.execute_keyboard_keys_press(
                x
            ),
            "keyboard_keys_down": lambda x: self._computer.execute_keyboard_keys_down(
                x
            ),
            "keyboard_keys_release": lambda x: self._computer.execute_keyboard_keys_release(
                x
            ),
            "keyboard_hotkey": lambda x: self._computer.hotkey(x),
            "type": lambda x: self._computer.type(x),
            "mouse_move": lambda x: self._computer.move(x),
            "mouse_scroll": lambda x: self._computer.scroll(x),
            "mouse_down": lambda x: self._computer.mouse_down(x),
            "mouse_button_up": lambda x: self._computer.mouse_up(x),
            "click": lambda x: self._computer.click(x),
            "double_click": lambda x: self._computer.double_click(x),
            "drag": lambda x: self._computer.drag(x),
        }

        super().__init__(
            observation_fns=observation_fns,
            action_fns=action_fns,
            observation_type=ComputerObservation,
        )

        if self.config.on_start_python:
            self._computer.shell(
                ShellCommandAction(
                    command=self.config.on_start_python,
                    timeout=self.config.on_start_timeout,
                )
            )

    def reset(self) -> ComputerObservation:
        if self.config.on_reset_python:
            self._computer.shell(
                ShellCommandAction(
                    command=self.config.on_reset_python,
                    timeout=self.config.on_reset_timeout,
                )
            )
        return self._computer.reset_state()

    def close(self):
        if self.config.on_stop_python:
            self._computer.shell(
                ShellCommandAction(
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
                from commandAGI.utils.viewer import EnvironmentViewer
            except ImportError:
                self._console.print(
                    "❌ [red]TkRender is required for human rendering but is not installed.[/]"
                )
                raise ImportError(
                    "TkRender is required for human rendering but is not installed."
                )
            # Instantiate the TkRender with the current environment instance
            # (self)
            self._env_viewer = EnvironmentViewer(
                self
            )  # This will open the window and block as mainloop runs
        elif mode == "rgb_array":
            obs = self._computer.get_screenshot()
            if not obs or not obs.screenshot:
                return None

            import base64
            import io

            import numpy as np
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
