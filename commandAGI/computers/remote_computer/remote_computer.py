import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from commandAGI._utils.image import process_screenshot
from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE
from commandAGI.computers.base_computer import BaseComputer
from commandAGI.computers.platform_managers.base_platform_manager import (
    BaseComputerPlatformManager,
)
from commandAGI.computers.remote_computer.applications.remote_background_shell import (
    RemoteBackgroundShell,
)
from commandAGI.computers.remote_computer.applications.remote_blender import (
    RemoteBlender,
)
from commandAGI.computers.remote_computer.applications.remote_chrome_browser import (
    RemoteChromeBrowser,
)
from commandAGI.computers.remote_computer.applications.remote_cursor_ide import (
    RemoteCursorIDE,
)
from commandAGI.computers.remote_computer.applications.remote_file_explorer import (
    RemoteFileExplorer,
)
from commandAGI.computers.remote_computer.applications.remote_freecad import (
    RemoteFreeCAD,
)
from commandAGI.computers.remote_computer.applications.remote_kdenlive import (
    RemoteKdenlive,
)
from commandAGI.computers.remote_computer.applications.remote_kicad import RemoteKicad
from commandAGI.computers.remote_computer.applications.remote_libre_office_calc import (
    RemoteLibreOfficeCalc,
)
from commandAGI.computers.remote_computer.applications.remote_libre_office_present import (
    RemoteLibreOfficePresent,
)
from commandAGI.computers.remote_computer.applications.remote_libre_office_writer import (
    RemoteLibreOfficeWriter,
)
from commandAGI.computers.remote_computer.applications.remote_microsoft_excel import (
    RemoteMicrosoftExcel,
)
from commandAGI.computers.remote_computer.applications.remote_microsoft_powerpoint import (
    RemoteMicrosoftPowerPoint,
)
from commandAGI.computers.remote_computer.applications.remote_microsoft_word import (
    RemoteMicrosoftWord,
)
from commandAGI.computers.remote_computer.applications.remote_paint_editor import (
    RemotePaintEditor,
)
from commandAGI.computers.remote_computer.applications.remote_shell import RemoteShell
from commandAGI.computers.remote_computer.applications.remote_text_editor import (
    RemoteTextEditor,
)
from commandAGI.computers.remote_computer.remote_subprocess import RemoteSubprocess
from commandAGI.types import (
    KeyboardKey,
    MouseButton,
    SystemInfo,
)

