from collections.abc import Callable
import inspect
import re
from textwrap import dedent
from typing import List, Optional

from pydantic import Field

from commandLAB.gym.agents.base_agent import BaseAgent
from commandLAB.gym.schema import Episode
from commandLAB.types import (
    ClickAction,
    ShellCommandAction,
    ComputerAction,
    ComputerObservation,
    DoubleClickAction,
    DragAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysDownAction,
    KeyboardKeysPressAction,
    KeyboardKeysReleaseAction,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    TypeAction,
)
from commandLAB.gym._utils.llms import get_chat_model
from langchain.schema import ChatMessage
from langchain_core.output_parsers.string import StrOutputParser
from rich.console import Console
from rich.panel import Panel
from commandLAB.utils.image import imageToB64

console = Console()


class NaiveComputerAgent(BaseAgent[ComputerObservation, ComputerAction]):
    total_reward: float = Field(default=0.0)
    chat_model_options: dict
    chat_model: Optional[object] = None
    str_output_parser: Optional[object] = None

    def __init__(self, chat_model_options: dict):
        super().__init__(chat_model_options=chat_model_options)
        self.chat_model = get_chat_model(**self.chat_model_options)
        self.str_output_parser = StrOutputParser()

    @property
    def action_fns(self) -> list[Callable]:
        """List of action functions that can be called to create ComputerAction objects."""

        def command(command: str, timeout: float | None = None):
            return ComputerAction(
                command=ShellCommandAction(command=command, timeout=timeout)
            )

        def keyboard_keys_press(keys: List[KeyboardKey], duration: float = 0.1):
            return ComputerAction(
                keyboard_keys_press=KeyboardKeysPressAction(
                    keys=keys, duration=duration
                )
            )

        def keyboard_key_press(key: KeyboardKey, duration: float = 0.1):
            return ComputerAction(
                keyboard_key_press=KeyboardKeyPressAction(key=key, duration=duration)
            )

        def keyboard_keys_down(keys: List[KeyboardKey]):
            return ComputerAction(keyboard_keys_down=KeyboardKeysDownAction(keys=keys))

        def keyboard_key_down(key: KeyboardKey):
            return ComputerAction(keyboard_key_down=KeyboardKeyDownAction(key=key))

        def keyboard_keys_release(keys: List[KeyboardKey]):
            return ComputerAction(
                keyboard_keys_release=KeyboardKeysReleaseAction(keys=keys)
            )

        def keyboard_key_release(key: KeyboardKey):
            return ComputerAction(
                keyboard_key_release=KeyboardKeyReleaseAction(key=key)
            )

        def keyboard_hotkey(keys: List[KeyboardKey]):
            return ComputerAction(keyboard_hotkey=KeyboardHotkeyAction(keys=keys))

        def type(text: str):
            return ComputerAction(type=TypeAction(text=text))

        def mouse_move(x: int, y: int, move_duration: float = 0.5):
            return ComputerAction(
                mouse_move=MouseMoveAction(x=x, y=y, move_duration=move_duration)
            )

        def mouse_scroll(amount: float):
            return ComputerAction(mouse_scroll=MouseScrollAction(amount=amount))

        def mouse_button_down(button: MouseButton = MouseButton.LEFT):
            return ComputerAction(
                mouse_button_down=MouseButtonDownAction(button=button)
            )

        def mouse_button_up(button: MouseButton = MouseButton.LEFT):
            return ComputerAction(mouse_button_up=MouseButtonUpAction(button=button))

        def click(
            x: int,
            y: int,
            move_duration: float = 0.5,
            press_duration: float = 0.1,
            button: MouseButton = MouseButton.LEFT,
        ):
            return ComputerAction(
                click=ClickAction(
                    x=x,
                    y=y,
                    move_duration=move_duration,
                    press_duration=press_duration,
                    button=button,
                )
            )

        def double_click(
            x: int,
            y: int,
            move_duration: float = 0.5,
            press_duration: float = 0.1,
            button: MouseButton = MouseButton.LEFT,
            double_click_interval_seconds: float = 0.1,
        ):
            return ComputerAction(
                double_click=DoubleClickAction(
                    x=x,
                    y=y,
                    move_duration=move_duration,
                    press_duration=press_duration,
                    button=button,
                    double_click_interval_seconds=double_click_interval_seconds,
                )
            )

        def drag(
            start_x: int,
            start_y: int,
            end_x: int,
            end_y: int,
            move_duration: float = 0.5,
            button: MouseButton = MouseButton.LEFT,
        ):
            return ComputerAction(
                drag=DragAction(
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    move_duration=move_duration,
                    button=button,
                )
            )

        return [
            command,
            keyboard_keys_press,
            keyboard_key_press,
            keyboard_keys_down,
            keyboard_key_down,
            keyboard_keys_release,
            keyboard_key_release,
            keyboard_hotkey,
            type,
            mouse_move,
            mouse_scroll,
            mouse_button_down,
            mouse_button_up,
            click,
            double_click,
            drag,
        ]

    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0

    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Analyze screenshot and decide on next action using LangChain chat model."""
        # Convert image to base64
        if not observation.screenshot.screenshot:
            return None

        input_messages = [
            ChatMessage(
                role="user",
                content=[
                    {
                        "type": "text",
                        "text": dedent(
                            """\
                            Look at this screenshot and suggest a single action to take.
                            Respond with a function call to the action you want to take.

                            Action space:
                            """
                            + "\n".join(
                                [
                                    f"- {fn.__name__}({', '.join(inspect.signature(fn).parameters)})"
                                    for fn in self.action_fns
                                ]
                            )
                        ).strip(),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{imageToB64(observation.screenshot.screenshot)}"
                        },
                    },
                    {
                        "type": "text",
                        "text": dedent(
                            """\
                            Now, please respond with a function call to the action you want to take.
                            """
                        ).strip(),
                    },
                ],
            ),
        ]

        response = self.chat_model.invoke(input_messages)
        response_str = self.str_output_parser.invoke(response.content.strip())
        console.print(Panel(f"🤖 [cyan]Agent response:[/] {response_str}"))
        # Parse response string into action
        action = ComputerAction(
            command=None,
            keyboard_keys_press=None,
            keyboard_keys_down=None,
            keyboard_keys_release=None,
            keyboard_key_press=None,
            keyboard_key_down=None,
            keyboard_key_release=None,
            keyboard_hotkey=None,
            type=None,
            mouse_move=None,
            mouse_scroll=None,
            mouse_button_down=None,
            mouse_button_up=None,
            click=None,
            double_click=None,
            drag=None,
        )
        # naive agent implementation, poor parsing, dangerous eval
        match = re.match(r"(\w+)\((.*)\)", response_str)
        if match:
            fn_name, fn_args = match.groups()
        else:
            raise ValueError(f"Invalid action format: {response_str}")
        action_fn = next((fn for fn in self.action_fns if fn.__name__ == fn_name), None)
        if action_fn:
            action = action_fn(*eval(fn_args))
        return action

    def update(self, reward: float):
        """Update agent with reward feedback"""
        self.total_reward += reward

    def train(self, episodes: list[Episode]) -> None:
        """Train the agent on a list of episodes."""
        pass
