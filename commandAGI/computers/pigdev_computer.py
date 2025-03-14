import base64
import datetime
import io
import os
import tempfile
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Literal, Optional, Union

try:
    from pig import Client
    from PIL import Image
except ImportError:
    raise ImportError(
        "The PigDev dependencies are not installed. Please install commandAGI with the pigdev extra:\n\npip install commandAGI[pigdev]"
    )

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI.computers.base_computer import BaseComputer, BaseComputerFile
from commandAGI.types import (
    ClickAction,
    DoubleClickAction,
    DragAction,
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


# PigDev-specific mappings
def mouse_button_to_pigdev(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to PigDev button name.

    PigDev uses string names for mouse buttons that match our MouseButton values.
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # PigDev mouse button mapping
    pigdev_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right",
    }

    return pigdev_button_mapping.get(
        button, "left"
    )  # Default to left button if not found


def keyboard_key_to_pigdev(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to PigDev key name.

    PigDev uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # PigDev-specific key mappings
    pigdev_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "enter",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "escape",
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
        KeyboardKey.LCTRL: "ctrl",  # PigDev may not distinguish between left/right
        KeyboardKey.RCTRL: "ctrl",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # PigDev may not distinguish between left/right
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "super",  # Command/Windows key is called "super" in PigDev
        KeyboardKey.LMETA: "super",  # PigDev may not distinguish between left/right
        KeyboardKey.RMETA: "super",
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
    return pigdev_key_mapping.get(key, key.value)


class PigDevComputerFile(BaseComputerFile):
    """Implementation of BaseComputerFile for PigDev computer files.

    This class provides a file-like interface for working with files on a remote computer
    accessed via PigDev. It uses temporary local files and PigDev's file transfer
    capabilities to provide file-like access.
    """


class PigDevComputer(BaseComputer):
    """Environment that uses PigDev for secure computer interactions"""

    def __init__(self, api_key: Optional[str] = None, machine_id: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.machine_id = machine_id
        self.client = None
        self.machine = None
        self.connection = None

    def _start(self):
        """Start the PigDev environment and establish a connection.

        This method initializes the Pig client, selects the appropriate machine,
        and establishes a connection that will be maintained throughout the session.
        """
        # Initialize the Pig client
        self.logger.info("Initializing PigDev client")
        if self.api_key:
            self.logger.debug("Using provided API key")
            self.client = Client(api_key=self.api_key)
        else:
            self.logger.debug("Using default API key from environment")
            self.client = Client()

        # Get the machine (either local or remote)
        if self.machine_id:
            self.logger.info(
                f"Connecting to remote machine with ID: {
                    self.machine_id}"
            )
            self.machine = self.client.machines.get(self.machine_id)
        else:
            self.logger.info("Connecting to local machine")
            self.machine = self.client.machines.local()

        # Establish a connection that will be maintained throughout the session
        self.logger.info("Establishing connection to machine")
        self.connection = self.machine.connect().__enter__()
        self.logger.info("PigDev connection established successfully")
        return True

    def _stop(self):
        """Stop the PigDev environment and close the connection.

        This method properly closes the connection and cleans up resources.
        """
        if self.connection:
            self.logger.info("Closing PigDev connection")
            # Properly exit the connection context manager
            self.machine.connect().__exit__(None, None, None)
            self.connection = None

        self.client = None
        self.machine = None
        self.logger.info("PigDev connection closed successfully")
        return True

    def reset_state(self):
        """Reset the PigDev environment"""
        self.logger.info("Resetting PigDev environment")
        # For PigDev, we'll restart the client connection
        self._stop()
        self._start()

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> Union[str, Image.Image, Path]:
        """Return a screenshot of the current state in the specified format."""
        # Get the screenshot from PigDev (returns PIL Image)
        self.logger.debug("Capturing screenshot via PigDev")
        screenshot = self.connection.screenshot()

        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=screenshot,
            output_format=format,
            input_format="PIL",
            computer_name="pigdev",
        )

    def _get_mouse_position(self) -> tuple[int, int]:
        """Return current mouse position."""
        self.logger.debug("Getting mouse cursor position")
        # Get cursor position using the existing connection
        x, y = self.connection.cursor_position()
        self.logger.debug(f"Cursor position: ({x}, {y})")
        return (x, y)

    def _get_mouse_button_states(self) -> dict[str, bool]:
        """Return states of mouse buttons."""
        # PigDev doesn't provide button state information
        raise NotImplementedError("PigDev does not support getting mouse button states")

    def _get_keyboard_key_states(self) -> dict[str, bool]:
        """Return states of keyboard keys."""
        raise NotImplementedError("PigDev does not support getting keyboard key states")

    def _execute_shell_command(
        self, command: str, timeout: float | None = None, executable: str | None = None
    ):
        """Execute a system command in the PigDev VM."""
        raise NotImplementedError("PigDev does not support direct command execution")

    def _execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key using PigDev."""
        try:
            # Convert to PigDev key format
            pigdev_key = keyboard_key_to_pigdev(key)
            self.logger.debug(f"Pressing key down: {key} (PigDev key: {pigdev_key})")

            # Use the existing connection
            self.connection.key_down(pigdev_key)
        except Exception as e:
            self.logger.error(f"Error executing key down via PigDev: {e}")
            raise

    def _execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key using PigDev."""
        try:
            # Convert to PigDev key format
            pigdev_key = keyboard_key_to_pigdev(key)
            self.logger.debug(f"Releasing key: {key} (PigDev key: {pigdev_key})")

            # Use the existing connection
            self.connection.key_up(pigdev_key)
        except Exception as e:
            self.logger.error(f"Error executing key release via PigDev: {e}")
            raise

    def _execute_type(self, text: str):
        """Type text using PigDev."""
        try:
            self.logger.debug(f"Typing text: {text}")
            # Use the existing connection
            self.connection.type(text)
        except Exception as e:
            self.logger.error(f"Error typing text via PigDev: {e}")
            raise

    def _execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5):
        """Move mouse to specified coordinates using PigDev."""
        try:
            self.logger.debug(f"Moving mouse to: ({x}, {y})")
            # Use the existing connection
            self.connection.mouse_move(x=x, y=y)
        except Exception as e:
            self.logger.error(f"Error moving mouse via PigDev: {e}")
            raise

    def _execute_mouse_scroll(self, amount: float):
        """Scroll mouse using PigDev."""
        self.logger.debug("PigDev does not support mouse scrolling")
        # PigDev doesn't have a direct scroll method
        raise NotImplementedError("PigDev does not support mouse scrolling")

    def _execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using PigDev."""
        pigdev_button = mouse_button_to_pigdev(button)
        self.logger.debug(
            f"Pressing mouse button down: {button} (PigDev button: {pigdev_button})"
        )

        # Use the existing connection
        self.connection.mouse_down(pigdev_button)

    def _execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using PigDev."""
        pigdev_button = mouse_button_to_pigdev(button)
        self.logger.debug(
            f"Releasing mouse button: {button} (PigDev button: {pigdev_button})"
        )

        # Use the existing connection
        self.connection.mouse_up(pigdev_button)

    def _execute_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a click action at the given coordinates using PigDev's click method."""
        self.logger.debug(f"Clicking at: ({x}, {y}) with button: {button}")
        # Use the existing connection
        # Move to position first
        self.connection.mouse_move(x=x, y=y)
        # Then click using the appropriate button
        if button == MouseButton.LEFT:
            self.connection.left_click()
        else:
            self.connection.right_click()

    def _execute_double_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
        double_click_interval_seconds: float = 0.1,
    ):
        """Execute a double click action at the given coordinates using PigDev's double_click method."""
        self.logger.debug(f"Double-clicking at: ({x}, {y})")
        # Use the existing connection
        # Move to position first
        self.connection.mouse_move(x=x, y=y)
        # Then double click (PigDev only supports left double click)
        self.connection.double_click()

    def _execute_drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a drag action using PigDev's left_click_drag method."""
        self.logger.debug(
            f"Dragging from: ({start_x}, {start_y}) to: ({end_x}, {end_y})"
        )
        # Use the existing connection
        # First move to the start position
        self.connection.mouse_move(x=start_x, y=start_y)
        # Then perform the drag to the end position
        self.connection.left_click_drag(x=end_x, y=end_y)

    def _execute_keyboard_key_press(self, key: KeyboardKey, duration: float = 0.1):
        """Execute pressing a keyboard key using PigDev's key method."""
        pigdev_key = keyboard_key_to_pigdev(key)
        self.logger.debug(f"Pressing key: {key} (PigDev key: {pigdev_key})")

        # Use the existing connection
        self.connection.key(pigdev_key)

    def _execute_keyboard_hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey using PigDev's key method with combined keys."""
        # Convert keys to PigDev format
        pigdev_keys = [keyboard_key_to_pigdev(key) for key in keys]
        hotkey_str = "+".join(pigdev_keys)
        self.logger.debug(f"Executing hotkey: {hotkey_str}")

        # Use the existing connection
        # PigDev supports hotkeys as a single string with '+' separator
        self.connection.key(hotkey_str)

    def _pause(self):
        """Pause the PigDev connection.

        For PigDev, pausing means putting the machine into a paused state.
        """
        if self.connection:
            self.logger.info("Pausing PigDev machine")
            try:
                self.connection.pause()
                self.logger.info("PigDev machine paused successfully")
            except Exception as e:
                self.logger.error(f"Error pausing PigDev machine: {e}")
                raise

    def _resume(self, timeout_hours: Optional[float] = None):
        """Resume the PigDev connection.

        For PigDev, resuming means taking the machine out of a paused state.

        Args:
            timeout_hours: Optional timeout in hours after which the machine will automatically pause again.
        """
        if self.connection:
            self.logger.info("Resuming PigDev machine")
            try:
                # Convert hours to seconds if provided
                timeout_seconds = None
                if timeout_hours is not None:
                    timeout_seconds = timeout_hours * 3600

                self.connection.resume(timeout_seconds=timeout_seconds)
                self.logger.info("PigDev machine resumed successfully")
            except Exception as e:
                self.logger.error(f"Error resuming PigDev machine: {e}")
                raise

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the PigDev instance.

        Returns:
            str: The URL for the video stream, or an empty string if video streaming is not available.
        """
        if not self.connection:
            self.logger.warning(
                "Cannot get video stream URL: PigDev connection not established"
            )
            return ""

        try:
            stream_info = self.connection.get_stream_info()
            if stream_info and "url" in stream_info:
                return stream_info["url"]
            return ""
        except Exception as e:
            self.logger.error(f"Error getting PigDev video stream URL: {e}")
            return ""

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Run a process with the specified parameters.

        This method attempts to use the PigDev API to run a process, but falls back
        to the default implementation using shell commands if direct process execution
        is not supported.

        Args:
            command: The command to run
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables for the process
            timeout: Timeout in seconds

        Returns:
            bool: True if the process was executed successfully
        """
        self.logger.info(f"Running process via PigDev: {command} with args: {args}")
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
    ) -> PigDevComputerFile:
        """Open a file on the remote computer.

        This method uses PigDev's file transfer capabilities to provide
        file-like access to files on the remote computer.

        Args:
            path: Path to the file on the remote computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            A PigDevComputerFile instance for the specified file
        """
        return PigDevComputerFile(
            computer=self,
            path=path,
            mode=mode,
            encoding=encoding,
            errors=errors,
            buffering=buffering,
        )
