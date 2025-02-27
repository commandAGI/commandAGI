from datetime import datetime
from pathlib import Path
import time
import logging
import os
from abc import abstractmethod
from typing import ClassVar, Literal, List, Optional
from commandLAB._utils.config import APPDIR, SCREENSHOTS_DIR
from commandLAB._utils.counter import next_for_cls
from faker import Faker

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
from pydantic import BaseModel, Field


class BaseComputer(BaseModel):

    name: str
    _state: Literal["stopped", "started"] = "stopped"
    logger: Optional[logging.Logger] = None
    _file_handler: Optional[logging.FileHandler] = None
    num_retries: int = 3

    def __init__(self, name=None, **kwargs):
        name = (
            name
            or f"{self.__class__.__name__}-{next_for_cls(self.__class__.__name__):03d}"
        )
        super().__init__(name=name, **kwargs)
        
        # Initialize logger
        self.logger = logging.getLogger(f"commandLAB.computers.{self.name}")
        self.logger.setLevel(logging.INFO)

    def start(self):
        """Start the computer."""
        if self._state != "stopped":
            raise ValueError("Computer is already started")
        
        # Ensure artifact directory exists
        os.makedirs(self.artifact_dir, exist_ok=True)
        
        # Setup file handler for logging if not already set up
        if not self._file_handler:
            self._file_handler = logging.FileHandler(self.logfile_path)
            self._file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self._file_handler.setFormatter(formatter)
            self.logger.addHandler(self._file_handler)
        
        self.logger.info(f"Starting {self.__class__.__name__} computer")
        self._start()
        self._state = "started"
        self.logger.info(f"{self.__class__.__name__} computer started successfully")

    def _start(self):
        """Start the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.start")

    def stop(self):
        """Stop the computer."""
        if self._state != "started":
            raise ValueError("Computer is already stopped")
        
        self.logger.info(f"Stopping {self.__class__.__name__} computer")
        self._stop()
        self._state = "stopped"
        
        # Close and remove the file handler
        if self._file_handler:
            self.logger.info(f"{self.__class__.__name__} computer stopped successfully")
            self._file_handler.close()
            self.logger.removeHandler(self._file_handler)
            self._file_handler = None

    def _stop(self):
        """Stop the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.stop")

    def reset_state(self):
        """Reset the computer state."""
        self.logger.info(f"Resetting {self.__class__.__name__} computer state")
        self.stop()
        self.start()

    @property
    def artifact_dir(self) -> Path:
        return APPDIR / self.name
    
    @property
    def logfile_path(self) -> Path:
        return self.artifact_dir / "logfile.log"

    @property
    def _new_screenshot_name(self) -> Path:
        return self.artifact_dir / f"screenshot-{datetime.now():%Y-%m-%d_%H-%M-%S-%f}"

    def get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> ScreenshotObservation:
        """Return a ScreenshotObservation containing the screenshot encoded as a base64 string.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        if self._state != "started":
            self._start()
        try:
            return self._get_screenshot(display_id=display_id, format=format)
        except Exception as e:
            self.logger.error(f"Error getting screenshot: {e}")
            return ScreenshotObservation()

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> ScreenshotObservation:
        """Get a screenshot of the current state.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        raise NotImplementedError(f"{self.__class__.__name__}.get_screenshot")

    def get_mouse_state(self) -> MouseStateObservation:
        """Return a MouseStateObservation containing the current mouse button states and position."""
        if self._state != "started":
            self._start()
        try:
            return self._get_mouse_state()
        except Exception as e:
            self.logger.error(f"Error getting mouse state: {e}")
            return MouseStateObservation()

    def _get_mouse_state(self) -> MouseStateObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_mouse_state")

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return a KeyboardStateObservation with the current keyboard keys mapped to their states."""
        if self._state != "started":
            self._start()
        try:
            return self._get_keyboard_state()
        except Exception as e:
            self.logger.error(f"Error getting keyboard state: {e}")
            return KeyboardStateObservation()

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_keyboard_state")

    def get_layout_tree(self) -> LayoutTreeObservation:
        """Return a LayoutTreeObservation containing the accessibility tree of the current UI."""
        if self._state != "started":
            self._start()
        try:
            return self._get_layout_tree()
        except Exception as e:
            self.logger.error(f"Error getting layout tree: {e}")
            return LayoutTreeObservation()

    def _get_layout_tree(self) -> LayoutTreeObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_layout_tree")

    def get_processes(self) -> ProcessesObservation:
        """Return a ProcessesObservation containing information about running processes."""
        if self._state != "started":
            self._start()
        try:
            return self._get_processes()
        except Exception as e:
            self.logger.error(f"Error getting processes: {e}")
            return ProcessesObservation()

    def _get_processes(self) -> ProcessesObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_processes")

    def get_windows(self) -> WindowsObservation:
        """Return a WindowsObservation containing information about open windows."""
        if self._state != "started":
            self._start()
        try:
            return self._get_windows()
        except Exception as e:
            self.logger.error(f"Error getting windows: {e}")
            return WindowsObservation()

    def _get_windows(self) -> WindowsObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_windows")

    def get_displays(self) -> DisplaysObservation:
        """Return a DisplaysObservation containing information about connected displays."""
        if self._state != "started":
            self._start()
        try:
            return self._get_displays()
        except Exception as e:
            self.logger.error(f"Error getting displays: {e}")
            return DisplaysObservation()

    def _get_displays(self) -> DisplaysObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_displays")

    def run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Run a process with the specified parameters and return True if successful."""
        if self._state != "started":
            self._start()
        
        action = RunProcessAction(
            command=command, args=args, cwd=cwd, env=env, timeout=timeout
        )
        
        for attempt in range(self.num_retries):
            try:
                self._run_process(action)
                return True
            except Exception as e:
                self.logger.error(f"Error running process (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _run_process(self, action: RunProcessAction) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__}.run_process")

    def execute_command(self, command: str, timeout: Optional[float] = None) -> bool:
        """Execute a system command in the environment and return True if successful.

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """
        if self._state != "started":
            self._start()
        
        action = CommandAction(command=command, timeout=timeout)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_command(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing command (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_command(self, action: CommandAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_command")

    def execute_keyboard_keys_press(
        self, keys: List[KeyboardKey], duration: float = 0.1
    ) -> bool:
        """Execute pressing keyboard keys."""
        if self._state != "started":
            self._start()
        
        action = KeyboardKeysPressAction(keys=keys, duration=duration)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_keys_press(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing keyboard keys press (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_keyboard_keys_press(self, action: KeyboardKeysPressAction):
        self.execute_keyboard_keys_down(action.keys)
        self.execute_keyboard_keys_release(action.keys)

    def execute_keyboard_keys_down(self, keys: List[KeyboardKey]) -> bool:
        """Execute key down for each keyboard key."""
        if self._state != "started":
            self._start()
        
        action = KeyboardKeysDownAction(keys=keys)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_keys_down(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing keyboard keys down (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_keyboard_keys_down(self, action: KeyboardKeysDownAction):
        for key in action.keys:
            self.execute_keyboard_key_down(key)

    def execute_keyboard_keys_release(self, keys: List[KeyboardKey]) -> bool:
        """Execute key release for each keyboard key."""
        if self._state != "started":
            self._start()
        
        action = KeyboardKeysReleaseAction(keys=keys)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_keys_release(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing keyboard keys release (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_keyboard_keys_release(self, action: KeyboardKeysReleaseAction):
        for key in action.keys:
            self.execute_keyboard_key_release(key)

    def execute_keyboard_key_press(
        self, key: KeyboardKey, duration: float = 0.1
    ) -> bool:
        """Execute pressing a keyboard key with a specified duration."""
        if self._state != "started":
            self._start()
        
        action = KeyboardKeyPressAction(key=key, duration=duration)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_key_press(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing keyboard key press (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction):
        self.execute_keyboard_key_down(KeyboardKeyDownAction(key=action.key))
        time.sleep(action.duration)
        self.execute_keyboard_key_release(KeyboardKeyReleaseAction(key=action.key))

    def execute_keyboard_key_down(self, key: KeyboardKey) -> bool:
        """Execute key down for a keyboard key."""
        if self._state != "started":
            self._start()
        
        action = KeyboardKeyDownAction(key=key)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_key_down(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing keyboard key down (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_keyboard_key_down"
        )

    def execute_keyboard_key_release(self, key: KeyboardKey) -> bool:
        """Execute key release for a keyboard key."""
        if self._state != "started":
            self._start()
        
        action = KeyboardKeyReleaseAction(key=key)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_key_release(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing keyboard key release (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_keyboard_key_release"
        )

    def execute_keyboard_hotkey(self, keys: List[KeyboardKey]) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        if self._state != "started":
            self._start()
        
        action = KeyboardHotkeyAction(keys=keys)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_hotkey(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing keyboard hotkey (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction):
        for key in action.keys:
            self.execute_keyboard_key_down(key)
        for key in reversed(action.keys):
            self.execute_keyboard_key_release(key)

    def execute_type(self, text: str) -> bool:
        """Execute typing the given text."""
        if self._state != "started":
            self._start()
        
        action = TypeAction(text=text)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_type(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing type (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_type(self, action: TypeAction):
        for char in action.text:
            self.execute_keyboard_key_press(KeyboardKeyPressAction(key=char))

    def execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5) -> bool:
        """Execute moving the mouse to (x, y) over the move duration."""
        if self._state != "started":
            self._start()
        
        action = MouseMoveAction(x=x, y=y, move_duration=move_duration)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_move(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing mouse move (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_mouse_move(self, action: MouseMoveAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_move")

    def execute_mouse_scroll(self, amount: float) -> bool:
        """Execute mouse scroll by a given amount."""
        if self._state != "started":
            self._start()
        
        action = MouseScrollAction(amount=amount)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_scroll(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing mouse scroll (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_mouse_scroll(self, action: MouseScrollAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_scroll")

    def execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button down action."""
        if self._state != "started":
            self._start()
        
        action = MouseButtonDownAction(button=button)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_button_down(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing mouse button down (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_mouse_button_down(self, action: MouseButtonDownAction):
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_mouse_button_down"
        )

    def execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button up action."""
        if self._state != "started":
            self._start()
        
        action = MouseButtonUpAction(button=button)
        
        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_button_up(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing mouse button up (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_mouse_button_up(self, action: MouseButtonUpAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_button_up")

    def execute_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
    ) -> bool:
        """Execute a click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        if self._state != "started":
            self._start()
        
        action = ClickAction(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
        )
        
        for attempt in range(self.num_retries):
            try:
                self._execute_click(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing click (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

    def _execute_click(self, action: ClickAction):
        move_action = MouseMoveAction(
            x=action.x, y=action.y, move_duration=action.move_duration
        )
        self.execute_mouse_move(move_action)
        down_action = MouseButtonDownAction(button=action.button)
        self.execute_mouse_button_down(down_action)
        time.sleep(action.press_duration)
        up_action = MouseButtonUpAction(button=action.button)
        self.execute_mouse_button_up(up_action)

    def execute_double_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
        double_click_interval_seconds: float = 0.1,
    ) -> bool:
        """Execute a double click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        if self._state != "started":
            self._start()
        
        action = DoubleClickAction(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
            double_click_interval_seconds=double_click_interval_seconds,
        )
        
        for attempt in range(self.num_retries):
            try:
                self._execute_double_click(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing double click (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

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

    def execute_drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ) -> bool:
        """Execute a drag action using the primitive mouse operations."""
        if self._state != "started":
            self._start()
        
        action = DragAction(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            move_duration=move_duration,
            button=button,
        )
        
        for attempt in range(self.num_retries):
            try:
                self._execute_drag(action)
                return True
            except Exception as e:
                self.logger.error(f"Error executing drag (attempt {attempt+1}/{self.num_retries}): {e}")
                if attempt == self.num_retries - 1:
                    return False
        
        return False

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
