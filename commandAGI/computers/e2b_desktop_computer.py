import base64
import datetime
import io
import os
import tempfile
from pathlib import Path
from typing import AnyStr, List, Literal, Optional, Union

try:
    from e2b_desktop import Sandbox
    from PIL import Image
except ImportError:
    raise ImportError(
        "The E2B Desktop dependencies are not installed. Please install commandAGI with the e2b_desktop extra:\n\npip install commandAGI[e2b_desktop]"
    )

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI.computers.base_computer import BaseComputer, BaseComputerFile
from commandAGI.types import (
    ClickAction,
    DoubleClickAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    RunProcessAction,
    ScreenshotObservation,
    ShellCommandAction,
    TypeAction,
)


# E2B Desktop-specific mappings
def mouse_button_to_e2b(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to E2B Desktop button name.

    E2B Desktop uses the following button names:
    'left' = left button
    'middle' = middle button
    'right' = right button
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # E2B Desktop mouse button mapping
    e2b_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right",
    }

    # Default to left button if not found
    return e2b_button_mapping.get(button, "left")


def keyboard_key_to_e2b(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to E2B Desktop key name.

    E2B Desktop uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # E2B Desktop key mappings
    e2b_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "return",  # E2B uses "return" not "enter"
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "esc",  # E2B uses "esc" not "escape"
        KeyboardKey.HOME: "home",
        KeyboardKey.END: "end",
        KeyboardKey.PAGE_UP: "pageup",
        KeyboardKey.PAGE_DOWN: "pagedown",
        # Arrow keys
        KeyboardKey.UP: "up",
        KeyboardKey.DOWN: "down",
        KeyboardKey.LEFT: "left",
        KeyboardKey.RIGHT: "right",
        # Modifier keys
        KeyboardKey.SHIFT: "shift",
        KeyboardKey.CTRL: "ctrl",
        KeyboardKey.LCTRL: "ctrl",  # E2B may not distinguish left/right
        KeyboardKey.RCTRL: "ctrl",  # E2B may not distinguish left/right
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # E2B may not distinguish left/right
        KeyboardKey.RALT: "alt",  # E2B may not distinguish left/right
        KeyboardKey.META: "win",  # Windows key
        KeyboardKey.LMETA: "win",  # E2B may not distinguish left/right
        KeyboardKey.RMETA: "win",  # E2B may not distinguish left/right
        # Function keys
        KeyboardKey.F1: "f1",
        KeyboardKey.F2: "f2",
        KeyboardKey.F3: "f3",
        KeyboardKey.F4: "f4",
        KeyboardKey.F5: "f5",
        KeyboardKey.F6: "f6",
        KeyboardKey.F7: "f7",
        KeyboardKey.F8: "f8",
        KeyboardKey.F9: "f9",
        KeyboardKey.F10: "f10",
        KeyboardKey.F11: "f11",
        KeyboardKey.F12: "f12",
    }

    # For letter keys and number keys, use the value directly
    return e2b_key_mapping.get(key, key.value)


class E2BDesktopComputerFile(BaseComputerFile):
    """Implementation of BaseComputerFile for E2B Desktop computer files.

    This class provides a file-like interface for working with files on a remote computer
    accessed via E2B Desktop. It uses temporary local files and E2B Desktop's file transfer
    capabilities to provide file-like access.
    """


