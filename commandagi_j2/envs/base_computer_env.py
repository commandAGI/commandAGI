from abc import abstractmethod
import time
from typing import ClassVar
from rich.console import Console
from commandagi_j2.utils.gym2.base_env import Env
from commandagi_j2.envs.computer_types import (
    CommandAction,
    ClickAction,
    ComputerObservation,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    KeyboardKeysPressAction,
    KeyboardKeysDownAction,
    KeyboardKeysReleaseAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    DragAction,
    ComputerAction,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
)
from commandagi_j2.utils.gym2.spaces import Space, StructuredSpace

console = Console()


class BaseComputerEnv(Env[ComputerObservation, ComputerAction]):
    """Base class for computer environments with standard actions"""

    _LOG_MODALITY_ERRORS: ClassVar[bool] = False

    observation_space: Space = StructuredSpace(model=ComputerObservation)
    action_space: Space = StructuredSpace(model=ComputerAction)

    def get_observation(self) -> ComputerObservation:
        """
        Get the current observation of the environment as a ComputerObservation containing:
            screenshot: Optional[ScreenshotObservation]
            mouse_state: Optional[MouseStateObservation]
            keyboard_state: Optional[KeyboardStateObservation]
        """
        try:
            screenshot = self.get_screenshot()
        except Exception as e:
            if self._LOG_MODALITY_ERRORS:
                console.print(f"🖼️ [red]Error getting screenshot:[/] {e}")
            screenshot = None

        try:
            mouse_state = self.get_mouse_state()
        except Exception as e:
            if self._LOG_MODALITY_ERRORS:
                console.print(f"🖱️ [red]Error getting mouse state:[/] {e}")
            mouse_state = None

        try:
            keyboard_state = self.get_keyboard_state()
        except Exception as e:
            if self._LOG_MODALITY_ERRORS:
                console.print(f"⌨️ [red]Error getting keyboard state:[/] {e}")
            keyboard_state = None

        return ComputerObservation(
            screenshot=screenshot,
            mouse_state=mouse_state,
            keyboard_state=keyboard_state,
        )

    def execute_action(self, action: ComputerAction) -> bool:
        """Route the action to the appropriate handler implemented by subclasses."""
        success = True

        if action.command:
            try:
                success = self.execute_command(
                    action.command.command, action.command.timeout
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"💻 [red]Error executing command:[/] {e}")
                success = False

        if action.keyboard_keys_press:
            try:
                success = self.execute_keyboard_keys_press(
                    action.keyboard_keys_press.keys
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard press:[/] {e}")
                success = False

        if action.keyboard_keys_down:
            try:
                success = self.execute_keyboard_keys_down(
                    action.keyboard_keys_down.keys
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard down:[/] {e}")
                success = False

        if action.keyboard_keys_release:
            try:
                success = self.execute_keyboard_keys_release(
                    action.keyboard_keys_release.keys
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard release:[/] {e}")
                success = False

        if action.keyboard_hotkey:
            try:
                success = self.execute_keyboard_hotkey(action.keyboard_hotkey.keys)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard hotkey:[/] {e}")
                success = False

        if action.type:
            try:
                success = self.execute_type(action.type.text)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing type:[/] {e}")
                success = False

        if action.mouse_move:
            try:
                success = self.execute_mouse_move(
                    action.mouse_move.x,
                    action.mouse_move.y,
                    action.mouse_move.move_duration,
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse move:[/] {e}")
                success = False

        if action.mouse_scroll:
            try:
                success = self.execute_mouse_scroll(action.mouse_scroll.amount)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse scroll:[/] {e}")
                success = False

        if action.mouse_button_down:
            try:
                success = self.execute_mouse_button_down(
                    action.mouse_button_down.button
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse button down:[/] {e}")
                success = False

        if action.mouse_button_up:
            try:
                success = self.execute_mouse_button_up(action.mouse_button_up.button)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse button up:[/] {e}")
                success = False

        if action.click:
            try:
                success = self.execute_click(action.click)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing click:[/] {e}")
                success = False

        if action.drag:
            try:
                success = self.execute_drag(
                    action.drag.start_x,
                    action.drag.start_y,
                    action.drag.end_x,
                    action.drag.end_y,
                    action.drag.move_duration,
                    action.drag.button,
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing drag:[/] {e}")
                success = False

        return success

    def get_reward(self, action: ComputerAction) -> float:
        return 0

    def get_done(self, action: ComputerAction) -> bool:
        return False

    def render(self, mode="human"):
        if mode == "human":
            try:
                from commandagi_j2.utils.env_viewer import EnvironmentViewer
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
            return self.get_observation()
        else:
            console.print(f"❌ [red]Unsupported render mode:[/] {mode}")
            raise ValueError("Unsupported render mode: " + mode)

    @abstractmethod
    def get_screenshot(self) -> ScreenshotObservation:
        """Return a ScreenshotObservation containing the screenshot encoded as a base64 string."""

    @abstractmethod
    def get_mouse_state(self) -> MouseStateObservation:
        """Return a MouseStateObservation containing the current mouse button states and position."""

    @abstractmethod
    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return a KeyboardStateObservation with the current keyboard keys mapped to their states."""

    @abstractmethod
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the environment and return True if successful.

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """

    def execute_keyboard_keys_press(self, action: KeyboardKeysPressAction):
        """Execute pressing keyboard keys."""
        self.execute_keyboard_keys_down(action.keys)
        self.execute_keyboard_keys_release(action.keys)

    def execute_keyboard_keys_down(self, action: KeyboardKeysDownAction):
        """Execute key down for each keyboard key."""
        for key in action.keys:
            self.execute_keyboard_key_down(key)

    def execute_keyboard_keys_release(self, action: KeyboardKeysReleaseAction):
        """Execute key release for each keyboard key."""
        success = True
        for key in action.keys:
            success_i = self.execute_keyboard_key_release(key)
            if not success_i:
                success = False
        return success

    def execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key with a specified duration."""
        self.execute_keyboard_key_down(KeyboardKeyDownAction(key=action.key))
        time.sleep(action.duration)
        self.execute_keyboard_key_release(KeyboardKeyReleaseAction(key=action.key))
        return True

    @abstractmethod
    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        """Execute key down for a keyboard key."""

    @abstractmethod
    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        """Execute key release for a keyboard key."""

    def execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        success = True
        for key in action.keys:
            success_i = self.execute_keyboard_key_down(key)
            if not success_i:
                success = False
        for key in reversed(action.keys):
            success_i = self.execute_keyboard_key_release(key)
            if not success_i:
                success = False
        return success

    def execute_type(self, action: TypeAction):
        """Execute typing the given text."""
        for char in action.text:
            self.execute_keyboard_key_press(KeyboardKeyPressAction(key=char))
        return True

    @abstractmethod
    def execute_mouse_move(self, action: MouseMoveAction):
        """Execute moving the mouse to (x, y) over the move duration."""

    @abstractmethod
    def execute_mouse_scroll(self, action: MouseScrollAction):
        """Execute mouse scroll by a given amount."""

    @abstractmethod
    def execute_mouse_button_down(self, action: MouseButtonDownAction):
        """Execute mouse button down action."""

    @abstractmethod
    def execute_mouse_button_up(self, action: MouseButtonUpAction):
        """Execute mouse button up action."""

    def execute_click(self, action: ClickAction) -> bool:
        """Execute a click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        move_action = MouseMoveAction(
            x=action.x, y=action.y, move_duration=action.move_duration
        )
        self.execute_mouse_move(move_action)
        down_action = MouseButtonDownAction(button=action.button)
        self.execute_mouse_button_down(down_action)
        time.sleep(action.press_duration)
        up_action = MouseButtonUpAction(button=action.button)
        self.execute_mouse_button_up(up_action)
        return True

    def execute_drag(self, action: DragAction):
        """Execute a drag action using the primitive mouse operations."""
        # Move to the starting position
        self.execute_mouse_move(
            x=action.start_x, y=action.start_y, move_duration=action.move_duration
        )
        # Press the mouse button down
        self.execute_mouse_button_down(button=action.button)
        # Move to the ending position while holding down the mouse button
        self.execute_mouse_move(
            x=action.end_x, y=action.end_y, move_duration=action.move_duration
        )
        # Release the mouse button
        self.execute_mouse_button_up(button=action.button)
        return True
