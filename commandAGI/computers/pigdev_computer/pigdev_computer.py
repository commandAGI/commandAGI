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



class PigDevComputer(BaseComputer):
    """Environment that uses PigDev for secure computer interactions"""

    preferred_video_stream_mode: Literal["vnc", "http"] = "http"
    '''Used  to indicate which video stream mode is more efficient (ie, to avoid using proxy streams)'''

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

    def _shell(
        self, command: str, timeout: float | None = None, executable: str | None = None
    ):
        """Execute a system command in the PigDev VM."""
        raise NotImplementedError("PigDev does not support direct command execution")

    def _keydown(self, key: KeyboardKey):
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

    def _keyup(self, key: KeyboardKey):
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

    def _type(self, text: str):
        """Type text using PigDev."""
        try:
            self.logger.debug(f"Typing text: {text}")
            # Use the existing connection
            self.connection.type(text)
        except Exception as e:
            self.logger.error(f"Error typing text via PigDev: {e}")
            raise

    def _move(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to specified coordinates using PigDev."""
        try:
            self.logger.debug(f"Moving mouse to: ({x}, {y})")
            # Use the existing connection
            self.connection.mouse_move(x=x, y=y)
        except Exception as e:
            self.logger.error(f"Error moving mouse via PigDev: {e}")
            raise

    def _scroll(self, amount: float):
        """Scroll mouse using PigDev."""
        self.logger.debug("PigDev does not support mouse scrolling")
        # PigDev doesn't have a direct scroll method
        raise NotImplementedError("PigDev does not support mouse scrolling")

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using PigDev."""
        pigdev_button = mouse_button_to_pigdev(button)
        self.logger.debug(
            f"Pressing mouse button down: {button} (PigDev button: {pigdev_button})"
        )

        # Use the existing connection
        self.connection.mouse_down(pigdev_button)

    def _mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using PigDev."""
        pigdev_button = mouse_button_to_pigdev(button)
        self.logger.debug(
            f"Releasing mouse button: {button} (PigDev button: {pigdev_button})"
        )

        # Use the existing connection
        self.connection.mouse_up(pigdev_button)

    def _click(
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

    def _double_click(
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

    def _drag(
        self,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a drag action using PigDev's left_click_drag method."""
        self.logger.debug(
            f"Dragging from: ({end_x}, {end_y})"
        )
        # Use the existing connection
        # Then perform the drag to the end position
        self.connection.left_click_drag(x=end_x, y=end_y)

    def _keypress(self, key: KeyboardKey, duration: float = 0.1):
        """Execute pressing a keyboard key using PigDev's key method."""
        pigdev_key = keyboard_key_to_pigdev(key)
        self.logger.debug(f"Pressing key: {key} (PigDev key: {pigdev_key})")

        # Use the existing connection
        self.connection.key(pigdev_key)

    def _hotkey(self, keys: List[KeyboardKey]):
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

    def _resume(self):
        """Resume the PigDev connection.

        For PigDev, resuming means taking the machine out of a paused state.
        """
        if self.connection:
            self.logger.info("Resuming PigDev machine")
            try:
                self.connection.resume()
                self.logger.info("PigDev machine resumed successfully")
            except Exception as e:
                self.logger.error(f"Error resuming PigDev machine: {e}")
                raise

    def _get_http_video_stream_url(self) -> str:
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
        
    def _start_http_video_stream(
        self,
        host: str = 'localhost',
        port: int = 8080,
        frame_rate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg"
    ):
        """Start the HTTP video stream for the PigDev instance.

        Args:
            host: HTTP server host address
            port: HTTP server port
            frame_rate: Target frame rate for the video stream
            quality: JPEG/PNG compression quality (0-100)
            scale: Scale factor for the video stream (0.1-1.0)
            compression: Image compression format to use
        """
        # not needed for PigDev as streaming is handled internally

    def _stop_http_video_stream(self):
        """Stop the HTTP video stream for the PigDev instance."""
        # not needed for PigDev as streaming is handled internally

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ):
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
        """
        self.logger.info(f"Running process via PigDev: {command} with args: {args}")
        self._default_run_process(
            command=command, args=args, cwd=cwd, env=env, timeout=timeout
        )
