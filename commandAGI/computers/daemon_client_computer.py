import base64
import datetime
import io
import logging
import os
import platform
import subprocess
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Literal, Optional, Union

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import base64_to_image, process_screenshot
from commandAGI.computers.base_computer import BaseComputer, BaseComputerFile
from commandAGI.computers.computer_clients.base_computer_client import (
    BaseComputerComputerClient,
)
from commandAGI.types import (
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
    SystemInfo,
    TypeAction,
)

# Import the proper client classes
try:
    from commandAGI.daemon.client import AuthenticatedClient
    from commandAGI.daemon.client.api.default.execute_command_execute_command_post import (
        sync as execute_command_sync,
    )
    from commandAGI.daemon.client.api.default.hotkey_hotkey_post import (
        sync as hotkey_sync,
    )
    from commandAGI.daemon.client.api.default.keydown_keydown_post import (
        sync as keydown_sync,
    )
    from commandAGI.daemon.client.api.default.keypress_keypress_post import (
        sync as keypress_sync,
    )
    from commandAGI.daemon.client.api.default.keyup_keyup_post import (
        sync as keyup_sync,
    )
    from commandAGI.daemon.client.api.default.mouse_down_mouse_down_post import (
        sync as mouse_down_sync,
    )
    from commandAGI.daemon.client.api.default.mouse_up_mouse_up_post import (
        sync as mouse_up_sync,
    )
    from commandAGI.daemon.client.api.default.move_move_post import (
        sync as move_sync,
    )
    from commandAGI.daemon.client.api.default.scroll_scroll_post import (
        sync as scroll_sync,
    )
    from commandAGI.daemon.client.api.default.execute_run_process_execute_run_process_post import (
        sync as run_process_sync,
    )
    from commandAGI.daemon.client.api.default.type_type_post import (
        sync as type_sync,
    )
    from commandAGI.daemon.client.api.default.get_keyboard_state_observation_keyboard_state_get import (
        sync as get_keyboard_state_sync,
    )
    from commandAGI.daemon.client.api.default.get_mouse_state_observation_mouse_state_get import (
        sync as get_mouse_state_sync,
    )
    from commandAGI.daemon.client.api.default.get_observation_observation_get import (
        sync as get_observation_sync,
    )
    from commandAGI.daemon.client.api.default.get_screenshot_observation_screenshot_get import (
        sync as get_screenshot_sync,
    )
    from commandAGI.daemon.client.api.default.get_video_stream_url_video_stream_url_get import (
        sync as get_video_stream_url_sync,
    )
    from commandAGI.daemon.client.api.default.reset_reset_post import sync as reset_sync
    from commandAGI.daemon.client.api.default.start_video_stream_video_start_stream_post import (
        sync as start_video_stream_sync,
    )
    from commandAGI.daemon.client.api.default.stop_video_stream_video_stop_stream_post import (
        sync as stop_video_stream_sync,
    )
    from commandAGI.daemon.client.models import (
        KeyboardHotkeyAction as ClientKeyboardHotkeyAction,
    )
    from commandAGI.daemon.client.models import KeyboardKey as ClientKeyboardKey
    from commandAGI.daemon.client.models import (
        KeyboardKeyDownAction as ClientKeyboardKeyDownAction,
    )
    from commandAGI.daemon.client.models import (
        KeyboardKeyPressAction as ClientKeyboardKeyPressAction,
    )
    from commandAGI.daemon.client.models import (
        KeyboardKeyReleaseAction as ClientKeyboardKeyReleaseAction,
    )
    from commandAGI.daemon.client.models import MouseButton as ClientMouseButton
    from commandAGI.daemon.client.models import (
        MouseButtonDownAction as ClientMouseButtonDownAction,
    )
    from commandAGI.daemon.client.models import (
        MouseButtonUpAction as ClientMouseButtonUpAction,
    )
    from commandAGI.daemon.client.models import MouseMoveAction as ClientMouseMoveAction
    from commandAGI.daemon.client.models import (
        MouseScrollAction as ClientMouseScrollAction,
    )
    from commandAGI.daemon.client.models import (
        RunProcessAction as ClientRunProcessAction,
    )
    from commandAGI.daemon.client.models import (
        ShellCommandAction as ClientShellCommandAction,
    )
    from commandAGI.daemon.client.models import TypeAction as ClientTypeAction
    from commandAGI.daemon.client.models import (
        VideoStartStreamAction as ClientVideoStartStreamAction,
    )
    from commandAGI.daemon.client.models import (
        VideoStopStreamAction as ClientVideoStopStreamAction,
    )
except ImportError:
    raise ImportError(
        "commandAGI daemon client is not installed. Please install commandAGI with the daemon extra:\n\npip install commandAGI[daemon-client-all] (or one of the other `daemon-client-*` extras)"
    )

try:
    from PIL import Image
except ImportError:
    pass  # PIL is optional for DaemonClientComputer


