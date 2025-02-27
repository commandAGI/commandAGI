from typing import Dict, Any, Tuple, Optional
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from PIL import Image
import base64
import io

from commandLAB.gym.environments.computer_env import ComputerEnv
from commandLAB.types import (
    ComputerAction,
    ComputerObservation,
    MouseButton,
    KeyboardKey,
    ComputerActionType,
    ShellCommandAction,
    KeyboardKeyPressAction,
    KeyboardKeysPressAction,
    KeyboardKeyDownAction,
    KeyboardKeysDownAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysReleaseAction,
    KeyboardHotkeyAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    ClickAction,
    DoubleClickAction,
    DragAction,
)


class OpenRLComputerEnv(gym.Env):
    """Wrapper that converts BaseComputerEnv to OpenRL Gym environment"""

    def __init__(self, env: ComputerEnv):
        super().__init__()
        self.env = env

        # Define observation space
        self.observation_space = spaces.Dict(
            {
                "screenshot": spaces.Box(
                    low=0, high=255, shape=(None, None, 3), dtype=np.uint8
                ),
                "mouse_state": spaces.Dict(
                    {
                        "buttons": spaces.Dict(
                            {btn.value: spaces.Discrete(2) for btn in MouseButton}
                        ),
                        "position": spaces.Box(
                            low=0, high=float("inf"), shape=(2,), dtype=np.int32
                        ),
                    }
                ),
                "keyboard_state": spaces.Dict(
                    {
                        "keys": spaces.Dict(
                            {key.value: spaces.Discrete(2) for key in KeyboardKey}
                        )
                    }
                ),
            }
        )

        # Define action space
        self.action_space = spaces.Dict(
            {
                "action_type": spaces.Discrete(len(ComputerActionType)),
                "params": spaces.Dict(
                    {
                        # Command action
                        "command": spaces.Text(min_length=0, max_length=1000),
                        "timeout": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.float32
                        ),
                        # Keyboard actions
                        "keys": spaces.Sequence(
                            spaces.Text(min_length=1, max_length=20)
                        ),
                        "key": spaces.Text(min_length=1, max_length=20),
                        "duration": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.float32
                        ),
                        "text": spaces.Text(min_length=0, max_length=1000),
                        # Mouse actions
                        "x": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.int32
                        ),
                        "y": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.int32
                        ),
                        "move_duration": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.float32
                        ),
                        "amount": spaces.Box(
                            low=-float("inf"),
                            high=float("inf"),
                            shape=(),
                            dtype=np.float32,
                        ),
                        "button": spaces.Discrete(len(MouseButton)),
                        "press_duration": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.float32
                        ),
                        "start_x": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.int32
                        ),
                        "start_y": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.int32
                        ),
                        "end_x": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.int32
                        ),
                        "end_y": spaces.Box(
                            low=0, high=float("inf"), shape=(), dtype=np.int32
                        ),
                    }
                ),
            }
        )

    def _process_observation(self, obs: ComputerObservation) -> Dict[str, Any]:
        """Convert ComputerObservation to gym observation format"""
        processed_obs = {}

        # Process screenshot
        if obs.get("screenshot"):
            img_bytes = base64.b64decode(obs["screenshot"].screenshot)
            img = Image.open(io.BytesIO(img_bytes))
            processed_obs["screenshot"] = np.array(img)

        # Process mouse state
        if obs.get("mouse_state"):
            processed_obs["mouse_state"] = {
                "buttons": obs["mouse_state"].buttons,
                "position": obs["mouse_state"].position,
            }

        # Process keyboard state
        if obs.get("keyboard_state"):
            processed_obs["keyboard_state"] = {"keys": obs["keyboard_state"].keys}

        return processed_obs

    def _create_action(self, action: Dict[str, Any]) -> ComputerAction:
        """Convert gym action format to ComputerAction"""
        action_type = ComputerActionType(
            list(ComputerActionType)[action["action_type"]]
        )
        params = action["params"]

        # Create appropriate action based on action_type
        computer_action = ComputerAction()

        if action_type == ComputerActionType.COMMAND:
            computer_action["command"] = ShellCommandAction(
                command=params["command"], timeout=params["timeout"]
            )

        elif action_type == ComputerActionType.KEYBOARD_KEY_PRESS:
            computer_action["keyboard_key_press"] = KeyboardKeyPressAction(
                key=params["key"], duration=params.get("duration", 0.1)
            )

        elif action_type == ComputerActionType.KEYBOARD_KEYS_PRESS:
            computer_action["keyboard_keys_press"] = KeyboardKeysPressAction(
                keys=params["keys"], duration=params.get("duration", 0.1)
            )

        elif action_type == ComputerActionType.KEYBOARD_KEY_DOWN:
            computer_action["keyboard_key_down"] = KeyboardKeyDownAction(
                key=params["key"]
            )

        elif action_type == ComputerActionType.KEYBOARD_KEYS_DOWN:
            computer_action["keyboard_keys_down"] = KeyboardKeysDownAction(
                keys=params["keys"]
            )

        elif action_type == ComputerActionType.KEYBOARD_KEY_RELEASE:
            computer_action["keyboard_key_release"] = KeyboardKeyReleaseAction(
                key=params["key"]
            )

        elif action_type == ComputerActionType.KEYBOARD_KEYS_RELEASE:
            computer_action["keyboard_keys_release"] = KeyboardKeysReleaseAction(
                keys=params["keys"]
            )

        elif action_type == ComputerActionType.KEYBOARD_HOTKEY:
            computer_action["keyboard_hotkey"] = KeyboardHotkeyAction(
                keys=params["keys"]
            )

        elif action_type == ComputerActionType.TYPE:
            computer_action["type"] = TypeAction(text=params["text"])

        elif action_type == ComputerActionType.MOUSE_MOVE:
            computer_action["mouse_move"] = MouseMoveAction(
                x=params["x"],
                y=params["y"],
                move_duration=params.get("move_duration", 0.5),
            )

        elif action_type == ComputerActionType.MOUSE_SCROLL:
            computer_action["mouse_scroll"] = MouseScrollAction(amount=params["amount"])

        elif action_type == ComputerActionType.MOUSE_BUTTON_DOWN:
            computer_action["mouse_button_down"] = MouseButtonDownAction(
                button=params.get("button", MouseButton.LEFT)
            )

        elif action_type == ComputerActionType.MOUSE_BUTTON_UP:
            computer_action["mouse_button_up"] = MouseButtonUpAction(
                button=params.get("button", MouseButton.LEFT)
            )

        elif action_type == ComputerActionType.CLICK:
            computer_action["click"] = ClickAction(
                x=params["x"],
                y=params["y"],
                move_duration=params.get("move_duration", 0.5),
                press_duration=params.get("press_duration", 0.1),
                button=params.get("button", MouseButton.LEFT),
            )

        elif action_type == ComputerActionType.DOUBLE_CLICK:
            computer_action["double_click"] = DoubleClickAction(
                x=params["x"],
                y=params["y"],
                move_duration=params.get("move_duration", 0.5),
                press_duration=params.get("press_duration", 0.1),
                button=params.get("button", MouseButton.LEFT),
                double_click_interval_seconds=params.get(
                    "double_click_interval_seconds", 0.1
                ),
            )

        elif action_type == ComputerActionType.DRAG:
            computer_action["drag"] = DragAction(
                start_x=params["start_x"],
                start_y=params["start_y"],
                end_x=params["end_x"],
                end_y=params["end_y"],
                move_duration=params.get("move_duration", 0.5),
                button=params.get("button", MouseButton.LEFT),
            )

        return computer_action

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        super().reset(seed=seed)
        obs = self.env.reset()
        return self._process_observation(obs), {}

    def step(
        self, action: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], float, bool, bool, Dict[str, Any]]:
        computer_action = self._create_action(action)
        obs = self.env.step(computer_action)
        reward = self.env.get_reward(computer_action)
        terminated = self.env.get_done(computer_action)
        truncated = False
        info = {}

        return self._process_observation(obs), reward, terminated, truncated, info

    def render(self, mode="human"):
        return self.env.render(mode)

    def close(self):
        self.env.close()
