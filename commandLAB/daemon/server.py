import platform
import shutil
import threading
import typer
import uvicorn
import secrets
import subprocess
import os
import sys
import tempfile
from typing import Optional, Dict, Any, List, Tuple
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.types import (
    ClickAction,
    CommandAction,
    DoubleClickAction,
    DragAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysPressAction,
    RunProcessAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)


class ComputerDaemon:
    # Default VNC executables
    DEFAULT_VNC_WINDOWS_EXECUTABLES = ["tvnserver.exe", "vncserver.exe", "winvnc.exe"]
    DEFAULT_VNC_UNIX_EXECUTABLES = ["vncserver", "tigervncserver", "x11vnc"]
    
    # Default VNC start command templates
    DEFAULT_VNC_START_COMMANDS = {
        "tvnserver.exe": "\"{path}\" -start",
        "winvnc.exe": "\"{path}\" -start",
        "x11vnc": "{path} -display :0 -bg -forever",
        # Default for other executables is just the path
    }
    
    # Default VNC stop command templates
    DEFAULT_VNC_STOP_COMMANDS = {
        "tvnserver.exe": "\"{path}\" -stop",
        "winvnc.exe": "\"{path}\" -stop",
        "vncserver": "vncserver -kill :*",
        "tigervncserver": "tigervncserver -kill :*",
        "x11vnc": "pkill x11vnc",
        # Default for other executables is taskkill on Windows
    }

    _mcp_server_name: str = "CommandLAB MCP Server"
    
    def __init__(
        self,
        computer: BaseComputer,
        api_token: Optional[str] = None,
        vnc_windows_executables: Optional[list[str]] = None,
        vnc_unix_executables: Optional[list[str]] = None,
        vnc_start_commands: Optional[dict[str, str]] = None,
        vnc_stop_commands: Optional[dict[str, str]] = None,
        rdp_use_system_commands: bool = True,
        mcp_server_name: str = "CommandLAB MCP Server",
    ):
        self._computer = computer
        self._api_token = api_token or secrets.token_urlsafe(32)
        
        # VNC configuration
        self._vnc_windows_executables = vnc_windows_executables or self.DEFAULT_VNC_WINDOWS_EXECUTABLES.copy()
        self._vnc_unix_executables = vnc_unix_executables or self.DEFAULT_VNC_UNIX_EXECUTABLES.copy()
        self._vnc_start_commands = vnc_start_commands or self.DEFAULT_VNC_START_COMMANDS.copy()
        self._vnc_stop_commands = vnc_stop_commands or self.DEFAULT_VNC_STOP_COMMANDS.copy()
        
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

        @app.post("/reset")
        async def reset(token: str = Depends(verify_token)):
            return self._computer.reset_state()

        @app.post("/execute/command")
        async def execute_command(
            action: CommandAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_command(action)}

        @app.post("/execute/keyboard/key_down")
        async def execute_keyboard_key_down(
            action: KeyboardKeyDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_key_down(action)}

        @app.post("/execute/keyboard/key_release")
        async def execute_keyboard_key_release(
            action: KeyboardKeyReleaseAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_key_release(action)}

        @app.post("/execute/keyboard/key_press")
        async def execute_keyboard_key_press(
            action: KeyboardKeyPressAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_key_press(action)}

        @app.post("/execute/keyboard/hotkey")
        async def execute_keyboard_hotkey(
            action: KeyboardHotkeyAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_hotkey(action)}

        @app.post("/execute/type")
        async def execute_type(action: TypeAction, token: str = Depends(verify_token)):
            return {"success": self._computer.execute_type(action)}

        @app.post("/execute/mouse/move")
        async def execute_mouse_move(
            action: MouseMoveAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_move(action)}

        @app.post("/execute/mouse/scroll")
        async def execute_mouse_scroll(
            action: MouseScrollAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_scroll(action)}

        @app.post("/execute/mouse/button_down")
        async def execute_mouse_button_down(
            action: MouseButtonDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_button_down(action)}

        @app.post("/execute/mouse/button_up")
        async def execute_mouse_button_up(
            action: MouseButtonUpAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_button_up(action)}

        @app.get("/observation")
        async def get_observation(token: str = Depends(verify_token)):
            return self._computer.get_observation()

        @app.get("/observation/screenshot")
        async def get_screenshot(token: str = Depends(verify_token)):
            return self._computer.get_screenshot()

        @app.get("/observation/mouse_state")
        async def get_mouse_state(token: str = Depends(verify_token)):
            return self._computer.get_mouse_state()

        @app.get("/observation/keyboard_state")
        async def get_keyboard_state(token: str = Depends(verify_token)):
            return self._computer.get_keyboard_state()

        @app.post("/vnc/start")
        async def start_vnc_server(token: str = Depends(verify_token)):
            success, message = self.start_vnc_server()
            return {"success": success, "message": message}

        @app.post("/vnc/stop")
        async def stop_vnc_server(token: str = Depends(verify_token)):
            success, message = self.stop_vnc_server()
            return {"success": success, "message": message}

        @app.post("/rdp/start")
        async def start_rdp_server(token: str = Depends(verify_token)):
            success, message = self.start_rdp_server()
            return {"success": success, "message": message}

        @app.post("/rdp/stop")
        async def stop_rdp_server(token: str = Depends(verify_token)):
            success, message = self.stop_rdp_server()
            return {"success": success, "message": message}
            
        @app.post("/mcp/start")
        async def start_mcp_server_endpoint(token: str = Depends(verify_token)):
            success, message = self.start_mcp_server()
            return {"success": success, "message": message}
            
        @app.post("/mcp/stop")
        async def stop_mcp_server_endpoint(token: str = Depends(verify_token)):
            success, message = self.stop_mcp_server()
            return {"success": success, "message": message}
            
        @app.get("/mcp/status")
        async def get_mcp_server_status(token: str = Depends(verify_token)):
            is_running = self.mcp_server_process is not None and self.mcp_server_process.poll() is None
            return {
                "running": is_running,
                "server_name": self._mcp_server_name,
                "port": self.mcp_server_port,
                "script_path": self.mcp_server_file
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
            target=self.uvicorn_server.run,
            daemon=True
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
        if not self._uvicorn_server_thread or not self._uvicorn_server_thread.is_alive():
            return False, "FastAPI server is not running"
            
        if hasattr(self, 'uvicorn_server'):
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
                    return False, f"No VNC server found. Please install one of: {', '.join(vnc_executables)}"
                
                # Start the VNC server using the found executable
                exe_name = vnc_path.split('\\')[-1].lower()
                
                # Get the command template or use default
                command_template = self._vnc_start_commands.get(exe_name, "\"{path}\"")
                command = command_template.format(path=vnc_path)
                
                result = self._computer.execute_command(
                    CommandAction(command=command, timeout=10)
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
                    return False, f"No VNC server found. Please install one of: {', '.join(vnc_executables)}"
                
                # Get the executable name
                exe_name = vnc_path.split('/')[-1].lower()
                
                # Get the command template or use default
                command_template = self._vnc_start_commands.get(exe_name, "{path}")
                command = command_template.format(path=vnc_path)
                
                result = self._computer.execute_command(
                    CommandAction(command=command, timeout=10)
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
                    return False, f"No VNC server found. Please install one of: {', '.join(vnc_executables)}"
                
                # Get the executable name
                exe_name = vnc_path.split('\\')[-1].lower()
                
                # Get the command template or use default (taskkill)
                command_template = self._vnc_stop_commands.get(
                    exe_name, 
                    "taskkill /f /im {exe_name}"
                )
                
                # Format the command
                if "{path}" in command_template:
                    command = command_template.format(path=vnc_path)
                elif "{exe_name}" in command_template:
                    command = command_template.format(exe_name=exe_name)
                else:
                    command = command_template
                
                result = self._computer.execute_command(
                    CommandAction(command=command, timeout=10)
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
                            result = self._computer.execute_command(
                                CommandAction(command=command, timeout=10)
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
                service_check = self._computer.execute_command(
                    CommandAction(command="sc query TermService", timeout=5)
                )
                
                if not service_check:
                    return False, "Remote Desktop Services not found on this Windows system"
                
                # Start Remote Desktop Services
                result = self._computer.execute_command(
                    CommandAction(command="net start TermService", timeout=10)
                )
                
                if result:
                    # Also enable Remote Desktop through registry
                    reg_result = self._computer.execute_command(
                        CommandAction(
                            command="reg add \"HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\" /v fDenyTSConnections /t REG_DWORD /d 0 /f", 
                            timeout=10
                        )
                    )
                    
                    firewall_result = self._computer.execute_command(
                        CommandAction(
                            command="netsh advfirewall firewall set rule group=\"remote desktop\" new enable=Yes",
                            timeout=10
                        )
                    )
                    
                    return True, "Windows Remote Desktop enabled successfully"
                return False, "Failed to start Windows Remote Desktop service"
            
            else:  # Unix-like systems or custom Windows configuration
                # Check if xrdp is installed
                xrdp_path = shutil.which("xrdp")
                
                if not xrdp_path:
                    # Check the package manager to give appropriate installation instructions
                    apt_path = shutil.which("apt")
                    dnf_path = shutil.which("dnf")
                    yum_path = shutil.which("yum")
                    
                    if apt_path:
                        return False, "xrdp is not installed. Please install it with: sudo apt install xrdp"
                    elif dnf_path:
                        return False, "xrdp is not installed. Please install it with: sudo dnf install xrdp"
                    elif yum_path:
                        return False, "xrdp is not installed. Please install it with: sudo yum install xrdp"
                    else:
                        return False, "xrdp is not installed. Please install the xrdp package for your distribution."
                
                # Try systemctl first (most modern distros)
                systemctl_path = shutil.which("systemctl")
                if systemctl_path:
                    result = self._computer.execute_command(
                        CommandAction(command="sudo systemctl start xrdp", timeout=10)
                    )
                    if result:
                        return True, "RDP server (xrdp) started successfully with systemctl"
                
                # Fallback to service command
                service_path = shutil.which("service")
                if service_path:
                    result = self._computer.execute_command(
                        CommandAction(command="sudo service xrdp start", timeout=10)
                    )
                    if result:
                        return True, "RDP server (xrdp) started successfully with service command"
                
                return False, "Failed to start xrdp. Ensure the service is properly installed."
                
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
                reg_result = self._computer.execute_command(
                    CommandAction(
                        command="reg add \"HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\" /v fDenyTSConnections /t REG_DWORD /d 1 /f", 
                        timeout=10
                    )
                )
                
                # Stop Windows Remote Desktop Services
                result = self._computer.execute_command(
                    CommandAction(command="net stop TermService", timeout=10)
                )
                
                if result:
                    return True, "Windows Remote Desktop disabled successfully"
                return False, "Failed to stop Windows Remote Desktop service (this is normal if sessions are active)"
            
            else:  # Unix-like systems or custom Windows configuration
                # Check if xrdp is installed
                xrdp_path = shutil.which("xrdp")
                
                if not xrdp_path:
                    return False, "xrdp does not appear to be installed"
                
                # Try systemctl first (most modern distros)
                systemctl_path = shutil.which("systemctl")
                if systemctl_path:
                    result = self._computer.execute_command(
                        CommandAction(command="sudo systemctl stop xrdp", timeout=10)
                    )
                    if result:
                        return True, "RDP server (xrdp) stopped successfully with systemctl"
                
                # Fallback to service command
                service_path = shutil.which("service")
                if service_path:
                    result = self._computer.execute_command(
                        CommandAction(command="sudo service xrdp stop", timeout=10)
                    )
                    if result:
                        return True, "RDP server (xrdp) stopped successfully with service command"
                
                return False, "Failed to stop xrdp server"
                
        except Exception as e:
            return False, f"Error stopping RDP server: {str(e)}"

    def _create_mcp_server(self):
        """Create an MCP server instance that interfaces with the FastAPI endpoints
        
        Returns:
            FastMCP: The MCP server instance
        """
        from mcp.server.fastmcp import FastMCP
        import requests
        
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
        
        # === OBSERVATION TOOLS ===
        
        @mcp.tool()
        def get_observation() -> dict:
            """Get the current computer observation"""
            return self._computer.get_observation()
        
        @mcp.tool()
        def get_screenshot() -> dict:
            """Get a screenshot of the computer"""
            return self._computer.get_screenshot()
        
        @mcp.tool()
        def get_mouse_state() -> dict:
            """Get the current mouse state"""
            return self._computer.get_mouse_state()
        
        @mcp.tool()
        def get_keyboard_state() -> dict:
            """Get the current keyboard state"""
            return self._computer.get_keyboard_state()
        
        # === ACTION TOOLS ===
        
        @mcp.tool()
        def execute_command(command: str, timeout: int = 30) -> dict:
            """Execute a system command"""
            return {"success": self._computer.execute_command(CommandAction(command=command, timeout=timeout))}
        
        @mcp.tool()
        def type_text(text: str) -> dict:
            """Type text on the computer"""
            return {"success": self._computer.execute_type(TypeAction(text=text))}
        
        @mcp.tool()
        def press_key(key: str) -> dict:
            """Press a keyboard key"""
            return {"success": self._computer.execute_keyboard_key_press(KeyboardKeyPressAction(key=key))}
        
        @mcp.tool()
        def press_keys(keys: list) -> dict:
            """Press multiple keyboard keys simultaneously"""
            return {"success": self._computer.execute_keyboard_keys_press(KeyboardKeysPressAction(keys=keys))}
        
        @mcp.tool()
        def press_hotkey(keys: list) -> dict:
            """Press a keyboard hotkey combination"""
            return {"success": self._computer.execute_keyboard_hotkey(KeyboardHotkeyAction(keys=keys))}
        
        @mcp.tool()
        def move_mouse(x: int, y: int) -> dict:
            """Move the mouse to specific coordinates"""
            return {"success": self._computer.execute_mouse_move(MouseMoveAction(x=x, y=y))}
        
        @mcp.tool()
        def scroll_mouse(amount: float) -> dict:
            """Scroll the mouse"""
            return {"success": self._computer.execute_mouse_scroll(MouseScrollAction(amount=amount))}
        
        @mcp.tool()
        def click(x: int, y: int, button: str = "left") -> dict:
            """Click at specific coordinates"""
            return {"success": self._computer.execute_click(ClickAction(x=x, y=y, button=button))}
        
        @mcp.tool()
        def double_click(x: int, y: int, button: str = "left") -> dict:
            """Double click at specific coordinates"""
            return {"success": self._computer.execute_double_click(DoubleClickAction(x=x, y=y, button=button))}
        
        @mcp.tool()
        def drag(start_x: int, start_y: int, end_x: int, end_y: int, button: str = "left") -> dict:
            """Drag from start coordinates to end coordinates"""
            return {"success": self._computer.execute_drag(DragAction(
                start_x=start_x, 
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                button=button
            ))}
        
        @mcp.tool()
        def run_process(command: str, args: list = [], cwd: str = None, env: dict = None, timeout: float = None) -> dict:
            """Run a process with the given command and arguments"""
            return {"success": self._computer.execute_run_process(RunProcessAction(
                command=command,
                args=args,
                cwd=cwd,
                env=env,
                timeout=timeout
            ))}
        
        @mcp.tool()
        def reset_computer() -> dict:
            """Reset the computer state"""
            return self._computer.reset_state()
        
        return mcp

    _mcp_server_thread: threading.Thread | None = None

    def start_mcp_server(self) -> Tuple[bool, str]:
        """Start an MCP server that interfaces with the FastAPI endpoints
        
        Returns:
            Tuple[bool, str]: Success status and message
        """
        # Check if the MCP server is already running.
        if self._mcp_server_thread and self._mcp_server_thread.is_alive():
            return False, "MCP server is already running"

        # Create and start the MCP server in a new thread; we assume that FastMCP.run() is blocking.
        # Optionally, you can pass parameters like port if FastMCP.run accepts them.
        self._mcp_server_thread = threading.Thread(
            target=self._mcp_server.run,
            kwargs={},
            daemon=True
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