class E2BDesktopComputer(BaseComputer):
    """Environment that uses E2B Desktop Sandbox for secure computer interactions"""

    def __init__(self, video_stream=False):
        super().__init__()
        self.video_stream = video_stream
        self.e2b_desktop = None

    def _start(self):
        """Start the E2B desktop environment."""
        if not self.e2b_desktop:
            self.logger.info("Initializing E2B Desktop Sandbox")
            self.e2b_desktop = Sandbox(video_stream=self.video_stream)
            self.logger.info("E2B Desktop Sandbox initialized successfully")
        return True

    def _stop(self):
        """Stop the E2B desktop environment."""
        if self.e2b_desktop:
            self.logger.info("Closing E2B Desktop Sandbox")
            # E2B sandbox automatically closes when object is destroyed
            self.e2b_desktop = None
            self.logger.info("E2B Desktop Sandbox closed successfully")
        return True

    def reset_state(self):
        """Reset the desktop environment and return initial observation"""
        self.logger.info("Resetting E2B Desktop environment state")
        # Show desktop to reset the environment state
        if self.e2b_desktop:
            self.logger.debug("Showing desktop with Win+D hotkey")
            self.e2b_desktop.hotkey("win", "d")
        else:
            self.logger.debug("Desktop not initialized, starting it")
            self._start()

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> Union[str, Image.Image, Path]:
        """Return a screenshot of the current state in the specified format.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        # Create a temporary file to store the screenshot
        temp_screenshot_path = self._new_screenshot_name

        # Take the screenshot using E2B Desktop
        self.e2b_desktop.screenshot(temp_screenshot_path)

        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=temp_screenshot_path,
            output_format=format,
            input_format="path",
            computer_name="e2b",
            cleanup_temp_file=True,
        )

    def _get_mouse_position(self) -> tuple[int, int]:
        """Return current mouse position."""
        self.logger.debug("E2B Desktop does not support getting mouse position")
        raise NotImplementedError("E2B Desktop does not support getting mouse position")

    def _get_mouse_button_states(self) -> dict[str, bool]:
        """Return states of mouse buttons."""
        self.logger.debug("E2B Desktop does not support getting mouse button states")
        raise NotImplementedError(
            "E2B Desktop does not support getting mouse button states"
        )

    def _get_keyboard_key_states(self) -> dict[str, bool]:
        """Return states of keyboard keys."""
        self.logger.debug("E2B Desktop does not support getting keyboard key states")
        raise NotImplementedError(
            "E2B Desktop does not support getting keyboard key states"
        )

    def _shell(self, command: str):
        """Execute a system command in the E2B Desktop VM."""
        self.e2b_desktop.commands.run(command)

    def _keydown(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        # E2B Desktop doesn't have direct key_down method, use PyAutoGUI
        e2b_key = keyboard_key_to_e2b(key)
        self.e2b_desktop.pyautogui(f"pyautogui.keyDown('{e2b_key}')")

    def _keyup(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        # E2B Desktop doesn't have direct key_up method, use PyAutoGUI
        e2b_key = keyboard_key_to_e2b(key)
        self.e2b_desktop.pyautogui(f"pyautogui.keyUp('{e2b_key}')")

    def _type(self, text: str):
        """Type text using E2B Desktop."""
        self.e2b_desktop.write(text)

    def _move(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to specified coordinates using E2B Desktop."""
        self.logger.debug(f"Moving mouse to: ({x}, {y})")
        # E2B Desktop doesn't have a direct move duration parameter
        self.e2b_desktop.mouse_move(x, y)

    def _scroll(self, amount: float):
        """Scroll mouse using E2B Desktop."""
        # E2B Desktop scroll takes an integer amount
        self.e2b_desktop.scroll(int(amount))

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using PyAutoGUI through E2B Desktop."""
        e2b_button = mouse_button_to_e2b(button)
        self.e2b_desktop.pyautogui(f"pyautogui.mouseDown(button='{e2b_button}')")

    def _mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using PyAutoGUI through E2B Desktop."""
        e2b_button = mouse_button_to_e2b(button)
        self.e2b_desktop.pyautogui(f"pyautogui.mouseUp(button='{e2b_button}')")

    def _click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a click action using E2B Desktop's click methods."""
        # Move to position first
        self.e2b_desktop.mouse_move(x, y)

        # Then click using the appropriate method
        e2b_button = mouse_button_to_e2b(button)
        if e2b_button == "left":
            self.e2b_desktop.left_click()
        elif e2b_button == "right":
            self.e2b_desktop.right_click()
        elif e2b_button == "middle":
            self.e2b_desktop.middle_click()

    def _double_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
        double_click_interval_seconds: float = 0.1,
    ):
        """Execute a double click action using E2B Desktop's double_click method."""
        # Move to position first
        self.e2b_desktop.mouse_move(x, y)

        # Then double click (E2B only supports left double click)
        self.e2b_desktop.double_click()

    def _keypress(self, key: KeyboardKey, duration: float = 0.1):
        """Execute pressing a keyboard key."""
        e2b_key = keyboard_key_to_e2b(key)
        # E2B doesn't have a direct press method, use PyAutoGUI
        self.e2b_desktop.pyautogui(f"pyautogui.press('{e2b_key}')")

    def _hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey using E2B Desktop's hotkey method."""
        # Convert keys to E2B format
        e2b_keys = [keyboard_key_to_e2b(key) for key in keys]

        # E2B Desktop's hotkey method takes individual arguments, not a list
        self.e2b_desktop.hotkey(*e2b_keys)

    def locate_text_on_screen(self, text: str, additional_ocr_args: dict = {}) -> tuple[int, int] | None:
        """Find text on screen and return coordinates.

        This is a direct wrapper for E2B Desktop's locate_on_screen method.
        """
        return self.e2b_desktop.locate_on_screen(text, **additional_ocr_args)

    def open_file(self, file_path):
        """Open a file with the default application.

        This is a direct wrapper for E2B Desktop's open method.
        """
        self.e2b_desktop.open(file_path)
        return True

    def get_video_stream_url(self) -> str:
        """Get the URL for the video stream of the E2B Desktop instance."""
        if not self.video_stream:
            self.logger.warning(
                "Warning: Video stream was not enabled during initialization"
            )
            return ""

        # The method name might be different based on the API
        # Check if the method exists
        if hasattr(self.e2b_desktop, "get_video_stream_url"):
            return self.e2b_desktop.get_video_stream_url()
        else:
            self.logger.warning(
                "Warning: get_video_stream_url method not found in E2B Desktop API"
            )
            return ""

    def _pause(self):
        """Pause the E2B Desktop instance.

        For E2B Desktop, pausing means putting the sandbox into a paused state.
        """
        if self.e2b_desktop:
            self.logger.info("Pausing E2B Desktop sandbox")
            try:
                if hasattr(self.e2b_desktop, "pause"):
                    self.e2b_desktop.pause()
                    self.logger.info("E2B Desktop sandbox paused successfully")
                else:
                    self.logger.warning("Pause method not found in E2B Desktop API")
            except Exception as e:
                self.logger.error(f"Error pausing E2B Desktop sandbox: {e}")
                raise

    def _resume(self, timeout_hours: Optional[float] = None):
        """Resume the E2B Desktop instance.

        For E2B Desktop, resuming means taking the sandbox out of a paused state.

        Args:
            timeout_hours: Optional timeout in hours after which the sandbox will automatically pause again.
                          Not used in the current E2B Desktop implementation.
        """
        if self.e2b_desktop:
            self.logger.info("Resuming E2B Desktop sandbox")
            try:
                if hasattr(self.e2b_desktop, "resume"):
                    self.e2b_desktop.resume()
                    self.logger.info("E2B Desktop sandbox resumed successfully")
                else:
                    self.logger.warning("Resume method not found in E2B Desktop API")
            except Exception as e:
                self.logger.error(f"Error resuming E2B Desktop sandbox: {e}")
                raise

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the E2B Desktop instance.

        Returns:
            str: The URL for the video stream, or an empty string if video streaming is not available.
        """
        return self.get_video_stream_url()

    def _run_process(
        self,
        command: str,
        args: List[str] = None,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Run a process with the specified parameters.

        This method uses the E2B Desktop API to run a process in the sandbox.

        Args:
            command: The command to execute
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables dictionary
            timeout: Timeout in seconds

        Returns:
            bool: True if the process was executed successfully
        """
        args = args or []
        self.logger.info(f"Running process in E2B Desktop: {command} with args: {args}")
        return self._default_run_process(
            command=command, args=args, cwd=cwd, env=env, timeout=timeout
        )

    def _open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ) -> E2BDesktopComputerFile:
        """Open a file on the E2B Desktop VM.

        This method uses E2B Desktop's file transfer capabilities to provide
        file-like access to files on the VM.

        Args:
            path: Path to the file on the E2B Desktop VM
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            An E2BDesktopComputerFile instance for the specified file
        """
        return E2BDesktopComputerFile(
            computer=self,
            path=path,
            mode=mode,
            encoding=encoding,
            errors=errors,
            buffering=buffering,
        )
