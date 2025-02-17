from abc import abstractmethod
import time
from typing import List
from commandagi_j2.utils.gym2.env_base import Env
from commandagi_j2.envs.computer_types import (
    CommandAction,
    ClickAction,
    ComputerObservation,
    KeyboardKey,
    TypeAction,
    KeyboardKeysPressAction,
    KeyboardKeysDownAction,
    KeyboardKeysReleaseAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    DragAction,
    ComputerAction,  # if needed as a type alias/union
    MouseButton,  # Added for proper type annotations
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
)


class BaseComputerEnv(Env):
    """Base class for computer environments with standard actions"""

    def __init__(self):
        # Removed default action_space. Subclasses must implement action handlers via abstract methods.
        pass

    def _get_observation(self) -> ComputerObservation:
        """
        Get the current observation of the environment as a ComputerObservation containing:
            screenshot: Optional[ScreenshotObservation]
            mouse_state: Optional[MouseStateObservation] 
            keyboard_state: Optional[KeyboardStateObservation]
        """
        try:
            screenshot = self.get_screenshot()
        except Exception as e:
            print(f"Error getting screenshot: {e}")
            screenshot = None

        try:
            mouse_state = self.get_mouse_state()
        except Exception as e:
            print(f"Error getting mouse state: {e}")
            mouse_state = None

        try:
            keyboard_state = self.get_keyboard_state()
        except Exception as e:
            print(f"Error getting keyboard state: {e}")
            keyboard_state = None

        return ComputerObservation(
            screenshot=screenshot,
            mouse_state=mouse_state,
            keyboard_state=keyboard_state
        )

    def _execute_action(self, action: ComputerAction) -> bool:
        """Route the action to the appropriate handler implemented by subclasses."""
        success = False

        if action.command:
            try:
                success = self.execute_command(action.command.command, action.command.timeout)
            except Exception as e:
                print(f"Error executing command: {e}")
                success = False



        if action.keyboard_keys_press:
            try:
                success = self.execute_keyboard_keys_press(action.keyboard_keys_press.keys)
            except Exception as e:
                print(f"Error executing keyboard press: {e}")
                success = False

        if action.keyboard_keys_down:
            try:
                success = self.execute_keyboard_keys_down(action.keyboard_keys_down.keys)
            except Exception as e:
                print(f"Error executing keyboard down: {e}")
                success = False

        if action.keyboard_keys_release:
            try:
                success = self.execute_keyboard_keys_release(action.keyboard_keys_release.keys)
            except Exception as e:
                print(f"Error executing keyboard release: {e}")
                success = False

        if action.keyboard_hotkey:
            try:
                success = self.execute_keyboard_hotkey(action.keyboard_hotkey.keys)
            except Exception as e:
                print(f"Error executing keyboard hotkey: {e}")
                success = False

        if action.type:
            try:
                success = self.execute_type(action.type.text)
            except Exception as e:
                print(f"Error executing type: {e}")
                success = False
                
        if action.mouse_move:
            try:
                success = self.execute_mouse_move(
                    action.mouse_move.x,
                    action.mouse_move.y,
                    action.mouse_move.move_duration
                )
            except Exception as e:
                print(f"Error executing mouse move: {e}")
                success = False

        if action.mouse_scroll:
            try:
                success = self.execute_mouse_scroll(action.mouse_scroll.amount)
            except Exception as e:
                print(f"Error executing mouse scroll: {e}")
                success = False

        if action.mouse_button_down:
            try:
                success = self.execute_mouse_button_down(action.mouse_button_down.button)
            except Exception as e:
                print(f"Error executing mouse button down: {e}")
                success = False

        if action.mouse_button_up:
            try:
                success = self.execute_mouse_button_up(action.mouse_button_up.button)
            except Exception as e:
                print(f"Error executing mouse button up: {e}")
                success = False

        if action.click:
            try:
                success = self.execute_click(
                    action.click.x,
                    action.click.y, 
                    action.click.move_duration,
                    action.click.button
                )
            except Exception as e:
                print(f"Error executing click: {e}")
                success = False

        if action.drag:
            try:
                success = self.execute_drag(
                    action.drag.start_x,
                    action.drag.start_y,
                    action.drag.end_x,
                    action.drag.end_y,
                    action.drag.move_duration,
                    action.drag.button
                )
            except Exception as e:
                print(f"Error executing drag: {e}")
                success = False

        return success

    def render(self, mode="human"):
        if mode == "human":
            try:
                from commandagi_j2.envs.tk_render import TkRender
            except ImportError:
                raise ImportError(
                    "TkRender is required for human rendering but is not installed."
                )
            # Instantiate the TkRender with the current environment instance (self)
            self._tk_renderer = TkRender(self)
            self._tk_renderer.run()  # This will open the window and block as mainloop runs
        elif mode == "rgb_array":
            return self._get_observation()
        else:
            raise ValueError("Unsupported render mode: " + mode)

    @abstractmethod
    def get_screenshot(self) -> ScreenshotObservation:
        """Return a ScreenshotObservation of the current state (e.g. including a file path for the screenshot)."""
        pass

    @abstractmethod
    def get_mouse_state(self) -> MouseStateObservation:
        """Return a MouseStateObservation containing the current mouse button states and position."""
        pass

    @abstractmethod
    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return a KeyboardStateObservation with the current keyboard keys mapped to their states."""
        pass

    @abstractmethod
    def execute_command(self, command: str, timeout: float | None = None) -> bool:
        """Execute a system command in the environment and return True if successful.

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """
        pass

    def execute_keyboard_keys_press(self, keys: List[KeyboardKey]):
        """Execute pressing a keyboard key."""
        self.execute_keyboard_keys_down(keys)
        # time.sleep(duration)
        self.execute_keyboard_keys_release(keys)

    def execute_keyboard_key_press(self, key: KeyboardKey):
        """Execute pressing a keyboard key."""
        self.execute_keyboard_key_down(key)
        # time.sleep(duration)
        self.execute_keyboard_key_release(key)

    def execute_keyboard_keys_down(self, keys: List[KeyboardKey]):
        """Execute key down for each keyboard key."""
        for key in keys:
            self.execute_keyboard_key_down(key)

    def execute_keyboard_keys_release(self, keys: List[KeyboardKey]):
        """Execute key release for each keyboard key."""
        for key in keys:
            self.execute_keyboard_key_release(key)

    @abstractmethod
    def execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        pass

    @abstractmethod
    def execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        pass

    def execute_keyboard_hotkey(self, keys: List[KeyboardKey]) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        try:
            for key in keys:
                self.execute_keyboard_key_down(key)
            for key in reversed(keys):
                self.execute_keyboard_key_release(key)
            return True
        except Exception as e:
            print(f"Error executing keyboard hotkey: {e}")
            return False

    @abstractmethod
    def execute_type(self, text):
        """Execute typing the given text."""
        pass

    @abstractmethod
    def execute_mouse_move(self, x, y, move_duration: float = 0.5):
        """Execute moving the mouse to (x, y) over the move duration."""
        pass

    @abstractmethod
    def execute_mouse_scroll(self, amount: float):
        """Execute mouse scroll by a given amount."""
        pass

    @abstractmethod
    def execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button down action."""
        pass

    @abstractmethod
    def execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button up action."""
        pass

    def execute_click(self, x, y, move_duration: float = 0.5, button: MouseButton = MouseButton.LEFT):
        """Execute a click action at the given coordinates using press and release operations."""
        self.execute_mouse_move(x, y, move_duration)
        self.execute_mouse_button_down(button)
        self.execute_mouse_button_up(button)
        return True

    def execute_drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a drag action using the primitive mouse operations."""
        # Move to the starting position
        self.execute_mouse_move(start_x, start_y, move_duration)
        # Press the mouse button down
        self.execute_mouse_button_down(button)
        # Move to the ending position while holding down the mouse button
        self.execute_mouse_move(end_x, end_y, move_duration)
        # Release the mouse button
        self.execute_mouse_button_up(button)
        return True
