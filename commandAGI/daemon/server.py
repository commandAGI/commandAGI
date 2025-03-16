import os
import platform
import platform as sys_platform
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Literal, Optional, Tuple

import psutil
import typer
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from commandAGI.computers.base_computer import BaseComputer
from commandAGI.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.types import (  # Observation types for return type annotations
    ClickAction,
    ComputerPauseAction,
    ComputerResumeAction,
    ComputerStartAction,
    ComputerStopAction,
    DisplaysObservation,
    DoubleClickAction,
    DragAction,
    FileCopyFromComputerAction,
    FileCopyToComputerAction,
    JupyterStartServerAction,
    JupyterStopServerAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysDownAction,
    KeyboardKeysPressAction,
    KeyboardKeysReleaseAction,
    KeyboardStateObservation,
    LayoutTreeObservation,
    McpStartServerAction,
    McpStopServerAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ProcessesObservation,
    RdpStartServerAction,
    RdpStopServerAction,
    RunProcessAction,
    ScreenshotObservation,
    ShellCommandAction,
    TypeAction,
    VideoStartStreamAction,
    VideoStopStreamAction,
    VncStartServerAction,
    VncStopServerAction,
    WindowsObservation,
)


# Define response models for consistent API responses
class SuccessResponse(BaseModel):
    success: bool


class MessageResponse(BaseModel):
    success: bool
    message: str


class VideoStreamUrlResponse(BaseModel):
    url: str


