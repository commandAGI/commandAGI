import base64
import datetime
import io
import os
import tempfile
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Literal, Optional, Union

try:
    import scrapybara
    from PIL import Image
except ImportError:
    raise ImportError(
        "The Scrapybara dependencies are not installed. Please install commandAGI with the scrapybara extra:\n\npip install commandAGI[scrapybara]"
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


# Scrapybara-specific mappings
def mouse_button_to_scrapybara(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to Scrapybara button action.

    Scrapybara uses specific action names for mouse buttons:
    - "left_click" for left button
    - "right_click" for right button
    - "middle_click" for middle button
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # Scrapybara mouse button mapping
    scrapybara_button_mapping = {
        MouseButton.LEFT: "left_click",
        MouseButton.MIDDLE: "middle_click",
        MouseButton.RIGHT: "right_click",
    }

    return scrapybara_button_mapping.get(
        button, "left_click"
    )  # Default to left click if not found


def keyboard_key_to_scrapybara(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to Scrapybara key name.

    Scrapybara uses specific key names that may differ from our standard KeyboardKey values.
    For hotkeys, Scrapybara uses the '+' separator (e.g., "ctrl+c").
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # Scrapybara-specific key mappings
    scrapybara_key_mapping = {
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
        KeyboardKey.LCTRL: "ctrl",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RCTRL: "ctrl",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "meta",  # Command/Windows key
        KeyboardKey.LMETA: "meta",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RMETA: "meta",
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
    return scrapybara_key_mapping.get(key, key.value)


class ScrapybaraComputerFile(BaseComputerFile):
    """Implementation of BaseComputerFile for Scrapybara computer files.

    This class provides a file-like interface for working with files on a remote computer
    accessed via Scrapybara. It uses temporary local files and Scrapybara's file transfer
    capabilities to provide file-like access.
    """


class ScrapybaraComputer(BaseComputer):
    """Environment that uses Scrapybara for secure computer interactions"""

    preferred_video_stream_mode: Literal["vnc", "http"] = "http"
    '''Used  to indicate which video stream mode is more efficient (ie, to avoid using proxy streams)'''

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.client = None

    def _start(self):
        """Start the Scrapybara environment."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                self.client = scrapybara.Client(api_key=self.api_key)
            else:
                self.client = scrapybara.Client()

            # Start a default Ubuntu instance
            self.client = self.client.start_ubuntu()

    def _stop(self):
        """Stop the Scrapybara environment."""
        if self.client:
            self.client.stop()
            self.client = None

    def reset_state(self):
        """Reset the Scrapybara environment"""
        # For Scrapybara, it's more efficient to stop and restart
        self._stop()
        self._start()

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> Union[str, Image.Image, Path]:
        """Return a screenshot of the current state in the specified format."""
        response = self.client.screenshot()
        return process_screenshot(
            screenshot_data=response.base_64_image,
            output_format=format,
            input_format="base64",
            computer_name="scrapybara",
        )

    def _get_mouse_position(self) -> tuple[int, int]:
        """Return current mouse position."""
        # Get cursor position using Scrapybara
        response = self.client.computer(action="cursor_position")
        position = response.output

        # Parse the position string into x, y coordinates
        # The output is typically in the format "x: X, y: Y"
        x_str = position.split("x:")[1].split(",")[0].strip()
        y_str = position.split("y:")[1].strip()
        return (int(x_str), int(y_str))

    def _get_mouse_button_states(self) -> dict[str, bool]:
        """Return states of mouse buttons."""
        self.logger.debug("Scrapybara does not support getting mouse button states")
        raise NotImplementedError(
            "Scrapybara does not support getting mouse button states"
        )

    def _get_keyboard_key_states(self) -> dict[str, bool]:
        """Return states of keyboard keys."""
        self.logger.debug("Scrapybara does not support getting keyboard key states")
        raise NotImplementedError(
            "Scrapybara does not support getting keyboard key states"
        )

    def _shell(
        self, command: str, timeout: float | None = None, executable: str | None = None
    ):
        """Execute a system command in the Scrapybara VM."""
        # Use bash command for Ubuntu instances
        response = self.client.bash(command=command)

    def _keydown(self, key: KeyboardKey):
        """Execute key down for a keyboard key using Scrapybara."""
        # Scrapybara doesn't have separate key down/up methods
        # We'll use the key method with a press and hold approach
        key_str = keyboard_key_to_scrapybara(key)
        # Note: This is a limitation as Scrapybara doesn't support key down
        # without release
        self.client.computer(action="key", text=key_str)

    def _keyup(self, key: KeyboardKey):
        """Execute key release for a keyboard key using Scrapybara."""
        # Scrapybara doesn't have separate key down/up methods
        raise NotImplementedError("Scrapybara does not support key release actions")

    def _type(self, text: str):
        """Type text using Scrapybara."""
        self.client.computer(action="type", text=text)

    def _move(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to specified coordinates using Scrapybara."""
        self.client.computer(action="mouse_move", coordinate=[x, y])

    def _scroll(self, amount: float):
        """Scroll mouse using Scrapybara."""
        # Scrapybara scroll takes [x, y] coordinates for horizontal and vertical scrolling
        # Convert our amount to a vertical scroll (positive = down, negative =
        # up)
        x_scroll = 0
        y_scroll = int(amount)

        self.client.computer(action="scroll", coordinate=[x_scroll, y_scroll])

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using Scrapybara."""
        # Scrapybara doesn't have separate mouse down/up methods
        raise NotImplementedError(
            "Scrapybara does not support mouse button down actions"
        )

    def _mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using Scrapybara."""
        # Scrapybara doesn't have separate mouse down/up methods
        raise NotImplementedError("Scrapybara does not support mouse button up actions")

    def _click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a click action at the given coordinates using Scrapybara's click action."""
        # Scrapybara has a direct click action
        # First move to the position
        self.client.computer(action="mouse_move", coordinate=[x, y])

        # Then perform the appropriate click based on the button
        click_action = mouse_button_to_scrapybara(button)
        self.client.computer(action=click_action)

    def _keypress(self, key: KeyboardKey, duration: float = 0.1):
        """Execute pressing a keyboard key using Scrapybara's key action."""
        # Scrapybara uses the computer action with key
        scrapybara_key = keyboard_key_to_scrapybara(key)
        self.client.computer(action="key", text=scrapybara_key)

    def _hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey using Scrapybara's key action with combined keys."""
        # Combine keys with + for Scrapybara hotkey format
        hotkey = "+".join([keyboard_key_to_scrapybara(key) for key in keys])
        self.client.computer(action="key", text=hotkey)

    def _double_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
        double_click_interval_seconds: float = 0.1,
    ):
        """Execute a double click action at the given coordinates using Scrapybara's double click action."""
        # Move to position first
        self.client.computer(action="mouse_move", coordinate=[x, y])
        # Then double click
        self.client.computer(action="double_click")

    def _drag(
        self,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a drag action using Scrapybara's left_click_drag method."""
        # Move to the end position
        self.client.computer(action="left_click_drag", coordinate=[end_x, end_y])

    def _pause(self):
        """Implementation of pause functionality for Scrapybara."""
        if self.client:
            self.logger.info("Pausing Scrapybara instance")
            self.client.pause()
            self.logger.info("Scrapybara instance paused successfully")

    def _resume(self, timeout_hours: Optional[float] = None):
        """Implementation of resume functionality for Scrapybara.

        Args:
            timeout_hours: Optional timeout in hours after which the instance will automatically pause again.
        """
        if self.client:
            self.logger.info("Resuming Scrapybara instance")
            if timeout_hours:
                self.client.resume(timeout_hours=timeout_hours)
            else:
                self.client.resume()
            self.logger.info("Scrapybara instance resumed successfully")

    def _get_http_video_stream_url(self) -> str:
        """Get the URL for the video stream of the Scrapybara instance.

        Returns:
            str: The URL for the video stream, or an empty string if video streaming is not available.
        """
        return self.client.get_stream_url()

    def _start_http_video_stream(
        self,
        host: str = 'localhost',
        port: int = 8080,
        frame_rate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg"
    ):
        """Start the video stream for the Scrapybara instance.

        Args:
            host: HTTP server host address
            port: HTTP server port
            frame_rate: Target frame rate for the video stream
            quality: JPEG/PNG compression quality (0-100)
            scale: Scale factor for the video stream (0.1-1.0)
            compression: Image compression format to use
        """
        if not self.client:
            self.logger.warning(
                "Cannot start video stream: Scrapybara client not initialized"
            )
            raise RuntimeError("Scrapybara client not initialized")

        self.client.start_stream()

    def _stop_http_video_stream(self):
        """Stop the video stream for the Scrapybara instance."""
        if not self.client:
            self.logger.warning(
                "Cannot stop video stream: Scrapybara client not initialized"
            )
            raise RuntimeError("Scrapybara client not initialized")
        self.client.stop_stream()

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ):
        """Run a process with the specified parameters.

        This method uses the Scrapybara API to run a process in the VM.

        Args:
            command: The command to run
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables for the process
            timeout: Timeout in seconds
        """
        self.logger.info(f"Running process via Scrapybara: {command} with args: {args}")
        self._default_run_process(
            command=command, args=args, cwd=cwd, env=env, timeout=timeout
        )

    def _open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ) -> ScrapybaraComputerFile:
        """Open a file on the remote computer.

        This method uses Scrapybara's capabilities to provide file-like access
        to files on the remote computer.

        Args:
            path: Path to the file on the remote computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            A ScrapybaraComputerFile instance for the specified file
        """
        return ScrapybaraComputerFile(
            computer=self,
            path=path,
            mode=mode,
            encoding=encoding,
            errors=errors,
            buffering=buffering,
        )


class UbuntuScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara computer specifically for Ubuntu instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _start(self):
        """Start an Ubuntu Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                client = scrapybara.Client(api_key=self.api_key)
            else:
                client = scrapybara.Client()

            # Start an Ubuntu instance
            self.client = client.start_ubuntu()

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executable: Optional[str] = None,
    ):
        """Execute a bash command in the Ubuntu instance."""
        response = self.client.bash(command=command)

    def edit_file(self, path: str, command: str, **kwargs):
        """Edit a file on the Ubuntu instance.

        Args:
            path: Path to the file
            command: Content to write to the file
            **kwargs: Additional arguments to pass to the edit method
        """
        self.client.edit(path=path, command=command, **kwargs)


class BrowserScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara computer specifically for Browser instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.client = None

    def _start(self):
        """Start a Browser Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                self.client = scrapybara.Client(api_key=self.api_key)
            else:
                self.client = scrapybara.Client()

            # Start a Browser instance
            self.client = self.client.start_browser()

    def get_cdp_url(self) -> str:
        """Get the Playwright CDP URL for the browser instance."""
        response = self.client.get_cdp_url()
        return response.cdp_url

    def save_auth(self, name: str = "default") -> str:
        """Save the current browser authentication state.

        Args:
            name: Name to identify the saved auth state

        Returns:
            The auth state ID that can be used to restore this state
        """
        response = self.client.save_auth(name=name)
        return response.auth_state_id

    def authenticate(self, auth_state_id: str):
        """Authenticate the browser using a saved auth state.

        Args:
            auth_state_id: The ID of the saved auth state to restore
        """
        self.client.authenticate(auth_state_id=auth_state_id)

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executable: Optional[str] = None,
    ):
        """Execute a command in the browser instance.

        Note: Browser instances don't support bash commands directly.
        This is a limitation of the browser-only environment.
        """
        self.logger.warning("Browser instances don't support direct command execution")
        raise NotImplementedError(
            "Browser instances don't support direct command execution"
        )


class WindowsScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara computer specifically for Windows instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _start(self):
        """Start a Windows Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                client = scrapybara.Client(api_key=self.api_key)
            else:
                client = scrapybara.Client()

            # Start a Windows instance
            self.client = client.start_windows()

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executable: Optional[str] = None,
    ):
        """Execute a command in the Windows instance.

        Note: Windows instances don't support bash commands directly.
        This implementation uses computer actions to open cmd and type commands.
        """
        # Open Windows Run dialog
        self.client.computer(action="key", text="meta+r")
        self.client.computer(action="wait")  # Wait for Run dialog to open

        # Type cmd and press Enter
        self.client.computer(action="type", text="cmd")
        self.client.computer(action="key", text="enter")
        self.client.computer(action="wait")  # Wait for cmd to open

        # Type the command and press Enter
        self.client.computer(action="type", text=command)
        self.client.computer(action="key", text="enter")

        # Wait for command to complete if timeout is specified
        if timeout:
            self.client.computer(action="wait")