# Daemon client-specific mappings
def keyboard_key_to_daemon(key: Union[KeyboardKey, str]) -> ClientKeyboardKey:
    """Convert KeyboardKey to Daemon client KeyboardKey.

    The daemon client uses its own KeyboardKey enum that should match our KeyboardKey values.
    This function ensures proper conversion between the two.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # The daemon client's KeyboardKey enum should have the same values as our KeyboardKey enum
    # We just need to convert to the client's enum type
    try:
        return ClientKeyboardKey(key.value)
    except ValueError:
        # If the key value doesn't exist in the client's enum, use a fallback
        logging.warning(
            f"Key {key} not found in daemon client KeyboardKey enum, using fallback"
        )
        return ClientKeyboardKey.ENTER  # Use a safe default


def mouse_button_to_daemon(button: Union[MouseButton, str]) -> ClientMouseButton:
    """Convert MouseButton to Daemon client MouseButton.

    The daemon client uses its own MouseButton enum that should match our MouseButton values.
    This function ensures proper conversion between the two.
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # The daemon client's MouseButton enum should have the same values as our MouseButton enum
    # We just need to convert to the client's enum type
    try:
        return ClientMouseButton(button.value)
    except ValueError:
        # If the button value doesn't exist in the client's enum, use a
        # fallback
        logging.warning(
            f"Button {button} not found in daemon client MouseButton enum, using fallback"
        )
        return ClientMouseButton.LEFT  # Use a safe default


class DaemonClientComputerFile(BaseComputerFile):
    """Implementation of BaseComputerFile for Daemon Client computer files.

    This class provides a file-like interface for working with files on a remote computer
    accessed via the Daemon Client. It uses temporary local files and the daemon's file
    transfer capabilities to provide file-like access.
    """


