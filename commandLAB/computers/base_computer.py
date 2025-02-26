import time
from abc import abstractmethod
from typing import Literal, List, Optional

from commandLAB.types import (
    ClickAction,
    CommandAction,
    DoubleClickAction,
    DragAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysDownAction,
    KeyboardKeysPressAction,
    KeyboardKeysReleaseAction,
    KeyboardStateObservation,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
    TypeAction,
    LayoutTreeObservation,
    ProcessesObservation,
    WindowsObservation,
    DisplaysObservation,
    RunProcessAction,
    KeyboardKey,
    MouseButton,
)
from pydantic import BaseModel


class BaseComputer(BaseModel):

    _state: Literal["stopped", "started"] = "stopped"

    def start(self):
        """Start the computer."""
        if self._state != "stopped":
            raise ValueError("Computer is already started")
        self._start()
        self._state = "started"

    def _start(self):
        """Start the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.start")

    def stop(self):
        """Stop the computer."""
        if self._state != "started":
            raise ValueError("Computer is already stopped")
        self._stop()
        self._state = "stopped"

    def _stop(self):
        """Stop the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.stop")

    def reset_state(self):
        """Reset the computer state."""
        self.stop()
        self.start()

    def get_screenshot(self, display_id: int = 0) -> ScreenshotObservation:
        """Return a ScreenshotObservation containing the screenshot encoded as a base64 string.
        
        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
        """
        if self._state != "started":
            self._start()
        return self._get_screenshot(display_id=display_id)
    
    def _get_screenshot(self, display_id: int = 0) -> ScreenshotObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_screenshot")

    def get_mouse_state(self) -> MouseStateObservation:
        """Return a MouseStateObservation containing the current mouse button states and position."""
        if self._state != "started":
            self._start()
        return self._get_mouse_state()

    def _get_mouse_state(self) -> MouseStateObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_mouse_state")

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return a KeyboardStateObservation with the current keyboard keys mapped to their states."""
        if self._state != "started":
            self._start()
        return self._get_keyboard_state()

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_keyboard_state")

    def get_layout_tree(self) -> LayoutTreeObservation:
        """Return a LayoutTreeObservation containing the accessibility tree of the current UI."""
        if self._state != "started":
            self._start()
        return self._get_layout_tree()

    def _get_layout_tree(self) -> LayoutTreeObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_layout_tree")

    def get_processes(self) -> ProcessesObservation:
        """Return a ProcessesObservation containing information about running processes."""
        if self._state != "started":
            self._start()
        return self._get_processes()

    def _get_processes(self) -> ProcessesObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_processes")

    def get_windows(self) -> WindowsObservation:
        """Return a WindowsObservation containing information about open windows."""
        if self._state != "started":
            self._start()
        return self._get_windows()

    def _get_windows(self) -> WindowsObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_windows")

    def get_displays(self) -> DisplaysObservation:
        """Return a DisplaysObservation containing information about connected displays."""
        if self._state != "started":
            self._start()
        return self._get_displays()

    def _get_displays(self) -> DisplaysObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_displays")

    def run_process(self, command: str, args: List[str] = [], cwd: Optional[str] = None, env: Optional[dict] = None, timeout: Optional[float] = None) -> bool:
        """Run a process with the specified parameters and return True if successful."""
        if self._state != "started":
            self._start()
        return self._run_process(RunProcessAction(command=command, args=args, cwd=cwd, env=env, timeout=timeout))

    def _run_process(self, action: RunProcessAction) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__}.run_process")

    def execute_command(self, command: str, timeout: Optional[float] = None) -> bool:
        """Execute a system command in the environment and return True if successful.

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """
        if self._state != "started":
            self._start()
        return self._execute_command(CommandAction(command=command, timeout=timeout))

    def _execute_command(self, action: CommandAction) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__}.execute_command")

    def execute_keyboard_keys_press(self, keys: List[KeyboardKey], duration: float = 0.1):
        """Execute pressing keyboard keys."""
        if self._state != "started":
            self._start()
        return self._execute_keyboard_keys_press(KeyboardKeysPressAction(keys=keys, duration=duration))
    
    def _execute_keyboard_keys_press(self, action: KeyboardKeysPressAction):
        self.execute_keyboard_keys_down(action.keys)
        self.execute_keyboard_keys_release(action.keys)

    def execute_keyboard_keys_down(self, keys: List[KeyboardKey]):
        """Execute key down for each keyboard key."""
        if self._state != "started":
            self._start()
        return self._execute_keyboard_keys_down(KeyboardKeysDownAction(keys=keys))

    def _execute_keyboard_keys_down(self, action: KeyboardKeysDownAction):
        for key in action.keys:
            self.execute_keyboard_key_down(key)

    def execute_keyboard_keys_release(self, keys: List[KeyboardKey]):
        """Execute key release for each keyboard key."""
        if self._state != "started":
            self._start()
        return self._execute_keyboard_keys_release(KeyboardKeysReleaseAction(keys=keys))

    def _execute_keyboard_keys_release(self, action: KeyboardKeysReleaseAction):
        success = True
        for key in action.keys:
            success_i = self.execute_keyboard_key_release(key)
            if not success_i:
                success = False
        return success

    def execute_keyboard_key_press(self, key: KeyboardKey, duration: float = 0.1) -> bool:
        """Execute pressing a keyboard key with a specified duration."""
        if self._state != "started":
            self._start()
        return self._execute_keyboard_key_press(KeyboardKeyPressAction(key=key, duration=duration))

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        self.execute_keyboard_key_down(KeyboardKeyDownAction(key=action.key))
        time.sleep(action.duration)
        self.execute_keyboard_key_release(KeyboardKeyReleaseAction(key=action.key))
        return True

    def execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        if self._state != "started":
            self._start()
        return self._execute_keyboard_key_down(KeyboardKeyDownAction(key=key))

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_keyboard_key_down")

    def execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        if self._state != "started":
            self._start()
        return self._execute_keyboard_key_release(KeyboardKeyReleaseAction(key=key))

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_keyboard_key_release")

    def execute_keyboard_hotkey(self, keys: List[KeyboardKey]) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        if self._state != "started":
            self._start()
        return self._execute_keyboard_hotkey(KeyboardHotkeyAction(keys=keys))

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
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

    def execute_type(self, text: str):
        """Execute typing the given text."""
        if self._state != "started":
            self._start()
        return self._execute_type(TypeAction(text=text))
    
    def _execute_type(self, action: TypeAction):
        for char in action.text:
            self.execute_keyboard_key_press(KeyboardKeyPressAction(key=char))
        return True

    def execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5):
        """Execute moving the mouse to (x, y) over the move duration."""
        if self._state != "started":
            self._start()
        return self._execute_mouse_move(MouseMoveAction(x=x, y=y, move_duration=move_duration))

    def _execute_mouse_move(self, action: MouseMoveAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_move")

    def execute_mouse_scroll(self, amount: float):
        """Execute mouse scroll by a given amount."""
        if self._state != "started":
            self._start()
        return self._execute_mouse_scroll(MouseScrollAction(amount=amount))

    def _execute_mouse_scroll(self, action: MouseScrollAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_scroll")

    def execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button down action."""
        if self._state != "started":
            self._start()
        return self._execute_mouse_button_down(MouseButtonDownAction(button=button))

    def _execute_mouse_button_down(self, action: MouseButtonDownAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_button_down")

    def execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button up action."""
        if self._state != "started":
            self._start()
        return self._execute_mouse_button_up(MouseButtonUpAction(button=button))

    def _execute_mouse_button_up(self, action: MouseButtonUpAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_button_up")

    def execute_click(self, x: int, y: int, move_duration: float = 0.5, press_duration: float = 0.1, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute a click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        if self._state != "started":
            self._start()
        return self._execute_click(ClickAction(x=x, y=y, move_duration=move_duration, press_duration=press_duration, button=button))

    def _execute_click(self, action: ClickAction) -> bool:
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

    def execute_double_click(self, x: int, y: int, move_duration: float = 0.5, press_duration: float = 0.1, button: MouseButton = MouseButton.LEFT, double_click_interval_seconds: float = 0.1):
        """Execute a double click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        if self._state != "started":
            self._start()
        return self._execute_double_click(DoubleClickAction(x=x, y=y, move_duration=move_duration, press_duration=press_duration, button=button, double_click_interval_seconds=double_click_interval_seconds))

    def _execute_double_click(self, action: DoubleClickAction):
        self.execute_click(
            ClickAction(
                x=action.x,
                y=action.y,
                move_duration=action.move_duration,
                press_duration=action.press_duration,
                button=action.button,
            )
        )
        time.sleep(action.double_click_interval_seconds)
        self.execute_click(
            ClickAction(
                x=action.x,
                y=action.y,
                move_duration=action.move_duration,
                press_duration=action.press_duration,
                button=action.button,
            )
        )
        return True

    def execute_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, move_duration: float = 0.5, button: MouseButton = MouseButton.LEFT):
        """Execute a drag action using the primitive mouse operations."""
        if self._state != "started":
            self._start()
        return self._execute_drag(DragAction(start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, move_duration=move_duration, button=button))

    def _execute_drag(self, action: DragAction):
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
