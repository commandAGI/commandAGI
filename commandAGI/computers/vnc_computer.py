import base64
import datetime
import io
import os
import tempfile
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Literal, Optional, Union

try:
    import vncdotool.api as vnc
    from PIL import Image

    # Try to import paramiko for SFTP file transfer
    try:
        import paramiko

        SFTP_AVAILABLE = True
    except ImportError:
        SFTP_AVAILABLE = False
except ImportError:
    raise ImportError(
        "The VNC dependencies are not installed. Please install commandAGI with the vnc extra:\n\npip install commandAGI[vnc]"
    )

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI.computers.base_computer import BaseComputer, BaseComputerFile
from commandAGI.types import (
    KeyboardKey,
    KeyboardKeyDownAction,
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


# VNC-specific mappings
def mouse_button_to_vnc(button: Union[MouseButton, str]) -> int:
    """Convert MouseButton to VNC mouse button code.

    VNC uses integers for mouse buttons:
    1 = left button
    2 = middle button
    3 = right button
    4 = wheel up
    5 = wheel down
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # VNC mouse button mapping
    vnc_button_mapping = {
        MouseButton.LEFT: 1,
        MouseButton.MIDDLE: 2,
        MouseButton.RIGHT: 3,
    }

    # Default to left button if not found
    return vnc_button_mapping.get(button, 1)


def keyboard_key_to_vnc(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to VNC key name.

    VNC uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # VNC-specific key mappings
    vnc_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "return",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "escape",
        KeyboardKey.HOME: "home",
        KeyboardKey.END: "end",
        KeyboardKey.PAGE_UP: "page_up",
        KeyboardKey.PAGE_DOWN: "page_down",
        # Arrow keys
        KeyboardKey.UP: "up",
        KeyboardKey.DOWN: "down",
        KeyboardKey.LEFT: "left",
        KeyboardKey.RIGHT: "right",
        # Modifier keys
        KeyboardKey.SHIFT: "shift",
        KeyboardKey.CTRL: "control",
        KeyboardKey.LCTRL: "control",
        KeyboardKey.RCTRL: "control",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "meta",
        KeyboardKey.LMETA: "meta",
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
    return vnc_key_mapping.get(key, key.value)


class VNCComputerFile(BaseComputerFile):
    """Implementation of BaseComputerFile for VNC computer files.

    This class provides a file-like interface for working with files on a remote computer
    accessed via VNC. It uses SFTP for file operations when available.
    """


class VNCComputer(BaseComputer):
    """Environment that uses VNC for remote computer interactions

    This class provides functionality to interact with a remote computer via VNC.
    It also supports file transfer via SFTP if the paramiko library is installed.

    Attributes:
        host: Hostname or IP address of the VNC server
        port: Port number of the VNC server (default: 5900)
        password: Password for VNC authentication (optional)
        ssh_host: Hostname or IP address for SSH/SFTP connection (defaults to VNC host)
        ssh_port: Port number for SSH/SFTP connection (default: 22)
        ssh_username: Username for SSH/SFTP authentication
        ssh_password: Password for SSH/SFTP authentication (optional if ssh_key_path is provided)
        ssh_key_path: Path to SSH private key file (optional if ssh_password is provided)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5900,
        password: Optional[str] = None,
        ssh_host: Optional[str] = None,
        ssh_port: int = 22,
        ssh_username: Optional[str] = None,
        ssh_password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
    ):
        """Initialize a VNC computer connection.

        Args:
            host: Hostname or IP address of the VNC server
            port: Port number of the VNC server (default: 5900)
            password: Password for VNC authentication (optional)
            ssh_host: Hostname or IP address for SSH/SFTP connection (defaults to VNC host)
            ssh_port: Port number for SSH/SFTP connection (default: 22)
            ssh_username: Username for SSH/SFTP authentication
            ssh_password: Password for SSH/SFTP authentication (optional if ssh_key_path is provided)
            ssh_key_path: Path to SSH private key file (optional if ssh_password is provided)
        """
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.client = None

        # SSH parameters for file transfer
        self.ssh_host = ssh_host if ssh_host is not None else host
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_key_path = ssh_key_path

    def _start(self):
        """Start the VNC connection."""
        if not self.client:
            connection_string = f"{self.host}::{self.port}"
            self.logger.info(f"Connecting to VNC server at {connection_string}")
            self.client = vnc.connect(connection_string, password=self.password)
            self.logger.info(f"Successfully connected to VNC server")

    def _stop(self):
        """Stop the VNC connection."""
        if self.client:
            self.logger.info(f"Disconnecting from VNC server")
            self.client.disconnect()
            self.client = None
            self.logger.info(f"Successfully disconnected from VNC server")

    def reset_state(self):
        """Reset the VNC connection"""
        self.logger.info(f"Resetting VNC connection")
        self._stop()
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
        # Capture the screenshot using vncdotool
        self.logger.debug(f"Capturing VNC screenshot")
        png_data = self.client.capture()

        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=png_data,
            output_format=format,
            input_format="bytes",
            computer_name="vnc",
        )

    def _get_mouse_position(self) -> tuple[int, int]:
        """Return current mouse position."""
        self.logger.debug("VNC does not support getting mouse position")
        raise NotImplementedError("VNC does not support getting mouse position")

    def _get_mouse_button_states(self) -> dict[str, bool]:
        """Return states of mouse buttons."""
        self.logger.debug("VNC does not support getting mouse button states")
        raise NotImplementedError("VNC does not support getting mouse button states")

    def _get_keyboard_key_states(self) -> dict[str, bool]:
        """Return states of keyboard keys."""
        self.logger.debug("VNC does not support getting keyboard key states")
        raise NotImplementedError("VNC does not support getting keyboard key states")

    def _execute_shell_command(self, command: str, timeout: float | None = None, executable: str | None = None):
        """Execute a system command on the remote system.

        Note: This is limited by VNC capabilities and may not work for all commands.
        """
        self.logger.info(f"Executing command via VNC: {command}")
        # For VNC, we can try to execute commands by opening a terminal and typing
        # This is a simplified approach and may not work in all environments
        self.client.keyPress("windown")  # Open start menu or equivalent
        self.client.pause(0.5)
        self.client.type("terminal")  # Type 'terminal' to search for terminal
        self.client.pause(0.5)
        self.client.keyPress("enter")  # Open terminal
        self.client.pause(1.0)
        self.client.type(command)  # Type the command
        self.client.keyPress("enter")  # Execute the command

        # Wait for command to complete if timeout is specified
        if timeout is not None:
            self.client.pause(timeout)

        self.logger.info(f"Command executed successfully")

    def _execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key using VNC."""
        vnc_key = keyboard_key_to_vnc(key)
        self.logger.debug(f"Pressing key down: {key} (VNC key: {vnc_key})")
        self.client.keyDown(vnc_key)

    def _execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key using VNC."""
        vnc_key = keyboard_key_to_vnc(key)
        self.logger.debug(f"Releasing key: {key} (VNC key: {vnc_key})")
        self.client.keyUp(vnc_key)

    def _execute_type(self, text: str):
        """Type text using VNC."""
        self.logger.debug(f"Typing text: {text}")
        self.client.type(text)

    def _execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5):
        """Move mouse to specified coordinates using VNC."""
        self.logger.debug(f"Moving mouse to: ({x}, {y})")
        # VNC doesn't have a direct move duration parameter, so we just move
        self.client.mouseMove(x, y)

    def _execute_mouse_scroll(self, amount: float):
        """Scroll mouse using VNC."""
        self.logger.debug(f"Scrolling mouse by: {amount}")
        # VNC scroll is typically done by wheel events
        # Positive values scroll up, negative values scroll down
        if amount > 0:
            for _ in range(int(abs(amount))):
                self.client.mouseWheel(1)  # Scroll up
        else:
            for _ in range(int(abs(amount))):
                self.client.mouseWheel(-1)  # Scroll down

    def _execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using VNC."""
        vnc_button = mouse_button_to_vnc(button)
        self.logger.debug(f"Pressing mouse button down: {button} (VNC button: {vnc_button})")
        self.client.mouseDown(vnc_button)

    def _execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using VNC."""
        vnc_button = mouse_button_to_vnc(button)
        self.logger.debug(f"Releasing mouse button: {button} (VNC button: {vnc_button})")
        self.client.mouseUp(vnc_button)

    def _pause(self):
        """Pause the VNC connection.

        For VNC, pausing means disconnecting but keeping the client object.
        """
        if self.client:
            self.logger.info("Pausing VNC connection")
            self.client.disconnect()
            self.logger.info("VNC connection paused")

    def _resume(self, timeout_hours: Optional[float] = None):
        """Resume the VNC connection.

        For VNC, resuming means reconnecting if the client was disconnected.

        Args:
            timeout_hours: Not used for VNC implementation.
        """
        if self.client:
            self.logger.info("Resuming VNC connection")
            connection_string = f"{self.host}::{self.port}"
            self.client = vnc.connect(connection_string, password=self.password)
            self.logger.info("VNC connection resumed")

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the VNC instance.

        VNC does not provide a direct video stream URL in this implementation.

        Returns:
            str: Empty string as VNC streaming is not implemented in this way.
        """
        self.logger.debug("Video streaming URL not available for VNC")
        return ""

    def start_video_stream(self) -> bool:
        """Start the video stream for the VNC instance.

        VNC does not support direct video streaming in this implementation.

        Returns:
            bool: False as VNC streaming is not implemented.
        """
        self.logger.debug("Video streaming not implemented for VNC")
        return False

    def stop_video_stream(self) -> bool:
        """Stop the video stream for the VNC instance.

        VNC does not support direct video streaming in this implementation.

        Returns:
            bool: False as VNC streaming is not implemented.
        """
        self.logger.debug("Video streaming not implemented for VNC")
        return False

    def _run_process(self, action: RunProcessAction) -> bool:
        """Run a process with the specified parameters.

        For VNC, we'll use the default implementation that relies on shell commands
        since VNC doesn't have direct process execution capabilities.

        Args:
            action: RunProcessAction containing the process parameters

        Returns:
            bool: True if the process was executed successfully
        """
        self.logger.info(
            f"Running process via VNC shell: {
                action.command} with args: {
                action.args}"
        )
        return self._default_run_process(action=action)

    def _copy_to_computer(self, source_path: Path, destination_path: Path) -> None:
        """Implementation of copy_to_computer functionality for VNCComputer.

        For VNC computers, we attempt to use SFTP if available, since VNC itself
        doesn't support file transfer. This requires paramiko to be installed and
        SSH/SFTP to be available on the remote system.

        Args:
            source_path: Path to the source file or directory on the local machine
            destination_path: Path where the file or directory should be copied on the computer

        Raises:
            NotImplementedError: If SFTP is not available (paramiko not installed)
            FileNotFoundError: If the source path does not exist
            ValueError: If SSH credentials are not properly configured
            PermissionError: If there are permission issues with SSH/SFTP
            OSError: For other file operation errors
        """
        if not SFTP_AVAILABLE:
            self.logger.warning(
                "SFTP not available. Install paramiko to enable file transfer."
            )
            raise NotImplementedError(
                "File transfer not supported without paramiko installed. Run: pip install paramiko"
            )

        # Ensure source exists
        if not source_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {source_path}")

        # Verify SSH credentials are configured
        if not self.ssh_username:
            raise ValueError(
                "SSH username not provided. Set ssh_username when initializing VNCComputer."
            )

        if not self.ssh_password and not self.ssh_key_path:
            raise ValueError(
                "Either ssh_password or ssh_key_path must be provided for SFTP file transfer."
            )

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to SSH server
            self.logger.debug(
                f"Connecting to SSH server {
                    self.ssh_host}:{
                    self.ssh_port} as {
                    self.ssh_username}"
            )
            if self.ssh_key_path:
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    key_filename=self.ssh_key_path,
                )
            else:
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    password=self.ssh_password,
                )

            # Create SFTP client
            sftp = ssh.open_sftp()

            # Create parent directories if they don't exist
            try:
                sftp.mkdir(str(destination_path.parent))
            except IOError:
                # Directory might already exist
                pass

            # Copy file or directory
            if source_path.is_dir():
                # Create destination directory if it doesn't exist
                try:
                    sftp.mkdir(str(destination_path))
                except IOError:
                    # Directory might already exist
                    pass

                # Recursively copy directory contents
                for item in source_path.iterdir():
                    if item.is_dir():
                        # Recursively call this method for subdirectories
                        self._copy_to_computer(item, destination_path / item.name)
                    else:
                        # Copy file
                        sftp.put(str(item), str(destination_path / item.name))
            else:
                # Copy a single file
                sftp.put(str(source_path), str(destination_path))

            sftp.close()
            ssh.close()

        except paramiko.AuthenticationException as e:
            self.logger.error(f"SSH authentication failed: {e}")
            raise ValueError(
                f"SSH authentication failed: {e}. Check your ssh_username, ssh_password, or ssh_key_path."
            )
        except paramiko.SSHException as e:
            self.logger.error(f"SSH connection error: {e}")
            raise ConnectionError(
                f"SSH connection error: {e}. Check your ssh_host and ssh_port."
            )
        except Exception as e:
            self.logger.error(f"Error during SFTP transfer: {e}")
            raise

    def _copy_from_computer(self, source_path: Path, destination_path: Path) -> None:
        """Implementation of copy_from_computer functionality for VNCComputer.

        For VNC computers, we attempt to use SFTP if available, since VNC itself
        doesn't support file transfer. This requires paramiko to be installed and
        SSH/SFTP to be available on the remote system.

        Args:
            source_path: Path to the source file or directory on the computer
            destination_path: Path where the file or directory should be copied on the local machine

        Raises:
            NotImplementedError: If SFTP is not available (paramiko not installed)
            FileNotFoundError: If the source path does not exist on the remote computer
            ValueError: If SSH credentials are not properly configured
            PermissionError: If there are permission issues with SSH/SFTP
            OSError: For other file operation errors
        """
        if not SFTP_AVAILABLE:
            self.logger.warning(
                "SFTP not available. Install paramiko to enable file transfer."
            )
            raise NotImplementedError(
                "File transfer not supported without paramiko installed. Run: pip install paramiko"
            )

        # Verify SSH credentials are configured
        if not self.ssh_username:
            raise ValueError(
                "SSH username not provided. Set ssh_username when initializing VNCComputer."
            )

        if not self.ssh_password and not self.ssh_key_path:
            raise ValueError(
                "Either ssh_password or ssh_key_path must be provided for SFTP file transfer."
            )

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to SSH server
            self.logger.debug(
                f"Connecting to SSH server {
                    self.ssh_host}:{
                    self.ssh_port} as {
                    self.ssh_username}"
            )
            if self.ssh_key_path:
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    key_filename=self.ssh_key_path,
                )
            else:
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    password=self.ssh_password,
                )

            # Create SFTP client
            sftp = ssh.open_sftp()

            # Create parent directories if they don't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if source exists
            try:
                sftp.stat(str(source_path))
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Source path does not exist on remote computer: {source_path}"
                )

            # Copy file or directory
            try:
                # Check if source is a directory by trying to list its contents
                sftp.listdir(str(source_path))
                is_dir = True
            except IOError:
                is_dir = False

            if is_dir:
                # Create destination directory if it doesn't exist
                destination_path.mkdir(exist_ok=True)

                # Recursively copy directory contents
                for item in sftp.listdir(str(source_path)):
                    remote_item_path = source_path / item
                    local_item_path = destination_path / item

                    try:
                        # Check if item is a directory
                        sftp.listdir(str(remote_item_path))
                        # Recursively call this method for subdirectories
                        self._copy_from_computer(remote_item_path, local_item_path)
                    except IOError:
                        # Item is a file
                        sftp.get(str(remote_item_path), str(local_item_path))
            else:
                # Copy a single file
                sftp.get(str(source_path), str(destination_path))

            sftp.close()
            ssh.close()

        except paramiko.AuthenticationException as e:
            self.logger.error(f"SSH authentication failed: {e}")
            raise ValueError(
                f"SSH authentication failed: {e}. Check your ssh_username, ssh_password, or ssh_key_path."
            )
        except paramiko.SSHException as e:
            self.logger.error(f"SSH connection error: {e}")
            raise ConnectionError(
                f"SSH connection error: {e}. Check your ssh_host and ssh_port."
            )
        except Exception as e:
            self.logger.error(f"Error during SFTP transfer: {e}")
            raise

    def _open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ) -> VNCComputerFile:
        """Open a file on the remote computer.

        This method uses SFTP to access files on the remote computer.

        Args:
            path: Path to the file on the remote computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            A VNCComputerFile instance for the specified file
        """
        return VNCComputerFile(
            computer=self,
            path=path,
            mode=mode,
            encoding=encoding,
            errors=errors,
            buffering=buffering,
        )
