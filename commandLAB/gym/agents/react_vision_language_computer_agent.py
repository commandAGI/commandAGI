from collections.abc import Callable
import inspect
import re
from textwrap import dedent
from typing import List, Optional

from transformers import Agent

from commandLAB.agents.base_agent import BaseComputerAgent
from commandLAB.gym.schema import Episode
from commandLAB.types import ClickAction, CommandAction, ComputerAction, ComputerObservation, DoubleClickAction, DragAction, KeyboardHotkeyAction, KeyboardKey, KeyboardKeyDownAction, KeyboardKeyPressAction, KeyboardKeyReleaseAction, KeyboardKeysDownAction, KeyboardKeysPressAction, KeyboardKeysReleaseAction, MouseButton, MouseButtonDownAction, MouseButtonUpAction, MouseMoveAction, MouseScrollAction, TypeAction
from commandLAB.agents._utils.llms import get_chat_model
from langchain.schema import ChatMessage
from langchain_core.output_parsers.string import StrOutputParser
from rich.console import Console
from rich.panel import Panel
from commandLAB.utils.image import imageToB64

console = Console()


class ReactComputerAgent(BaseComputerAgent[ComputerObservation, ComputerAction]):

    def __init__(self, model: str, device: Optional[str] = None):
        """Initialize the React agent with a Hugging Face model.
        
        Args:
            model: Name of the Hugging Face model to use
            device: Device to run the model on (e.g., 'cuda', 'cpu')
        """
        self.total_reward = 0.0
        self.agent = Agent(model, device=device)
        
        # Register all our actions as tools
        for action_fn in self.action_fns:
            self.agent.register_tool(
                name=action_fn.__name__,
                description=action_fn.__doc__ or f"Execute {action_fn.__name__} action",
                fn=action_fn
            )

    @property
    def action_fns(self) -> list[Callable]:
        """List of action functions that can be called to create ComputerAction objects."""
        
        def command(command: str, timeout: float | None = None):
            return ComputerAction(command=CommandAction(command=command, timeout=timeout))

        def keyboard_keys_press(keys: List[KeyboardKey], duration: float = 0.1):
            return ComputerAction(keyboard_keys_press=KeyboardKeysPressAction(keys=keys, duration=duration))

        def keyboard_key_press(key: KeyboardKey, duration: float = 0.1):
            return ComputerAction(keyboard_key_press=KeyboardKeyPressAction(key=key, duration=duration))

        def keyboard_keys_down(keys: List[KeyboardKey]):
            return ComputerAction(keyboard_keys_down=KeyboardKeysDownAction(keys=keys))

        def keyboard_key_down(key: KeyboardKey):
            return ComputerAction(keyboard_key_down=KeyboardKeyDownAction(key=key))

        def keyboard_keys_release(keys: List[KeyboardKey]):
            return ComputerAction(keyboard_keys_release=KeyboardKeysReleaseAction(keys=keys))

        def keyboard_key_release(key: KeyboardKey):
            return ComputerAction(keyboard_key_release=KeyboardKeyReleaseAction(key=key))

        def keyboard_hotkey(keys: List[KeyboardKey]):
            return ComputerAction(keyboard_hotkey=KeyboardHotkeyAction(keys=keys))

        def type(text: str):
            return ComputerAction(type=TypeAction(text=text))

        def mouse_move(x: int, y: int, move_duration: float = 0.5):
            return ComputerAction(mouse_move=MouseMoveAction(x=x, y=y, move_duration=move_duration))

        def mouse_scroll(amount: float):
            return ComputerAction(mouse_scroll=MouseScrollAction(amount=amount))

        def mouse_button_down(button: MouseButton = MouseButton.LEFT):
            return ComputerAction(mouse_button_down=MouseButtonDownAction(button=button))

        def mouse_button_up(button: MouseButton = MouseButton.LEFT):
            return ComputerAction(mouse_button_up=MouseButtonUpAction(button=button))

        def click(x: int, y: int, move_duration: float = 0.5, press_duration: float = 0.1, button: MouseButton = MouseButton.LEFT):
            return ComputerAction(click=ClickAction(x=x, y=y, move_duration=move_duration, press_duration=press_duration, button=button))

        def double_click(x: int, y: int, move_duration: float = 0.5, press_duration: float = 0.1, button: MouseButton = MouseButton.LEFT, double_click_interval_seconds: float = 0.1):
            return ComputerAction(double_click=DoubleClickAction(x=x, y=y, move_duration=move_duration, press_duration=press_duration, button=button, double_click_interval_seconds=double_click_interval_seconds))

        def drag(start_x: int, start_y: int, end_x: int, end_y: int, move_duration: float = 0.5, button: MouseButton = MouseButton.LEFT):
            return ComputerAction(drag=DragAction(start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, move_duration=move_duration, button=button))

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
            drag
        ]

    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0
        # Reset agent conversation history if needed
        self.agent.reset()

    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Analyze screenshot and decide on next action using React agent."""
        if not observation.screenshot.screenshot:
            return None

        # Convert image to base64 for the prompt
        image_b64 = imageToB64(observation.screenshot.screenshot)
        
        # Create the prompt for the React agent
        prompt = dedent("""
            Look at this screenshot and suggest a single action to take.
            You have access to various computer control actions through registered tools.
            Analyze the image and choose the most appropriate action.
        """).strip()

        # Run the React agent with the image
        response = self.agent.run(
            prompt,
            image=f"data:image/png;base64,{image_b64}"
        )
        
        console.print(Panel(f"🤖 [cyan]Agent response:[/] {response}"))
        
        # The agent.run() should return the executed action directly
        # since we registered our action functions as tools
        return response

    def update(self, reward: float):
        """Update agent with reward feedback"""
        self.total_reward += reward

    def train(self, episodes: list[Episode]) -> None:
        """Train the agent on a list of episodes."""
        # React agents typically don't support direct training
        pass