# Import the proper client classes
try:
    from commandAGI.daemon.client import AuthenticatedClient
    from commandAGI.daemon.client.api.default.execute_run_process_execute_run_process_post import (
        sync as run_process_sync,
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
    from commandAGI.daemon.client.api.default.hotkey_hotkey_post import (
        sync as hotkey_sync,
    )
    from commandAGI.daemon.client.api.default.keydown_keydown_post import (
        sync as keydown_sync,
    )
    from commandAGI.daemon.client.api.default.keypress_keypress_post import (
        sync as keypress_sync,
    )
    from commandAGI.daemon.client.api.default.keyup_keyup_post import sync as keyup_sync
    from commandAGI.daemon.client.api.default.mouse_down_mouse_down_post import (
        sync as mouse_down_sync,
    )
    from commandAGI.daemon.client.api.default.mouse_up_mouse_up_post import (
        sync as mouse_up_sync,
    )
    from commandAGI.daemon.client.api.default.move_move_post import sync as move_sync
    from commandAGI.daemon.client.api.default.scroll_scroll_post import (
        sync as scroll_sync,
    )
    from commandAGI.daemon.client.api.default.type_type_post import sync as type_sync
    from commandAGI.daemon.client.models import (
        KeyboardHotkeyAction as ClientKeyboardHotkeyAction,
    )
    from commandAGI.daemon.client.models import (
        KeyboardKeyDownAction as ClientKeyboardKeyDownAction,
    )
    from commandAGI.daemon.client.models import (
        KeyboardKeyPressAction as ClientKeyboardKeyPressAction,
    )
    from commandAGI.daemon.client.models import (
        KeyboardKeyReleaseAction as ClientKeyboardKeyReleaseAction,
    )
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
    from commandAGI.daemon.client.models import TypeAction as ClientTypeAction
except ImportError:
    raise ImportError(
        "commandAGI daemon client is not installed. Please install commandAGI with the daemon extra:\n\npip install commandAGI[daemon-client-all] (or one of the other `daemon-client-*` extras)"
    )

try:
    from PIL import Image
except ImportError:
    pass  # PIL is optional for Computer


class RemoteComputer(BaseComputer):
    platform_manager: Optional[BaseComputerPlatformManager] = None
    client: Optional[AuthenticatedClient] = None
    logger: Optional[logging.Logger] = None
    daemon_token: str = ""
    preferred_video_stream_mode: Literal["vnc", "http"] = "vnc"
    """Used  to indicate which video stream mode is more efficient (ie, to avoid using proxy streams)"""
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        platform_manager: BaseComputerPlatformManager,
        daemon_token: Optional[str] = None,
    ):
        # First call super().__init__() to initialize the Pydantic model
        super().__init__()

        # Now it's safe to set attributes
        self.logger = logging.getLogger(__name__)

        # Store the platform_manager
        self.platform_manager = platform_manager

        # Use the provided token or get it from the platform_manager
        self.daemon_token = daemon_token or self.platform_manager.daemon_token

        # Setup the platform_manager
        self.logger.info(
            f"Starting daemon services at {
                self.platform_manager.daemon_url}"
        )
        self.platform_manager.setup()

        # Create the authenticated client
        self.client = AuthenticatedClient(
            base_url=self.platform_manager.daemon_url,
            token=self.daemon_token,
        )
        self.logger.info(
            f"Successfully connected to daemon services at {
                self.platform_manager.daemon_url}"
        )

    def _start(self):
        """Start the daemon services"""
        if not self.client:
            self.logger.info(
                f"Starting daemon at {
                    self.platform_manager.daemon_url}"
            )
            self.platform_manager.setup()

            # Create the authenticated client
            self.client = AuthenticatedClient(
                base_url=self.platform_manager.daemon_url,
                token=self.daemon_token,
            )
            self.logger.info(
                f"Successfully connected to daemon services at {
                    self.platform_manager.daemon_url}"
            )

    def _stop(self):
        """Stop the daemon services"""
        if self.client:
            self.logger.info("Shutting down daemon services")
            self.platform_manager.teardown()
            self.client = None
            self.logger.info("Daemon services successfully stopped")

    def reset_state(self):
        """Reset the computer state"""
        super().reset_state()

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

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> RemoteSubprocess:
        """Run a process with the specified parameters.

        Args:
            command: The command to run
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables for the process
            timeout: Optional timeout in seconds
        """
        raise NotImplementedError(f"{self.__class__.__name__}._run_process")

    def _start_shell(
        self,
        executable: str = None,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> RemoteShell:
        raise NotImplementedError(f"{self.__class__.__name__}.start_shell")

    def _start_background_shell(
        self,
        executable: str = None,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> RemoteBackgroundShell:
        """Create and return a new remote background shell instance.

        Args:
            executable: Path to the shell executable to use
            cwd: Initial working directory for the shell
            env: Environment variables to set in the shell

        Returns:
            RemoteBackgroundShell: A background shell instance for executing background commands
        """
        return RemoteBackgroundShell(
            executable=executable or DEFAULT_SHELL_EXECUTIBLE,
            cwd=cwd,
            env=env,
            logger=self.logger,
        )

    def _start_cursor_ide(self) -> RemoteCursorIDE:
        """Create and return a new LocalCursorIDE instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseCursorIDE for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_cursor_ide")

    def _start_kicad(self) -> RemoteKicad:
        """Create and return a new LocalKicad instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseKicad for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_kicad")

    def _start_blender(self) -> RemoteBlender:
        """Create and return a new LocalBlender instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalBlender for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_blender")

    def _start_file_explorer(self) -> RemoteFileExplorer:
        """Create and return a new LocalFileExplorer instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalFileExplorer for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_file_explorer")

    def _start_chrome_browser(self) -> RemoteChromeBrowser:
        """Create and return a new LocalChromeBrowser instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseChromeBrowser for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_chrome_browser")

    def _start_text_editor(self) -> RemoteTextEditor:
        """Create and return a new LocalTextEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalTextEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_text_editor")

    def _start_libre_office_writer(self) -> RemoteLibreOfficeWriter:
        """Create and return a new LocalLibreOfficeWriter instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_libre_office_writer"
        )

    def _start_libre_office_calc(self) -> RemoteLibreOfficeCalc:
        """Create and return a new LocalLibreOfficeCalc instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_libre_office_calc")

    def _start_libre_office_present(self) -> RemoteLibreOfficePresent:
        """Create and return a new LocalLibreOfficePresent instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_libre_office_present"
        )

    def _start_microsoft_word(self) -> RemoteMicrosoftWord:
        """Create and return a new LocalMicrosoftWord instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_microsoft_word")

    def _start_microsoft_excel(self) -> RemoteMicrosoftExcel:
        """Create and return a new LocalMicrosoftExcel instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_microsoft_excel")

    def _start_microsoft_powerpoint(self) -> RemoteMicrosoftPowerPoint:
        """Create and return a new LocalMicrosoftPowerPoint instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_microsoft_powerpoint"
        )

    def _start_paint_editor(self) -> RemotePaintEditor:
        """Create and return a new LocalPaintEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalPaintEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_paint_editor")

    def _start_freecad(self) -> RemoteFreeCAD:
        """Create and return a new LocalFreeCAD instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalFreeCAD for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_cad")

    def _start_kdenlive(self) -> RemoteKdenlive:
        """Create and return a new LocalKdenlive instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseVideoEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_video_editor")

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

    def _resume(self):
        """Resume the daemon client computer.

        For daemon client, resuming means sending a resume command to the daemon."""
        # TODO: implement specifically for the system in mind

    def _get_http_video_stream_url(self) -> str:
        """Get the URL for the HTTP video stream of the daemon client instance.

        Returns:
            str: The URL for the HTTP video stream, or an empty string if HTTP video streaming is not available.
        """
        response = get_http_video_stream_url_sync(client=self.client)
        if not response or not response.url:
            raise RuntimeError("Failed to get HTTP video stream URL from daemon")
        return response.url

    def _start_http_video_stream(self):
        """Start the HTTP video stream for the daemon client instance."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = start_http_video_stream_sync(
            client=self.client, body=ClientHttpVideoStartStreamAction()
        )
        if not response or not response.success:
            raise RuntimeError("Failed to start HTTP video stream")

    def _stop_http_video_stream(self):
        """Stop the HTTP video stream for the daemon client instance."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = stop_http_video_stream_sync(
            client=self.client, body=ClientHttpVideoStopStreamAction()
        )
        if not response or not response.success:
            raise RuntimeError("Failed to stop HTTP video stream")

    def _get_vnc_video_stream_url(self) -> str:
        """Get the URL for the VNC video stream of the daemon client instance.

        Returns:
            str: The URL for the VNC video stream, or an empty string if VNC video streaming is not available.
        """
        response = get_vnc_video_stream_url_sync(client=self.client)
        if not response or not response.url:
            raise RuntimeError("Failed to get VNC video stream URL from daemon")
        return response.url

    def _start_vnc_video_stream(self, **kwargs):
        """Start the VNC video stream for the daemon client instance.

        Args:
            **kwargs: VNC server configuration options passed to the daemon
        """
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = start_vnc_video_stream_sync(
            client=self.client, body=ClientVncVideoStartStreamAction(**kwargs)
        )
        if not response or not response.success:
            raise RuntimeError("Failed to start VNC video stream")

    def _stop_vnc_video_stream(self):
        """Stop the VNC video stream for the daemon client instance."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = stop_vnc_video_stream_sync(
            client=self.client, body=ClientVncVideoStopStreamAction()
        )
        if not response or not response.success:
            raise RuntimeError("Failed to stop VNC video stream")

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
    ) -> RemoteComputerFile:
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
            A ComputerFile instance for the specified file
        """
        return RemoteComputerFile(
            computer=self,
            path=path,
            mode=mode,
            encoding=encoding,
            errors=errors,
            buffering=buffering,
        )
