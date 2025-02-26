import platform
import shutil
import typer
import uvicorn
import secrets
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.types import (
    CommandAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
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
    
    def __init__(
        self,
        computer: BaseComputer,
        api_token: Optional[str] = None,
        vnc_windows_executables: Optional[list[str]] = None,
        vnc_unix_executables: Optional[list[str]] = None,
        vnc_start_commands: Optional[dict[str, str]] = None,
        vnc_stop_commands: Optional[dict[str, str]] = None,
        rdp_use_system_commands: bool = True,
    ):
        self.app = FastAPI()
        self._computer = computer
        self.api_token = api_token or secrets.token_urlsafe(32)
        
        # VNC configuration
        self.vnc_windows_executables = vnc_windows_executables or self.DEFAULT_VNC_WINDOWS_EXECUTABLES
        self.vnc_unix_executables = vnc_unix_executables or self.DEFAULT_VNC_UNIX_EXECUTABLES
        
        # VNC start command templates
        self.vnc_start_commands = self.DEFAULT_VNC_START_COMMANDS.copy()
        if vnc_start_commands:
            self.vnc_start_commands.update(vnc_start_commands)
            
        # VNC stop command templates
        self.vnc_stop_commands = self.DEFAULT_VNC_STOP_COMMANDS.copy()
        if vnc_stop_commands:
            self.vnc_stop_commands.update(vnc_stop_commands)
            
        # RDP configuration
        self.rdp_use_system_commands = rdp_use_system_commands

        security = HTTPBearer()

        def verify_token(
            credentials: HTTPAuthorizationCredentials = Security(security),
        ):
            if credentials.credentials != self.api_token:
                raise HTTPException(status_code=401, detail="Invalid token")
            return credentials.credentials

        @self.app.post("/reset")
        async def reset(token: str = Depends(verify_token)):
            return self._computer.reset()

        @self.app.post("/execute/command")
        async def execute_command(
            action: CommandAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_command(action)}

        @self.app.post("/execute/keyboard/key_down")
        async def execute_keyboard_key_down(
            action: KeyboardKeyDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_key_down(action)}

        @self.app.post("/execute/keyboard/key_release")
        async def execute_keyboard_key_release(
            action: KeyboardKeyReleaseAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_key_release(action)}

        @self.app.post("/execute/keyboard/key_press")
        async def execute_keyboard_key_press(
            action: KeyboardKeyPressAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_key_press(action)}

        @self.app.post("/execute/keyboard/hotkey")
        async def execute_keyboard_hotkey(
            action: KeyboardHotkeyAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_keyboard_hotkey(action)}

        @self.app.post("/execute/type")
        async def execute_type(action: TypeAction, token: str = Depends(verify_token)):
            return {"success": self._computer.execute_type(action)}

        @self.app.post("/execute/mouse/move")
        async def execute_mouse_move(
            action: MouseMoveAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_move(action)}

        @self.app.post("/execute/mouse/scroll")
        async def execute_mouse_scroll(
            action: MouseScrollAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_scroll(action)}

        @self.app.post("/execute/mouse/button_down")
        async def execute_mouse_button_down(
            action: MouseButtonDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_button_down(action)}

        @self.app.post("/execute/mouse/button_up")
        async def execute_mouse_button_up(
            action: MouseButtonUpAction, token: str = Depends(verify_token)
        ):
            return {"success": self._computer.execute_mouse_button_up(action)}

        @self.app.get("/observation")
        async def get_observation(token: str = Depends(verify_token)):
            return self._computer.get_observation()

        @self.app.get("/observation/screenshot")
        async def get_screenshot(token: str = Depends(verify_token)):
            return self._computer.get_screenshot()

        @self.app.get("/observation/mouse_state")
        async def get_mouse_state(token: str = Depends(verify_token)):
            return self._computer.get_mouse_state()

        @self.app.get("/observation/keyboard_state")
        async def get_keyboard_state(token: str = Depends(verify_token)):
            return self._computer.get_keyboard_state()

        @self.app.post("/vnc/start")
        async def start_vnc_server(token: str = Depends(verify_token)):
            success, message = self.start_vnc_server()
            return {"success": success, "message": message}

        @self.app.post("/vnc/stop")
        async def stop_vnc_server(token: str = Depends(verify_token)):
            success, message = self.stop_vnc_server()
            return {"success": success, "message": message}

        @self.app.post("/rdp/start")
        async def start_rdp_server(token: str = Depends(verify_token)):
            success, message = self.start_rdp_server()
            return {"success": success, "message": message}

        @self.app.post("/rdp/stop")
        async def stop_rdp_server(token: str = Depends(verify_token)):
            success, message = self.stop_rdp_server()
            return {"success": success, "message": message}

    def get_computer(self) -> BaseComputer:
        if self._computer is None:
            self._computer = self._computer_cls(**self._computer_cls_kwargs)
        return self._computer

    def start_server(self, host="0.0.0.0", port=8000):
        uvicorn.run(self.app, host=host, port=port)

    def start_vnc_server(self):
        """Attempt to start a VNC server on Windows or Unix-like systems
        
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Check if VNC server is installed (common ones)
                vnc_executables = self.vnc_windows_executables
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
                command_template = self.vnc_start_commands.get(exe_name, "\"{path}\"")
                command = command_template.format(path=vnc_path)
                
                result = self._computer.execute_command(
                    CommandAction(command=command, timeout=10)
                )
                
                if result:
                    return True, f"VNC server started successfully using {vnc_path}"
                return False, "Failed to start VNC server"
                
            else:  # Unix-like systems (Linux, macOS)
                # Check if VNC server is installed
                vnc_executables = self.vnc_unix_executables
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
                command_template = self.vnc_start_commands.get(exe_name, "{path}")
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
                vnc_executables = self.vnc_windows_executables
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
                command_template = self.vnc_stop_commands.get(
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
                for exe in self.vnc_unix_executables:
                    if shutil.which(exe):
                        # Get the command template
                        command = self.vnc_stop_commands.get(exe)
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
            
            if system == "windows" and self.rdp_use_system_commands:
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
            
            if system == "windows" and self.rdp_use_system_commands:
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