class ComputerDaemon:
    # Default VNC executables
    DEFAULT_VNC_WINDOWS_EXECUTABLES = ["tvnserver.exe", "vncserver.exe", "winvnc.exe"]
    DEFAULT_VNC_UNIX_EXECUTABLES = ["vncserver", "tigervncserver", "x11vnc"]

    # Default VNC start command templates
    DEFAULT_VNC_START_COMMANDS = {
        "tvnserver.exe": '"{path}" -start',
        "winvnc.exe": '"{path}" -start',
        "x11vnc": "{path} -display :0 -bg -forever",
        # Default for other executables is just the path
    }

    # Default VNC stop command templates
    DEFAULT_VNC_STOP_COMMANDS = {
        "tvnserver.exe": '"{path}" -stop',
        "winvnc.exe": '"{path}" -stop',
        "vncserver": "vncserver -kill :*",
        "tigervncserver": "tigervncserver -kill :*",
        "x11vnc": "pkill x11vnc",
        # Default for other executables is taskkill on Windows
    }

    _mcp_server_name: str = "commandAGI MCP Server"
    _mcp_server_thread: threading.Thread | None = None

    def __init__(
        self,
        computer: BaseComputer,
        api_token: Optional[str] = None,
        vnc_windows_executables: Optional[list[str]] = None,
        vnc_unix_executables: Optional[list[str]] = None,
        vnc_start_commands: Optional[dict[str, str]] = None,
        vnc_stop_commands: Optional[dict[str, str]] = None,
        rdp_use_system_commands: bool = True,
        mcp_server_name: str = "commandAGI MCP Server",
    ):
        self._computer = computer
        # Use the provided token or generate a new one
        self._api_token = api_token or secrets.token_urlsafe(32)
        print(f"Using API token: {self._api_token}")

        # VNC configuration
        self._vnc_windows_executables = (
            vnc_windows_executables or self.DEFAULT_VNC_WINDOWS_EXECUTABLES.copy()
        )
        self._vnc_unix_executables = (
            vnc_unix_executables or self.DEFAULT_VNC_UNIX_EXECUTABLES.copy()
        )
        self._vnc_start_commands = (
            vnc_start_commands or self.DEFAULT_VNC_START_COMMANDS.copy()
        )
        self._vnc_stop_commands = (
            vnc_stop_commands or self.DEFAULT_VNC_STOP_COMMANDS.copy()
        )

        # RDP configuration
        self._rdp_use_system_commands = rdp_use_system_commands

        # MCP configuration
        self._mcp_server_name = mcp_server_name

        self._fastapi_server = self._create_fastapi_server()
        self._mcp_server = self._create_mcp_server()

    def _create_fastapi_server(self):

        app = FastAPI()
        security = HTTPBearer()

        def verify_token(
            credentials: HTTPAuthorizationCredentials = Security(security),
        ):
            if credentials.credentials != self._api_token:
                raise HTTPException(status_code=401, detail="Invalid token")
            return credentials.credentials

        @app.post("/reset", response_model=SuccessResponse)
        async def reset(token: str = Depends(verify_token)) -> Dict[str, Any]:
            return {"success": self._computer.reset_state()}

        @app.post("/execute/command", response_model=SuccessResponse)
        async def execute_command(
            action: ShellCommandAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.shell(
                    action.command, action.timeout, action.executible
                )
            }

        @app.post("/execute/run_process", response_model=SuccessResponse)
        async def execute_run_process(
            action: RunProcessAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.run_process(
                    action.command, action.args, action.cwd, action.env, action.timeout
                )
            }

        @app.post("/execute/keyboard/key_down", response_model=SuccessResponse)
        async def keydown(
            action: KeyboardKeyDownAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.keydown(action.key)}

        @app.post("/execute/keyboard/key_release", response_model=SuccessResponse)
        async def keyup(
            action: KeyboardKeyReleaseAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.keyup(action.key)}

        @app.post("/execute/keyboard/key_press", response_model=SuccessResponse)
        async def keypress(
            action: KeyboardKeyPressAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.keypress(action.key, action.duration)}

        @app.post("/execute/keyboard/keys_press", response_model=SuccessResponse)
        async def execute_keyboard_keys_press(
            action: KeyboardKeysPressAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.execute_keyboard_keys_press(
                    action.keys, action.duration
                )
            }

        @app.post("/execute/keyboard/keys_down", response_model=SuccessResponse)
        async def execute_keyboard_keys_down(
            action: KeyboardKeysDownAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.execute_keyboard_keys_down(action.keys)}

        @app.post("/execute/keyboard/keys_release", response_model=SuccessResponse)
        async def execute_keyboard_keys_release(
            action: KeyboardKeysReleaseAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.execute_keyboard_keys_release(action.keys)
            }

        @app.post("/execute/keyboard/hotkey", response_model=SuccessResponse)
        async def hotkey(
            action: KeyboardHotkeyAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.hotkey(action.keys)}

        @app.post("/execute/type", response_model=SuccessResponse)
        async def type(
            action: TypeAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.type(action.text)}

        @app.post("/execute/mouse/move", response_model=SuccessResponse)
        async def move(
            action: MouseMoveAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.move(action.x, action.y, action.move_duration)
            }

        @app.post("/execute/mouse/scroll", response_model=SuccessResponse)
        async def scroll(
            action: MouseScrollAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.scroll(action.amount)}

        @app.post("/execute/mouse/button_down", response_model=SuccessResponse)
        async def mouse_down(
            action: MouseButtonDownAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.mouse_down(action.button)}

        @app.post("/execute/mouse/button_up", response_model=SuccessResponse)
        async def mouse_up(
            action: MouseButtonUpAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.mouse_up(action.button)}

        @app.post("/execute/click", response_model=SuccessResponse)
        async def click(
            action: ClickAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.click(
                    action.x,
                    action.y,
                    action.move_duration,
                    action.press_duration,
                    action.button,
                )
            }

        @app.post("/execute/double_click", response_model=SuccessResponse)
        async def double_click(
            action: DoubleClickAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.double_click(
                    action.x,
                    action.y,
                    action.move_duration,
                    action.press_duration,
                    action.button,
                    action.double_click_interval_seconds,
                )
            }

        @app.post("/execute/drag", response_model=SuccessResponse)
        async def drag(
            action: DragAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.drag(
                    action.end_x,
                    action.end_y,
                    action.move_duration,
                    action.button
                )
            }

        @app.get("/observation")
        async def get_observation(token: str = Depends(verify_token)) -> Dict[str, Any]:
            return self._computer.get_observation()

        @app.get("/observation/screenshot")
        async def get_screenshot(
            display_id: int = 0,
            format: Literal["base64", "PIL", "path"] = "PIL",
            token: str = Depends(verify_token),
        ) -> ScreenshotObservation:
            return self._computer.get_screenshot(display_id, format)

        @app.get("/observation/mouse_state")
        async def get_mouse_state(
            token: str = Depends(verify_token),
        ) -> MouseStateObservation:
            return self._computer.get_mouse_state()

        @app.get("/observation/keyboard_state")
        async def get_keyboard_state(
            token: str = Depends(verify_token),
        ) -> KeyboardStateObservation:
            return self._computer.get_keyboard_state()

        @app.get("/observation/layout_tree")
        async def get_layout_tree(
            token: str = Depends(verify_token),
        ) -> LayoutTreeObservation:
            return self._computer.get_layout_tree()

        @app.get("/observation/processes")
        async def get_processes(
            token: str = Depends(verify_token),
        ) -> ProcessesObservation:
            return self._computer.get_processes()

        @app.get("/observation/windows")
        async def get_windows(token: str = Depends(verify_token)) -> WindowsObservation:
            return self._computer.get_windows()

        @app.get("/observation/displays")
        async def get_displays(
            token: str = Depends(verify_token),
        ) -> DisplaysObservation:
            return self._computer.get_displays()

        @app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """
            Simple health check endpoint that doesn't require authentication.
            Returns information about the daemon status.
            """
            try:

                # Check if the computer is responsive
                computer_responsive = self._computer is not None

                return {
                    "healthy": True,
                    "timestamp": time.time(),
                    "daemon_info": {
                        "version": getattr(self._computer, "version", "unknown"),
                        "platform": sys_platform.system(),
                        "python_version": sys_platform.python_version(),
                        "cpu_percent": psutil.cpu_percent(interval=0.1),
                        "memory_percent": psutil.virtual_memory().percent,
                    },
                    "computer_responsive": computer_responsive,
                }
            except Exception as e:
                # If there's an error, we're still "healthy" but we report the
                # error
                return {"healthy": True, "error": str(e), "timestamp": time.time()}

        @app.post("/file/copy_to_computer", response_model=SuccessResponse)
        async def copy_to_computer(
            action: FileCopyToComputerAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.copy_to_computer(
                    action.source_path, action.destination_path
                )
            }

        @app.post("/file/copy_from_computer", response_model=SuccessResponse)
        async def copy_from_computer(
            action: FileCopyFromComputerAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.copy_from_computer(
                    action.source_path, action.destination_path
                )
            }

        @app.post("/jupyter/start_server", response_model=SuccessResponse)
        async def start_jupyter_server(
            action: JupyterStartServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {
                "success": self._computer.start_jupyter_server(
                    action.port, action.notebook_dir
                )
            }

        @app.post("/jupyter/stop_server", response_model=SuccessResponse)
        async def stop_jupyter_server(
            action: JupyterStopServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.stop_jupyter_server()}

        @app.post("/video/start_stream", response_model=SuccessResponse)
        async def start_video_stream(
            action: VideoStartStreamAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.start_video_stream()}

        @app.post("/video/stop_stream", response_model=SuccessResponse)
        async def stop_video_stream(
            action: VideoStopStreamAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.stop_video_stream()}

        @app.get("/video/stream_url", response_model=VideoStreamUrlResponse)
        async def get_video_stream_url(
            token: str = Depends(verify_token),
        ) -> Dict[str, str]:
            return {"url": self._computer.video_stream_url}

        @app.post("/computer/start", response_model=SuccessResponse)
        async def start_computer(
            action: ComputerStartAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.start()}

        @app.post("/computer/stop", response_model=SuccessResponse)
        async def stop_computer(
            action: ComputerStopAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.stop()}

        @app.post("/computer/pause", response_model=SuccessResponse)
        async def pause_computer(
            action: ComputerPauseAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.pause()}

        @app.post("/computer/resume", response_model=SuccessResponse)
        async def resume_computer(
            action: ComputerResumeAction, token: str = Depends(verify_token)
        ) -> Dict[str, bool]:
            return {"success": self._computer.resume(action.timeout_hours)}

        @app.post("/vnc/start", response_model=MessageResponse)
        async def start_vnc_server(
            action: VncStartServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, Any]:
            success, message = self.start_vnc_server()
            return {"success": success, "message": message}

        @app.post("/vnc/stop", response_model=MessageResponse)
        async def stop_vnc_server(
            action: VncStopServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, Any]:
            success, message = self.stop_vnc_server()
            return {"success": success, "message": message}

        @app.post("/rdp/start", response_model=MessageResponse)
        async def start_rdp_server(
            action: RdpStartServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, Any]:
            success, message = self.start_rdp_server()
            return {"success": success, "message": message}

        @app.post("/rdp/stop", response_model=MessageResponse)
        async def stop_rdp_server(
            action: RdpStopServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, Any]:
            success, message = self.stop_rdp_server()
            return {"success": success, "message": message}

        @app.post("/mcp/start", response_model=MessageResponse)
        async def start_mcp_server_endpoint(
            action: McpStartServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, Any]:
            success, message = self.start_mcp_server()
            return {"success": success, "message": message}

        @app.post("/mcp/stop", response_model=MessageResponse)
        async def stop_mcp_server_endpoint(
            action: McpStopServerAction, token: str = Depends(verify_token)
        ) -> Dict[str, Any]:
            success, message = self.stop_mcp_server()
            return {"success": success, "message": message}

        @app.get("/mcp/status")
        async def get_mcp_server_status(
            token: str = Depends(verify_token),
        ) -> Dict[str, Any]:
            is_running = (
                self._mcp_server_thread is not None
                and self._mcp_server_thread.is_alive()
            )
            return {
                "running": is_running,
                "server_name": self._mcp_server_name,
                "port": getattr(self._mcp_server, "port", None),
                "server_info": str(self._mcp_server),
            }

        return app

    _uvicorn_server_thread: threading.Thread | None = None

    def start_fastapi_server(self, host="0.0.0.0", port=8000) -> Tuple[bool, str]:
        """
        Start the FastAPI server in a separate thread using a Uvicorn Server instance.

        Returns:
            Tuple[bool, str]: Success status and message
        """
        # Check if the FastAPI server is already running
        if self._uvicorn_server_thread and self._uvicorn_server_thread.is_alive():
            return False, "FastAPI server is already running"

        config = uvicorn.Config(
            self._fastapi_server,
            host=host,
            port=port,
            log_level="info",
        )
        self.uvicorn_server = uvicorn.Server(config)

        # Start the Uvicorn server in a separate thread.
        self._uvicorn_server_thread = threading.Thread(
            target=self.uvicorn_server.run, daemon=True
        )
        self._uvicorn_server_thread.start()
        return True, f"FastAPI server started successfully on {host}:{port}"

    def stop_fastapi_server(self) -> Tuple[bool, str]:
        """
        Stop the FastAPI server gracefully.

        Returns:
            Tuple[bool, str]: Success status and message
        """
        # Check if the FastAPI server is running
        if (
            not self._uvicorn_server_thread
            or not self._uvicorn_server_thread.is_alive()
        ):
            return False, "FastAPI server is not running"

        if hasattr(self, "uvicorn_server"):
            try:
                # Signal the Uvicorn server to shut down gracefully.
                self.uvicorn_server.should_exit = True
                # Wait for the thread to finish.
                self._uvicorn_server_thread.join(timeout=5)
                return True, "FastAPI server stopped successfully"
            except Exception as e:
                return False, f"Error stopping FastAPI server: {str(e)}"
        return False, "FastAPI server instance not found"

    def start_vnc_server(self):
        """Attempt to start a VNC server on Windows or Unix-like systems

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            system = platform.system().lower()

            if system == "windows":
                # Check if VNC server is installed (common ones)
                vnc_executables = self._vnc_windows_executables
                vnc_found = False
                vnc_path = None

                for exe in vnc_executables:
                    vnc_path = shutil.which(exe)
                    if vnc_path:
                        vnc_found = True
                        break

                if not vnc_found:
                    return (
                        False,
                        f"No VNC server found. Please install one of: {
                            ', '.join(vnc_executables)}",
                    )

                # Start the VNC server using the found executable
                exe_name = vnc_path.split("\\")[-1].lower()

                # Get the command template or use default
                command_template = self._vnc_start_commands.get(exe_name, '"{path}"')
                command = command_template.format(path=vnc_path)

                result = self._computer.shell(
                    ShellCommandAction(command=command, timeout=10)
                )

                if result:
                    return True, f"VNC server started successfully using {vnc_path}"
                return False, "Failed to start VNC server"

            else:  # Unix-like systems (Linux, macOS)
                # Check if VNC server is installed
                vnc_executables = self._vnc_unix_executables
                vnc_found = False
                vnc_path = None

                for exe in vnc_executables:
                    vnc_path = shutil.which(exe)
                    if vnc_path:
                        vnc_found = True
                        break

                if not vnc_found:
                    return (
                        False,
                        f"No VNC server found. Please install one of: {
                            ', '.join(vnc_executables)}",
                    )

                # Get the executable name
                exe_name = vnc_path.split("/")[-1].lower()

                # Get the command template or use default
                command_template = self._vnc_start_commands.get(exe_name, "{path}")
                command = command_template.format(path=vnc_path)

                result = self._computer.shell(
                    ShellCommandAction(command=command, timeout=10)
                )

                if result:
                    return True, f"VNC server started successfully using {vnc_path}"
                return False, "Failed to start VNC server"

        except Exception as e:
            return False, f"Error starting VNC server: {str(e)}"

    def stop_vnc_server(self):
        """Attempt to stop a VNC server on Windows or Unix-like systems

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            system = platform.system().lower()

            if system == "windows":
                # Check if VNC server is installed (common ones)
                vnc_executables = self._vnc_windows_executables
                vnc_found = False
                vnc_path = None

                for exe in vnc_executables:
                    vnc_path = shutil.which(exe)
                    if vnc_path:
                        vnc_found = True
                        break

                if not vnc_found:
                    return (
                        False,
                        f"No VNC server found. Please install one of: {
                            ', '.join(vnc_executables)}",
                    )

                # Get the executable name
                exe_name = vnc_path.split("\\")[-1].lower()

                # Get the command template or use default (taskkill)
                command_template = self._vnc_stop_commands.get(
                    exe_name, "taskkill /f /im {exe_name}"
                )

                # Format the command
                if "{path}" in command_template:
                    command = command_template.format(path=vnc_path)
                elif "{exe_name}" in command_template:
                    command = command_template.format(exe_name=exe_name)
                else:
                    command = command_template

                result = self._computer.shell(
                    ShellCommandAction(command=command, timeout=10)
                )

                if result:
                    return True, "VNC server stopped successfully"
                return False, "Failed to stop VNC server"

            else:  # Unix-like systems (Linux, macOS)
                # Check which VNC server is installed
                for exe in self._vnc_unix_executables:
                    if shutil.which(exe):
                        # Get the command template
                        command = self._vnc_stop_commands.get(exe)
                        if command:
                            result = self._computer.shell(
                                ShellCommandAction(command=command, timeout=10)
                            )
                            if result:
                                return True, f"VNC server ({exe}) stopped successfully"

                return False, "No running VNC server found or failed to stop it"

        except Exception as e:
            return False, f"Error stopping VNC server: {str(e)}"

    def start_rdp_server(self):
        """Attempt to start an RDP server on Windows or Unix-like systems

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            system = platform.system().lower()

            if system == "windows" and self._rdp_use_system_commands:
                # Windows has built-in RDP (Remote Desktop Services)
                # Check if the service exists
                service_check = self._computer.shell(
                    ShellCommandAction(command="sc query TermService", timeout=5)
                )

                if not service_check:
                    return (
                        False,
                        "Remote Desktop Services not found on this Windows system",
                    )

                # Start Remote Desktop Services
                result = self._computer.shell(
                    ShellCommandAction(command="net start TermService", timeout=10)
                )

                if result:
                    # Also enable Remote Desktop through registry
                    reg_result = self._computer.shell(
                        ShellCommandAction(
                            command='reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f',
                            timeout=10,
                        )
                    )

                    firewall_result = self._computer.shell(
                        ShellCommandAction(
                            command='netsh advfirewall firewall set rule group="remote desktop" new enable=Yes',
                            timeout=10,
                        )
                    )

                    return True, "Windows Remote Desktop enabled successfully"
                return False, "Failed to start Windows Remote Desktop service"

            else:  # Unix-like systems or custom Windows configuration
                # Check if xrdp is installed
                xrdp_path = shutil.which("xrdp")

                if not xrdp_path:
                    # Check the package manager to give appropriate
                    # installation instructions
                    apt_path = shutil.which("apt")
                    dnf_path = shutil.which("dnf")
                    yum_path = shutil.which("yum")

                    if apt_path:
                        return (
                            False,
                            "xrdp is not installed. Please install it with: sudo apt install xrdp",
                        )
                    elif dnf_path:
                        return (
                            False,
                            "xrdp is not installed. Please install it with: sudo dnf install xrdp",
                        )
                    elif yum_path:
                        return (
                            False,
                            "xrdp is not installed. Please install it with: sudo yum install xrdp",
                        )
                    else:
                        return (
                            False,
                            "xrdp is not installed. Please install the xrdp package for your distribution.",
                        )

                # Try systemctl first (most modern distros)
                systemctl_path = shutil.which("systemctl")
                if systemctl_path:
                    result = self._computer.shell(
                        ShellCommandAction(
                            command="sudo systemctl start xrdp", timeout=10
                        )
                    )
                    if result:
                        return (
                            True,
                            "RDP server (xrdp) started successfully with systemctl",
                        )

                # Fallback to service command
                service_path = shutil.which("service")
                if service_path:
                    result = self._computer.shell(
                        ShellCommandAction(
                            command="sudo service xrdp start", timeout=10
                        )
                    )
                    if result:
                        return (
                            True,
                            "RDP server (xrdp) started successfully with service command",
                        )

                return (
                    False,
                    "Failed to start xrdp. Ensure the service is properly installed.",
                )

        except Exception as e:
            return False, f"Error starting RDP server: {str(e)}"

    def stop_rdp_server(self):
        """Attempt to stop an RDP server on Windows or Unix-like systems

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            system = platform.system().lower()

            if system == "windows" and self._rdp_use_system_commands:
                # Disable Remote Desktop through registry first
                reg_result = self._computer.shell(
                    ShellCommandAction(
                        command='reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f',
                        timeout=10,
                    )
                )

                # Stop Windows Remote Desktop Services
                result = self._computer.shell(
                    ShellCommandAction(command="net stop TermService", timeout=10)
                )

                if result:
                    return True, "Windows Remote Desktop disabled successfully"
                return (
                    False,
                    "Failed to stop Windows Remote Desktop service (this is normal if sessions are active)",
                )

            else:  # Unix-like systems or custom Windows configuration
                # Check if xrdp is installed
                xrdp_path = shutil.which("xrdp")

                if not xrdp_path:
                    return False, "xrdp does not appear to be installed"

                # Try systemctl first (most modern distros)
                systemctl_path = shutil.which("systemctl")
                if systemctl_path:
                    result = self._computer.shell(
                        ShellCommandAction(
                            command="sudo systemctl stop xrdp", timeout=10
                        )
                    )
                    if result:
                        return (
                            True,
                            "RDP server (xrdp) stopped successfully with systemctl",
                        )

                # Fallback to service command
                service_path = shutil.which("service")
                if service_path:
                    result = self._computer.shell(
                        ShellCommandAction(command="sudo service xrdp stop", timeout=10)
                    )
                    if result:
                        return (
                            True,
                            "RDP server (xrdp) stopped successfully with service command",
                        )

                return False, "Failed to stop xrdp server"

        except Exception as e:
            return False, f"Error stopping RDP server: {str(e)}"

    def _create_mcp_server(self):
        """Create an MCP server instance that interfaces with the FastAPI endpoints

        Returns:
            FastMCP: The MCP server instance
        """
        import requests
        from mcp.server.fastmcp import FastMCP

        # Create the MCP server instance
        mcp = FastMCP(self._mcp_server_name)

        # === OBSERVATION RESOURCES ===

        @mcp.resource("observation://current")
        def get_observation_resource() -> str:
            """Get the current computer observation as a resource"""
            observation = self._computer.get_observation()
            return str(observation)

        @mcp.resource("screenshot://current")
        def get_screenshot_resource() -> str:
            """Get a screenshot of the computer as a resource"""
            screenshot = self._computer.get_screenshot()
            return str(screenshot)

        @mcp.resource("mouse://state")
        def get_mouse_state_resource() -> str:
            """Get the current mouse state as a resource"""
            mouse_state = self._computer.get_mouse_state()
            return str(mouse_state)

        @mcp.resource("keyboard://state")
        def get_keyboard_state_resource() -> str:
            """Get the current keyboard state as a resource"""
            keyboard_state = self._computer.get_keyboard_state()
            return str(keyboard_state)

        @mcp.resource("layout://tree")
        def get_layout_tree_resource() -> str:
            """Get the layout tree as a resource"""
            layout_tree = self._computer.get_layout_tree()
            return str(layout_tree)

        @mcp.resource("processes://list")
        def get_processes_resource() -> str:
            """Get the list of processes as a resource"""
            processes = self._computer.get_processes()
            return str(processes)

        @mcp.resource("windows://list")
        def get_windows_resource() -> str:
            """Get the list of windows as a resource"""
            windows = self._computer.get_windows()
            return str(windows)

        @mcp.resource("displays://list")
        def get_displays_resource() -> str:
            """Get the list of displays as a resource"""
            displays = self._computer.get_displays()
            return str(displays)

        # === OBSERVATION TOOLS ===

        @mcp.tool()
        def get_observation() -> dict:
            """Get the current computer observation"""
            return self._computer.get_observation()

        @mcp.tool()
        def get_screenshot(display_id: int = 0, format: str = "PIL") -> dict:
            """Get a screenshot of the computer"""
            return self._computer.get_screenshot(display_id, format)

        @mcp.tool()
        def get_mouse_state() -> dict:
            """Get the current mouse state"""
            return self._computer.get_mouse_state()

        @mcp.tool()
        def get_keyboard_state() -> dict:
            """Get the current keyboard state"""
            return self._computer.get_keyboard_state()

        @mcp.tool()
        def get_layout_tree() -> dict:
            """Get the layout tree"""
            return self._computer.get_layout_tree()

        @mcp.tool()
        def get_processes() -> dict:
            """Get the list of processes"""
            return self._computer.get_processes()

        @mcp.tool()
        def get_windows() -> dict:
            """Get the list of windows"""
            return self._computer.get_windows()

        @mcp.tool()
        def get_displays() -> dict:
            """Get the list of displays"""
            return self._computer.get_displays()

        # === ACTION TOOLS ===

        @mcp.tool()
        def execute_command(
            command: str, timeout: int = 30, executible: str = None
        ) -> dict:
            """Execute a system command"""
            action = ShellCommandAction(
                command=command, timeout=timeout, executible=executible
            )
            return {
                "success": self._computer.shell(
                    action.command, action.timeout, action.executible
                )
            }

        @mcp.tool()
        def type_text(text: str) -> dict:
            """Type text on the computer"""
            action = TypeAction(text=text)
            return {"success": self._computer.type(action.text)}

        @mcp.tool()
        def press_key(key: str, duration: float = None) -> dict:
            """Press a keyboard key"""
            action = KeyboardKeyPressAction(key=key, duration=duration)
            return {"success": self._computer.keypress(action.key, action.duration)}

        @mcp.tool()
        def press_keys(keys: list, duration: float = None) -> dict:
            """Press multiple keyboard keys simultaneously"""
            action = KeyboardKeysPressAction(keys=keys, duration=duration)
            return {
                "success": self._computer.execute_keyboard_keys_press(
                    action.keys, action.duration
                )
            }

        @mcp.tool()
        def press_hotkey(keys: list) -> dict:
            """Press a keyboard hotkey combination"""
            action = KeyboardHotkeyAction(keys=keys)
            return {"success": self._computer.hotkey(action.keys)}

        @mcp.tool()
        def move_mouse(x: int, y: int, move_duration: float = None) -> dict:
            """Move the mouse to specific coordinates"""
            action = MouseMoveAction(x=x, y=y, move_duration=move_duration)
            return {
                "success": self._computer.move(action.x, action.y, action.move_duration)
            }

        @mcp.tool()
        def scroll_mouse(amount: float) -> dict:
            """Scroll the mouse"""
            action = MouseScrollAction(amount=amount)
            return {"success": self._computer.scroll(action.amount)}

        @mcp.tool()
        def click(
            x: int,
            y: int,
            move_duration: float = None,
            press_duration: float = None,
            button: str = "left",
        ) -> dict:
            """Click at specific coordinates"""
            action = ClickAction(
                x=x,
                y=y,
                move_duration=move_duration,
                press_duration=press_duration,
                button=button,
            )
            return {
                "success": self._computer.click(
                    action.x,
                    action.y,
                    action.move_duration,
                    action.press_duration,
                    action.button,
                )
            }

        @mcp.tool()
        def double_click(
            x: int,
            y: int,
            move_duration: float = None,
            press_duration: float = None,
            button: str = "left",
            double_click_interval_seconds: float = None,
        ) -> dict:
            """Double click at specific coordinates"""
            action = DoubleClickAction(
                x=x,
                y=y,
                move_duration=move_duration,
                press_duration=press_duration,
                button=button,
                double_click_interval_seconds=double_click_interval_seconds,
            )
            return {
                "success": self._computer.double_click(
                    action.x,
                    action.y,
                    action.move_duration,
                    action.press_duration,
                    action.button,
                    action.double_click_interval_seconds,
                )
            }

        @mcp.tool()
        def drag(
            start_x: int,
            start_y: int,
            end_x: int,
            end_y: int,
            move_duration: float = None,
            button: str = "left",
        ) -> dict:
            """Drag from start coordinates to end coordinates"""
            action = DragAction(
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                move_duration=move_duration,
                button=button,
            )
            return {
                "success": self._computer.drag(
                    action.start_x,
                    action.start_y,
                    action.end_x,
                    action.end_y,
                    action.move_duration,
                    action.button,
                )
            }

        @mcp.tool()
        def run_process(
            command: str,
            args: list = [],
            cwd: str = None,
            env: dict = None,
            timeout: float = None,
        ) -> dict:
            """Run a process with the given command and arguments"""
            action = RunProcessAction(
                command=command, args=args, cwd=cwd, env=env, timeout=timeout
            )
            return {
                "success": self._computer.run_process(
                    action.command, action.args, action.cwd, action.env, action.timeout
                )
            }

        @mcp.tool()
        def reset_computer() -> dict:
            """Reset the computer state"""
            return self._computer.reset_state()

        # === FILE OPERATION TOOLS ===

        @mcp.tool()
        def copy_to_computer(source_path: str, destination_path: str) -> dict:
            """Copy a file to the computer"""
            action = FileCopyToComputerAction(
                source_path=source_path, destination_path=destination_path
            )
            return {
                "success": self._computer.copy_to_computer(
                    action.source_path, action.destination_path
                )
            }

        @mcp.tool()
        def copy_from_computer(source_path: str, destination_path: str) -> dict:
            """Copy a file from the computer"""
            action = FileCopyFromComputerAction(
                source_path=source_path, destination_path=destination_path
            )
            return {
                "success": self._computer.copy_from_computer(
                    action.source_path, action.destination_path
                )
            }

        # === JUPYTER SERVER TOOLS ===

        @mcp.tool()
        def start_jupyter_server(port: int = 8888, notebook_dir: str = None) -> dict:
            """Start a Jupyter notebook server"""
            action = JupyterStartServerAction(port=port, notebook_dir=notebook_dir)
            return {
                "success": self._computer.start_jupyter_server(
                    action.port, action.notebook_dir
                )
            }

        @mcp.tool()
        def stop_jupyter_server() -> dict:
            """Stop the Jupyter notebook server"""
            action = JupyterStopServerAction()
            return {"success": self._computer.stop_jupyter_server()}

        # === VIDEO STREAM TOOLS ===

        @mcp.tool()
        def start_video_stream() -> dict:
            """Start the video stream"""
            action = VideoStartStreamAction()
            return {"success": self._computer.start_video_stream()}

        @mcp.tool()
        def stop_video_stream() -> dict:
            """Stop the video stream"""
            action = VideoStopStreamAction()
            return {"success": self._computer.stop_video_stream()}

        @mcp.tool()
        def get_video_stream_url() -> dict:
            """Get the URL of the video stream"""
            return {"url": self._computer.video_stream_url}

        # === COMPUTER CONTROL TOOLS ===

        @mcp.tool()
        def start_computer() -> dict:
            """Start the computer"""
            action = ComputerStartAction()
            return {"success": self._computer.start()}

        @mcp.tool()
        def stop_computer() -> dict:
            """Stop the computer"""
            action = ComputerStopAction()
            return {"success": self._computer.stop()}

        @mcp.tool()
        def pause_computer() -> dict:
            """Pause the computer"""
            action = ComputerPauseAction()
            return {"success": self._computer.pause()}

        @mcp.tool()
        def resume_computer(timeout_hours: float = None) -> dict:
            """Resume the computer"""
            action = ComputerResumeAction(timeout_hours=timeout_hours)
            return {"success": self._computer.resume(action.timeout_hours)}

        # === VNC SERVER TOOLS ===

        @mcp.tool()
        def start_vnc_server() -> dict:
            """Start the VNC server"""
            action = VncStartServerAction()
            success, message = self.start_vnc_server()
            return {"success": success, "message": message}

        @mcp.tool()
        def stop_vnc_server() -> dict:
            """Stop the VNC server"""
            action = VncStopServerAction()
            success, message = self.stop_vnc_server()
            return {"success": success, "message": message}

        # === RDP SERVER TOOLS ===

        @mcp.tool()
        def start_rdp_server() -> dict:
            """Start the RDP server"""
            action = RdpStartServerAction()
            success, message = self.start_rdp_server()
            return {"success": success, "message": message}

        @mcp.tool()
        def stop_rdp_server() -> dict:
            """Stop the RDP server"""
            action = RdpStopServerAction()
            success, message = self.stop_rdp_server()
            return {"success": success, "message": message}

        # === MCP SERVER TOOLS ===

        @mcp.tool()
        def start_mcp_server() -> dict:
            """Start the MCP server"""
            action = McpStartServerAction()
            success, message = self.start_mcp_server()
            return {"success": success, "message": message}

        @mcp.tool()
        def stop_mcp_server() -> dict:
            """Stop the MCP server"""
            action = McpStopServerAction()
            success, message = self.stop_mcp_server()
            return {"success": success, "message": message}

        return mcp

    def start_mcp_server(self) -> Tuple[bool, str]:
        """Start an MCP server that interfaces with the FastAPI endpoints

        Returns:
            Tuple[bool, str]: Success status and message
        """
        # Check if the MCP server is already running.
        if self._mcp_server_thread and self._mcp_server_thread.is_alive():
            return False, "MCP server is already running"

        # Create and start the MCP server in a new thread; we assume that FastMCP.run() is blocking.
        # Optionally, you can pass parameters like port if FastMCP.run accepts
        # them.
        self._mcp_server_thread = threading.Thread(
            target=self._mcp_server.run, kwargs={}, daemon=True
        )
        self._mcp_server_thread.start()
        return True, f"MCP server started successfully"

    def stop_mcp_server(self) -> Tuple[bool, str]:
        """Stop the MCP server

        Returns:
            Tuple[bool, str]: Success status and message
        """
        # Check if the MCP server is running.
        if not self._mcp_server_thread or not self._mcp_server_thread.is_alive():
            return False, "MCP server is not running"

        try:
            self._mcp_server_thread.join(timeout=5)
            return True, "MCP server stopped successfully"
        except Exception as e:
            return False, f"Error stopping MCP server: {str(e)}"