class DaemonClientComputer(BaseComputer):
    computer_client: Optional[BaseComputerComputerClient] = None
    client: Optional[AuthenticatedClient] = None
    logger: Optional[logging.Logger] = None
    daemon_token: str = ""

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        computer_client: BaseComputerComputerClient,
        daemon_token: Optional[str] = None,
    ):
        # First call super().__init__() to initialize the Pydantic model
        super().__init__()

        # Now it's safe to set attributes
        self.logger = logging.getLogger(__name__)

        # Store the computer_client
        self.computer_client = computer_client

        # Use the provided token or get it from the computer_client
        self.daemon_token = daemon_token or self.computer_client.daemon_token

        # Setup the computer_client
        self.logger.info(
            f"Starting daemon services at {
                self.computer_client.daemon_url}"
        )
        self.computer_client.setup()

        # Create the authenticated client
        self.client = AuthenticatedClient(
            base_url=self.computer_client.daemon_url,
            token=self.daemon_token,
        )
        self.logger.info(
            f"Successfully connected to daemon services at {
                self.computer_client.daemon_url}"
        )

    def _start(self):
        """Start the daemon services"""
        if not self.client:
            self.logger.info(
                f"Starting daemon at {
                    self.computer_client.daemon_url}"
            )
            self.computer_client.setup()

            # Create the authenticated client
            self.client = AuthenticatedClient(
                base_url=self.computer_client.daemon_url,
                token=self.daemon_token,
            )
            self.logger.info(
                f"Successfully connected to daemon services at {
                    self.computer_client.daemon_url}"
            )
        return True

    def _stop(self):
        """Stop the daemon services"""
        if self.client:
            self.logger.info("Shutting down daemon services")
            self.computer_client.teardown()
            self.client = None
            self.logger.info("Daemon services successfully stopped")
        return True

    def reset_state(self) -> bool:
        """Reset the computer state"""
        return super().reset_state()

    def get_observation(self) -> Dict[str, Any]:
        """Get a complete observation of the computer state"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = get_observation_sync(client=self.client)
        return response if response else {}

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> Union[str, Image.Image, Path]:
        """Get a screenshot of the computer in the specified format.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        # Get the screenshot from the daemon (usually returns base64)
        response = get_screenshot_sync(client=self.client)
        if not response or "screenshot" not in response:
            raise RuntimeError("Failed to get screenshot from daemon")

        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=response["screenshot"],
            output_format=format,
            input_format="base64",
            computer_name="daemon",
        )

    def _get_mouse_position(self) -> tuple[int, int]:
        """Get the current mouse cursor position.

        Returns:
            tuple[int, int]: The x,y coordinates of the mouse cursor
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = get_mouse_state_sync(client=self.client)
        if not response or "position" not in response:
            raise RuntimeError("Failed to get mouse position from daemon")
        return (response["position"]["x"], response["position"]["y"])

    def _get_mouse_button_states(self) -> dict[str, bool]:
        """Get the current state of mouse buttons.

        Returns:
            dict[str, bool]: Dictionary mapping button names to pressed state
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = get_mouse_state_sync(client=self.client)
        if not response or "buttons" not in response:
            raise RuntimeError("Failed to get mouse button states from daemon")
        return response["buttons"]

    def _get_keyboard_key_states(self) -> dict[str, bool]:
        """Get the current state of keyboard keys.

        Returns:
            dict[str, bool]: Dictionary mapping key names to pressed state
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = get_keyboard_state_sync(client=self.client)
        if not response or "keys" not in response:
            raise RuntimeError("Failed to get keyboard key states from daemon")
        return response["keys"]

    def _get_sysinfo(self) -> SystemInfo:
        """Get system information from daemon client."""
        response = self.client.get_sysinfo()
        if response:
            return SystemInfo(**response)

        raise RuntimeError("Failed to get system info from daemon")

    def _shell(self, command: str, timeout: Optional[float] = None):
        """Execute a shell command on the computer"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientShellCommandAction(command=command, timeout=timeout)

        response = execute_command_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute command: {command}")

    def _keydown(self, key: KeyboardKey):
        """Press down a keyboard key"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientKeyboardKeyDownAction(key=keyboard_key_to_daemon(key))

        response = keydown_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute keyboard key down: {key}")

    def _keyup(self, key: KeyboardKey):
        """Release a keyboard key"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientKeyboardKeyReleaseAction(key=keyboard_key_to_daemon(key))

        response = keyup_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute keyboard key release: {key}")

    def _keypress(self, key: KeyboardKey, duration: float = 0.1):
        """Press and release a keyboard key"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientKeyboardKeyPressAction(
            key=keyboard_key_to_daemon(key), duration=duration
        )

        response = keypress_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute keyboard key press: {key}")

    def _hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey (multiple keys pressed simultaneously)"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientKeyboardHotkeyAction(
            keys=[keyboard_key_to_daemon(k) for k in keys]
        )

        response = hotkey_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute keyboard hotkey: {keys}")

    def _type(self, text: str):
        """Type text on the keyboard"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientTypeAction(text=text)

        response = type_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute type: {text}")

    def _move(self, x: int, y: int, duration: float = 0.5):
        """Move the mouse to a position"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientMouseMoveAction(x=x, y=y, move_duration=move_duration)

        response = move_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute mouse move to ({x}, {y})")

    def _scroll(self, amount: float):
        """Scroll the mouse wheel"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientMouseScrollAction(amount=amount)

        response = scroll_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute mouse scroll: {amount}")

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Press down a mouse button"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientMouseButtonDownAction(
            button=mouse_button_to_daemon(button) if button else None
        )

        response = mouse_down_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute mouse button down: {button}")

    def _mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Release a mouse button"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        client_action = ClientMouseButtonUpAction(
            button=mouse_button_to_daemon(button) if button else None
        )

        response = mouse_up_sync(client=self.client, body=client_action)
        if not response or not response.success:
            raise RuntimeError(f"Failed to execute mouse button up: {button}")

    def _pause(self):
        """Pause the daemon client computer.

        For daemon client, pausing means sending a pause command to the daemon.
        """
        # TODO: implement specifically for the system in mind

    def _resume(self, timeout_hours: Optional[float] = None):
        """Resume the daemon client computer.

        For daemon client, resuming means sending a resume command to the daemon.

        Args:
            timeout_hours: Optional timeout in hours after which the computer will automatically pause again.
        """
        # TODO: implement specifically for the system in mind

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the daemon client instance.

        Returns:
            str: The URL for the video stream, or an empty string if video streaming is not available.
        """
        response = get_video_stream_url_sync(client=self.client)
        if not response or not response.url:
            raise RuntimeError("Failed to get video stream URL from daemon")
        return response.url

    def start_video_stream(self):
        """Start the video stream for the daemon client instance."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = start_video_stream_sync(
            client=self.client, body=ClientVideoStartStreamAction()
        )
        if not response or not response.success:
            raise RuntimeError("Failed to start video stream")
        return True

    def stop_video_stream(self):
        """Stop the video stream for the daemon client instance."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = stop_video_stream_sync(
            client=self.client, body=ClientVideoStopStreamAction()
        )
        return response.success if response else False

    def _run_process(
        self,
        command: str,
        args: List[str] = None,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Run a process with the specified parameters.

        This method uses the daemon client API to execute a process on the remote system.

        Args:
            command: The command to execute
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables for the process
            timeout: Timeout in seconds

        Returns:
            str: The output of the process
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        args = args or []
        response = run_process_sync(
            client=self.client,
            body=ClientRunProcessAction(command=command, args=args),
        )
        if not response or not response.output:
            raise RuntimeError("Failed to run process")
        return response.output

    def _open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ) -> DaemonClientComputerFile:
        """Open a file on the remote computer.

        This method uses the Daemon Client API to access files on the remote computer.
        Note: File operations may not be implemented in the current Daemon Client API.

        Args:
            path: Path to the file on the remote computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            A DaemonClientComputerFile instance for the specified file
        """
        return DaemonClientComputerFile(
            computer=self,
            path=path,
            mode=mode,
            encoding=encoding,
            errors=errors,
            buffering=buffering,
        )
