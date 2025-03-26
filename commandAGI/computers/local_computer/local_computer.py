import datetime
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

import psutil

from commandAGI._utils.image import process_screenshot
from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE
from commandAGI.computers.base_computer import (
    BaseComputer,
    SystemInfo,
)
from commandAGI.computers.local_computer.applications.local_background_shell import (
    LocalBackgroundShell,
)
from commandAGI.computers.local_computer.applications.local_blender import LocalBlender
from commandAGI.computers.local_computer.applications.local_chrome_browser import (
    LocalChromeBrowser,
)
from commandAGI.computers.local_computer.applications.local_cursor_ide import (
    LocalCursorIDE,
)
from commandAGI.computers.local_computer.applications.local_file_explorer import (
    LocalFileExplorer,
)
from commandAGI.computers.local_computer.applications.local_freecad import LocalFreeCAD
from commandAGI.computers.local_computer.applications.local_kdenlive import (
    LocalKdenlive,
)
from commandAGI.computers.local_computer.applications.local_kicad import LocalKicad
from commandAGI.computers.local_computer.applications.local_libre_office_calc import (
    LocalLibreOfficeCalc,
)
from commandAGI.computers.local_computer.applications.local_libre_office_present import (
    LocalLibreOfficePresent,
)
from commandAGI.computers.local_computer.applications.local_libreoffice_writer import (
    LocalLibreOfficeWriter,
)
from commandAGI.computers.local_computer.applications.local_microsoft_excel import (
    LocalMicrosoftExcel,
)
from commandAGI.computers.local_computer.applications.local_microsoft_powerpoint import (
    LocalMicrosoftPowerPoint,
)
from commandAGI.computers.local_computer.applications.local_microsoft_word import (
    LocalMicrosoftWord,
)
from commandAGI.computers.local_computer.applications.local_paint_editor import (
    LocalPaintEditor,
)
from commandAGI.computers.local_computer.applications.local_shell import LocalShell
from commandAGI.computers.local_computer.applications.local_text_editor import (
    LocalTextEditor,
)
from commandAGI.computers.local_computer.local_subprocess import LocalSubprocess
from commandAGI.types import (
    DisplaysObservation,
    LayoutTreeObservation,
    Platform,
    ProcessesObservation,
    WindowsObservation,
)

# Make Unix-specific imports conditional
if platform.system() != "Windows":
    import fcntl
    import pty
    import select
    import signal
    import termios
else:
    # For Windows, we need msvcrt for console I/O
    pass

    # Define dummy imports for Unix-specific modules
    pty = None
    select = None
    fcntl = None
    termios = None
    signal = None

try:
    import mss
    from PIL import Image
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandAGI with the local extra:\n\npip install commandAGI[local]"
    )

try:
    pass
except ImportError:
    raise ImportError(
        "Jupyter notebook dependencies are not installed. Please install with:\n\npip install nbformat nbclient"
    )

# Accessibility imports - these are optional and will be checked at runtime
# Windows UI Automation
uiautomation_available = False
try:
    import uiautomation as auto

    uiautomation_available = True
except ImportError:
    auto = None

# macOS Accessibility API
pyax_available = False
try:
    import pyax

    pyax_available = True
except ImportError:
    pyax = None

# Linux AT-SPI
pyatspi_available = False
try:
    import pyatspi

    pyatspi_available = True
except ImportError:
    pyatspi = None


class LocalComputer(BaseComputer):
    """Base class for local computer implementations.

    This class provides common functionality for local computer implementations
    such as screenshot capture, command execution, and basic resource management.
    """

    preferred_video_stream_mode: Literal["vnc", "http"] = "vnc"
    """Used  to indicate which video stream mode is more efficient (ie, to avoid using proxy streams)"""

    def __init__(self):
        super().__init__()
        self._sct = None
        self._temp_dir = None
        self._video_server = None
        self._video_server_thread = None
        self._video_server_port = None
        self._video_streaming = False
        self._ui_automation = None
        self._pyax = None
        self._atspi = None
        self._jupyter_server_pid = None

    def _start(self):
        """Start the local computer environment."""
        if not self._sct:
            self.logger.info("Initializing MSS screen capture")
            self._sct = mss.mss()
        if not self._temp_dir:
            self.logger.info("Creating temporary directory")
            self._temp_dir = tempfile.mkdtemp()
        self.logger.info(f"{self.__class__.__name__} started")

    def _stop(self):
        """Stop the local computer environment."""
        # Stop video streaming if active
        if self._video_streaming:
            self.stop_video_stream()

        if self._sct:
            self.logger.info("Closing MSS screen capture")
            self._sct.close()
            self._sct = None
        if self._temp_dir:
            self.logger.info("Cleaning up temporary directory")
            self._temp_dir = None
        self.logger.info(f"{self.__class__.__name__} stopped")

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
        # Capture screenshot using mss
        self.logger.debug(f"Capturing screenshot of display {display_id}")
        # mss uses 1-based indexing
        monitor = self._sct.monitors[display_id + 1]
        screenshot = self._sct.grab(monitor)

        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=screenshot,
            output_format=format,
            input_format="PIL",
            computer_name=self.__class__.__name__.lower(),
        )

    def _get_layout_tree(self) -> LayoutTreeObservation:
        """Return a LayoutTreeObservation containing the accessibility tree of the current UI.

        This method uses platform-specific accessibility APIs to retrieve the UI component tree.
        """
        system = platform.system()

        if system == "Windows":
            return self._get_windows_layout_tree()
        elif system == "Darwin":
            return self._get_macos_layout_tree()
        elif system == "Linux":
            return self._get_linux_layout_tree()
        else:
            self.logger.warning(f"Layout tree retrieval not implemented for {system}")
            return LayoutTreeObservation(tree={})

    def _get_windows_layout_tree(self) -> LayoutTreeObservation:
        """Get the UI component tree on Windows using UIAutomation."""
        if not uiautomation_available:
            self.logger.error(
                "UIAutomation not available. Install with: pip install uiautomation"
            )
            return LayoutTreeObservation(tree={"error": "UIAutomation not available"})

        try:
            desktop = auto.GetRootControl()

            def build_tree(element):
                if not element:
                    return None
                # Build common normalized properties
                common_props = {
                    "name": element.Name if hasattr(element, "Name") else None,
                    "role": (
                        element.ControlTypeName
                        if hasattr(element, "ControlTypeName")
                        else None
                    ),
                    "enabled": (
                        element.IsEnabled if hasattr(element, "IsEnabled") else None
                    ),
                    "focused": (
                        element.HasKeyboardFocus
                        if hasattr(element, "HasKeyboardFocus")
                        else None
                    ),
                    "offscreen": (
                        element.IsOffscreen if hasattr(element, "IsOffscreen") else None
                    ),
                    "bounds": (
                        {
                            "left": element.BoundingRectangle.left,
                            "top": element.BoundingRectangle.top,
                            "width": element.BoundingRectangle.width(),
                            "height": element.BoundingRectangle.height(),
                        }
                        if hasattr(element, "BoundingRectangle")
                        else None
                    ),
                    "selected": None,
                    "checked": None,
                    "expanded": None,
                    "current_value": None,
                    "min_value": None,
                    "max_value": None,
                    "percentage": None,
                }
                # Collect platform specific properties
                platform_props = {
                    "AutomationId": (
                        element.AutomationId
                        if hasattr(element, "AutomationId")
                        else None
                    ),
                    "ClassName": (
                        element.ClassName if hasattr(element, "ClassName") else None
                    ),
                }
                children = []
                for child in element.GetChildren():
                    child_tree = build_tree(child)
                    if child_tree:
                        children.append(child_tree)
                return {
                    "properties": common_props,
                    "platform": Platform.WINDOWS,
                    "platform_properties": platform_props,
                    "children": children,
                }

            tree = build_tree(desktop)
            return LayoutTreeObservation(tree=tree)

        except Exception as e:
            self.logger.error(f"Error getting Windows layout tree: {e}")
            return LayoutTreeObservation(tree={"error": str(e)})

    def _get_macos_layout_tree(self) -> LayoutTreeObservation:
        """Get the UI component tree on macOS using pyax (Accessibility API)."""
        if not pyax_available:
            self.logger.error("pyax not available. Install with: pip install pyax")
            return LayoutTreeObservation(tree={"error": "pyax not available"})

        try:

            def build_tree(element):
                if not element:
                    return None
                # Normalize common properties
                common_props = {
                    "name": (
                        element.get("AXTitle")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "role": (
                        element.get("AXRole")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "enabled": (
                        element.get("AXEnabled")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "focused": (
                        element.get("AXFocused")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "offscreen": None,
                    "bounds": None,
                    "selected": (
                        element.get("AXSelected")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "checked": None,
                    "expanded": (
                        element.get("AXExpanded")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "current_value": (
                        element.get("AXValue")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "min_value": (
                        element.get("AXMinValue")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "max_value": (
                        element.get("AXMaxValue")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "percentage": None,
                }
                # Platform-specific properties: store entire element dict
                platform_props = dict(element) if hasattr(element, "items") else {}
                children = []
                try:
                    # Assuming element is iterable for children
                    for child in element:
                        child_tree = build_tree(child)
                        if child_tree:
                            children.append(child_tree)
                except Exception:
                    pass
                return {
                    "properties": common_props,
                    "platform": Platform.MACOS,
                    "platform_properties": platform_props,
                    "children": children,
                }

            frontmost_app = pyax.get_frontmost_application()
            if not frontmost_app:
                return LayoutTreeObservation(
                    tree={"error": "No frontmost application found"}
                )
            tree = build_tree(frontmost_app)
            return LayoutTreeObservation(tree=tree)

        except Exception as e:
            self.logger.error(f"Error getting macOS layout tree: {e}")
            return LayoutTreeObservation(tree={"error": str(e)})

    def _get_linux_layout_tree(self) -> LayoutTreeObservation:
        """Get the UI component tree on Linux using AT-SPI."""
        if not pyatspi_available:
            self.logger.error(
                "pyatspi not available. Install with: pip install pyatspi"
            )
            return LayoutTreeObservation(tree={"error": "pyatspi not available"})

        try:

            def build_tree(element):
                if not element:
                    return None
                common_props = {
                    "name": element.name if hasattr(element, "name") else None,
                    "role": (
                        element.getRole().name if hasattr(element, "getRole") else None
                    ),
                    "enabled": None,
                    "focused": None,
                    "offscreen": None,
                    "bounds": None,
                    "selected": None,
                    "checked": None,
                    "expanded": None,
                    "current_value": None,
                    "min_value": None,
                    "max_value": None,
                    "percentage": None,
                }
                platform_props = {}
                try:
                    state_set = element.getState()
                    states = {
                        state: bool(state_set.contains(getattr(pyatspi.STATE, state)))
                        for state in pyatspi.STATE_VALUE_TO_NAME.values()
                    }
                    common_props["enabled"] = states.get("ENABLED", False)
                    common_props["focused"] = states.get("FOCUSED", False)
                    common_props["selected"] = states.get("SELECTED", False)
                    platform_props["States"] = states
                except Exception:
                    pass
                children = []
                try:
                    for i in range(element.childCount):
                        child = element.getChildAtIndex(i)
                        child_tree = build_tree(child)
                        if child_tree:
                            children.append(child_tree)
                except Exception:
                    pass
                return {
                    "properties": common_props,
                    "platform": Platform.LINUX,
                    "platform_properties": platform_props,
                    "children": children,
                }

            desktop = pyatspi.Registry.getDesktop(0)
            tree = build_tree(desktop)
            return LayoutTreeObservation(tree=tree)

        except Exception as e:
            self.logger.error(f"Error getting Linux layout tree: {e}")
            return LayoutTreeObservation(tree={"error": str(e)})

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executable: Optional[str] = None,
    ):
        """Execute a system command using subprocess.

        Args:
            command: The shell command to execute
            timeout: Optional timeout in seconds. Defaults to 10 if not specified
            executable: Optional executable to use for running the command
        """
        self.logger.info(f"Executing command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout if timeout is not None else 10,
            executable=executable,
        )
        if result.returncode != 0:
            self.logger.warning(
                f"Command returned non-zero exit code: {result.returncode}"
            )
            raise RuntimeError(
                f"Command returned non-zero exit code: {result.returncode}"
            )
        self.logger.info("Command executed successfully")

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ):
        """Run a process with the specified parameters.

        Args:
            command: The command/executable to run
            args: List of command line arguments
            cwd: Working directory for the process
            env: Environment variables to set
            timeout: Timeout in seconds
        """
        self.logger.info(f"Running process: {command} with args: {args}")

        # Prepare environment variables
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Run the process
        result = subprocess.run(
            [command] + args,
            cwd=cwd,
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )

        if result.returncode != 0:
            self.logger.warning(
                f"Process returned non-zero exit code: {result.returncode}"
            )
            raise RuntimeError(
                f"Process returned non-zero exit code: {result.returncode}"
            )
        self.logger.info("Process executed successfully")

    def _pause(self):
        """Pause the local computer.

        For local computers, pausing doesn't have a specific implementation
        as it's running on the local machine.
        """
        self.logger.info(f"Pausing {self.__class__.__name__} (no-op)")
        # No specific pause implementation for local computers

    def _resume(self):
        """Resume the local computer.

        For local computers, resuming doesn't have a specific implementation
        as it's running on the local machine.
        """
        self.logger.info(f"Resuming {self.__class__.__name__} (no-op)")
        # No specific resume implementation for local computers

    _jupyter_server_pid: Optional[int] = None

    def create_jupyter_notebook(self) -> NbFormatJupyterNotebook:
        """Create and return a new NbFormatJupyterNotebook instance.

        Returns:
            NbFormatJupyterNotebook: A notebook client instance for creating and manipulating notebooks.
        """
        self.logger.info("Creating new Jupyter notebook client")
        return NbFormatJupyterNotebook()

    def start_jupyter_server(
        self, port: int = 8888, notebook_dir: Optional[str] = None
    ):
        """Start a Jupyter notebook server.

        Args:
            port: Port number to run the server on
            notebook_dir: Directory to serve notebooks from. If None, uses current directory.
        """
        if self._jupyter_server_pid is not None:
            self.logger.info("Jupyter server is already running")
            return

        notebook_dir = notebook_dir or os.getcwd()
        self.logger.info(
            f"Starting Jupyter notebook server on port {port} in directory {notebook_dir}"
        )

        # Start the Jupyter notebook server as a subprocess
        cmd = [
            sys.executable,
            "-m",
            "jupyter",
            "notebook",
            f"--port={port}",
            f"--notebook-dir={notebook_dir}",
            "--no-browser",
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # Create a new process group
        )

        self._jupyter_server_pid = process.pid
        self.logger.info(
            f"Jupyter notebook server started with PID {
                self._jupyter_server_pid}"
        )

        # Wait a moment for the server to start
        time.sleep(2)

        # Check if the server is running
        if process.poll() is not None:
            stderr = process.stderr.read().decode("utf-8")
            self.logger.error(f"Jupyter notebook server failed to start: {stderr}")
            self._jupyter_server_pid = None
            raise RuntimeError(f"Jupyter notebook server failed to start: {stderr}")

    def stop_jupyter_server(self):
        """Stop the running Jupyter notebook server if one exists."""
        if self._jupyter_server_pid is None:
            self.logger.info("No Jupyter server is running")
            return

        try:
            # Try to terminate the process gracefully
            process = psutil.Process(self._jupyter_server_pid)
            process.terminate()

            # Wait for the process to terminate
            gone, still_alive = psutil.wait_procs([process], timeout=3)

            # If the process is still alive, kill it
            if still_alive:
                for p in still_alive:
                    p.kill()

            self._jupyter_server_pid = None
            self.logger.info("Jupyter notebook server stopped")
        except psutil.NoSuchProcess:
            self.logger.info("Jupyter notebook server process no longer exists")
            self._jupyter_server_pid = None
        except Exception as e:
            self.logger.error(f"Error stopping Jupyter notebook server: {e}")
            raise

    def _get_sysinfo(self) -> SystemInfo:
        """Get local system information using psutil."""
        try:
            import platform
            import socket

            import psutil

            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # Get disk usage
            disk = psutil.disk_usage("/")
            disk_usage = disk.percent

            # Get uptime
            uptime = time.time() - psutil.boot_time()

            # Get hostname and IP
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)

            # Get current user
            try:
                import getpass

                user = getpass.getuser()
            except:
                user = "unknown"

            # Get OS info
            os_name = platform.system()
            os_version = platform.version()
            architecture = platform.machine()

            return SystemInfo(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                uptime=uptime,
                hostname=hostname,
                ip_address=ip_address,
                user=user,
                os=os_name,
                version=os_version,
                architecture=architecture,
            )

        except ImportError:
            self.logger.warning("psutil not available - limited system info available")
            return SystemInfo(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                uptime=0.0,
                hostname="localhost",
                ip_address="127.0.0.1",
                user="unknown",
                os=platform.system(),
                version=platform.version(),
                architecture=platform.machine(),
            )

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executible: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
    ):
        """Execute a shell command.

        Args:
            command: The command to execute
            timeout: Optional timeout in seconds
            executable: Optional shell executable to use
            cwd: Optional working directory to use
            env: Optional environment variables to use
        """
        shell_process = self.start_shell(executible=executible, cwd=cwd, env=env)
        output = shell_process.execute(command, timeout=timeout)
        return output

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> LocalSubprocess:
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
    ) -> LocalShell:
        raise NotImplementedError(f"{self.__class__.__name__}.start_shell")

    def _start_background_shell(
        self,
        executable: str = None,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> LocalBackgroundShell:
        """Create and return a new local background shell instance.

        Args:
            executable: Path to the shell executable to use
            cwd: Initial working directory for the shell
            env: Environment variables to set in the shell

        Returns:
            LocalBackgroundShell: A background shell instance for executing background commands
        """
        return LocalBackgroundShell(
            executable=executable or DEFAULT_SHELL_EXECUTIBLE,
            cwd=cwd,
            env=env,
            logger=self.logger,
        )

    def _start_cursor_ide(self) -> LocalCursorIDE:
        """Create and return a new LocalCursorIDE instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseCursorIDE for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_cursor_ide")

    def _start_kicad(self) -> LocalKicad:
        """Create and return a new LocalKicad instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseKicad for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_kicad")

    def _start_blender(self) -> LocalBlender:
        """Create and return a new LocalBlender instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalBlender for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_blender")

    def _start_file_explorer(self) -> LocalFileExplorer:
        """Create and return a new LocalFileExplorer instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalFileExplorer for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_file_explorer")

    def _start_chrome_browser(self) -> LocalChromeBrowser:
        """Create and return a new LocalChromeBrowser instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseChromeBrowser for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_chrome_browser")

    def _start_text_editor(self) -> LocalTextEditor:
        """Create and return a new LocalTextEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalTextEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_text_editor")

    def _start_libre_office_writer(self) -> LocalLibreOfficeWriter:
        """Create and return a new LocalLibreOfficeWriter instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_libre_office_writer"
        )

    def _start_libre_office_calc(self) -> LocalLibreOfficeCalc:
        """Create and return a new LocalLibreOfficeCalc instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_libre_office_calc")

    def _start_libre_office_present(self) -> LocalLibreOfficePresent:
        """Create and return a new LocalLibreOfficePresent instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_libre_office_present"
        )

    def _start_microsoft_word(self) -> LocalMicrosoftWord:
        """Create and return a new LocalWord instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_word")

    def _start_microsoft_excel(self) -> LocalMicrosoftExcel:
        """Create and return a new LocalExcel instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_excel")

    def _start_microsoft_powerpoint(self) -> LocalMicrosoftPowerPoint:
        """Create and return a new LocalPowerPoint instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_powerpoint")

    def _start_paint_editor(self) -> LocalPaintEditor:
        """Create and return a new LocalPaintEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalPaintEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_paint_editor")

    def _start_freecad(self) -> LocalFreeCAD:
        """Create and return a new LocalFreeCAD instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of LocalFreeCAD for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_cad")

    def _start_kdenlive(self) -> LocalKdenlive:
        """Create and return a new LocalKdenlive instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseVideoEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_video_editor")

    def _find_free_port(self) -> int:
        """Find a free port to use for the video server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def _get_http_video_stream_url(self) -> str:
        """Get the URL for the HTTP video stream of the local computer instance.

        Returns:
            str: The URL for the HTTP video stream, or an empty string if HTTP video streaming is not active.
        """
        if self._video_streaming and self._video_server_port:
            return f"http://localhost:{self._video_server_port}/"
        return ""

    def _start_http_video_stream(
        self,
        host: str = "localhost",
        port: int = 8080,
        frame_rate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg",
    ):
        """Start the HTTP video stream for the local computer instance.

        This starts a simple HTTP server that serves screenshots as a video stream.

        Args:
            host: HTTP server host address
            port: HTTP server port
            frame_rate: Target frame rate for the video stream
            quality: JPEG/PNG compression quality (0-100)
            scale: Scale factor for the video stream (0.1-1.0)
            compression: Image compression format to use
        """
        if self._video_streaming:
            self.logger.info("Video stream is already running")
            return

        # Find a free port if none specified
        port = port if port != 8080 else self._find_free_port()
        self._video_server_port = port

        # Create and start the HTTP server
        self.logger.info(f"Starting video stream server on {host}:{port}")
        server = ThreadedHTTPServer(
            (host, port),
            VideoStreamHandler,
            computer=self,
            frame_rate=frame_rate,
            quality=quality,
            scale=scale,
            compression=compression,
        )

        # Run the server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = (
            True  # So the thread will exit when the main program exits
        )
        server_thread.start()

        # Store references
        self._video_server = server
        self._video_server_thread = server_thread
        self._video_streaming = True

        self.logger.info(f"Video stream started at http://{host}:{port}/")

    def _stop_http_video_stream(self):
        """Stop the HTTP video stream for the local computer instance."""
        if not self._video_streaming:
            self.logger.info("No video stream is running")
            return

        if self._video_server:
            self.logger.info("Stopping video stream server")
            self._video_server.shutdown()
            self._video_server.server_close()
            self._video_server = None
            self._video_server_thread = None
            self._video_streaming = False
            self.logger.info("Video stream stopped")

    def _get_vnc_video_stream_url(self) -> str:
        """Get the URL for the VNC video stream of the computer instance.
        Uses direct VNC server implementation instead of HTTP stream proxy.

        Returns:
            str: The URL for the VNC video stream, or an empty string if not running
        """
        # Check if VNC process exists using getattr to avoid attribute errors
        if getattr(self, "_vnc_process", None):
            host = getattr(self, "_vnc_host", "localhost")
            port = getattr(self, "_vnc_port", 5900)
            return f"vnc://{host}:{port}"
        return ""

    def _start_vnc_video_stream(
        self,
        host: str = "localhost",
        port: int = 5900,
        password: str = "commandagi",
        shared: bool = True,
        framerate: int = 30,
        quality: int = 80,
        encoding: Literal["raw", "tight", "zrle"] = "tight",
        compression_level: int = 6,
        scale: float = 1.0,
        allow_clipboard: bool = True,
        view_only: bool = False,
        allow_resize: bool = True,
    ):
        """Start a direct VNC server for the local computer using TigerVNC.

        Args:
            host: VNC server host address
            port: VNC server port
            password: VNC server password
            shared: Allow multiple simultaneous connections
            framerate: Target frame rate for the VNC stream
            quality: Image quality level (0-100)
            encoding: VNC encoding method to use
            compression_level: Compression level (0-9)
            scale: Scale factor for the VNC display (0.1-1.0)
            allow_clipboard: Enable clipboard sharing
            view_only: Disable input from VNC clients
            allow_resize: Allow clients to resize the display
        """
        import os
        import shutil
        import subprocess
        import tempfile

        # Store configuration for URL generation
        self._vnc_host = host
        self._vnc_port = port

        # Check if TigerVNC is installed
        if not shutil.which("x0vncserver"):
            self.logger.error(
                "TigerVNC (x0vncserver) not found. Please install it first."
            )
            raise RuntimeError("TigerVNC (x0vncserver) not found")

        # Create password file
        passwd_file = os.path.join(tempfile.gettempdir(), f"vnc_passwd_{self.name}")
        try:
            # Use vncpasswd to create password file
            subprocess.run(
                ["vncpasswd", "-f"],
                input=password.encode(),
                stdout=open(passwd_file, "wb"),
                check=True,
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create VNC password file: {e}")
            raise

        # Start x0vncserver with explicit parameters
        cmd = [
            "x0vncserver",
            f"-rfbport={port}",
            f"-PasswordFile={passwd_file}",
            f"-MaxProcessorUsage={framerate}",  # Use framerate to control CPU usage
            f"-CompressionLevel={compression_level}",
            f"-Quality={quality}",
            f"-PreferredEncoding={encoding}",
            f"-Scale={scale}",
            "-localhost=0" if not host == "localhost" else "-localhost=1",
            "-AlwaysShared=1" if shared else "-AlwaysShared=0",
            "-SecurityTypes=VncAuth",
            "-AcceptClipboard=1" if allow_clipboard else "-AcceptClipboard=0",
            "-SendClipboard=1" if allow_clipboard else "-SendClipboard=0",
            "-ViewOnly=1" if view_only else "-ViewOnly=0",
            "-ResizeDesktop=1" if allow_resize else "-ResizeDesktop=0",
        ]

        self._vnc_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Check if server started successfully
        time.sleep(2)  # Give it a moment to start

        if self._vnc_process.poll() is not None:  # Process is not running
            stdout, stderr = self._vnc_process.communicate()
            self.logger.error(f"VNC server failed to start: {stderr.decode()}")
            self._vnc_process = None
            raise RuntimeError(f"VNC server failed to start: {stderr.decode()}")

        self.logger.info(f"VNC server started on {host}:{port}")

    def _stop_vnc_video_stream(self):
        """Stop the direct VNC server."""
        # Check if VNC process exists using getattr to avoid attribute errors
        if getattr(self, "_vnc_process", None):
            self._vnc_process.terminate()
            self._vnc_process.wait(timeout=5)
            self._vnc_process = None

            # Clean up password file
            import os
            import tempfile

            passwd_file = os.path.join(tempfile.gettempdir(), f"vnc_passwd_{self.name}")
            if os.path.exists(passwd_file):
                os.remove(passwd_file)

            self.logger.info("VNC server stopped")

    def _copy_to_computer(self, source_path: Path, destination_path: Path) -> None:
        """Implementation of copy_to_computer functionality for LocalComputer.

        For a local computer, this simply copies files from one location to another
        on the same machine using shutil.

        Args:
            source_path: Path to the source file or directory on the local machine
            destination_path: Path where the file or directory should be copied on the computer

        Raises:
            FileNotFoundError: If the source path does not exist
            PermissionError: If there are permission issues
            OSError: For other file operation errors
        """
        self.logger.debug(f"Copying {source_path} to {destination_path} using shutil")
        self._copy_local(source_path, destination_path)

    def _copy_from_computer(self, source_path: Path, destination_path: Path) -> None:
        """Implementation of copy_from_computer functionality for LocalComputer.

        For a local computer, this simply copies files from one location to another
        on the same machine using shutil.

        Args:
            source_path: Path to the source file or directory on the computer
            destination_path: Path where the file or directory should be copied on the local machine

        Raises:
            FileNotFoundError: If the source path does not exist
            PermissionError: If there are permission issues
            OSError: For other file operation errors
        """
        # For LocalComputer, copy_from_computer is identical to copy_to_computer
        # since both source and destination are on the same machine
        self._copy_local(source_path, destination_path)

    def _copy_local(self, source_path: Path, destination_path: Path) -> None:
        """Helper method to copy files or directories locally.

        Args:
            source_path: Path to the source file or directory
            destination_path: Path where the file or directory should be copied

        Raises:
            FileNotFoundError: If the source path does not exist
            PermissionError: If there are permission issues
            OSError: For other file operation errors
        """
        # Ensure source exists
        if not source_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {source_path}")

        # Create parent directories if they don't exist
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file or directory
        if source_path.is_dir():
            if destination_path.exists() and destination_path.is_dir():
                # If destination exists and is a directory, copy contents into
                # it
                for item in source_path.iterdir():
                    if item.is_dir():
                        shutil.copytree(
                            item, destination_path / item.name, dirs_exist_ok=True
                        )
                    else:
                        shutil.copy2(item, destination_path / item.name)
            else:
                # Copy the entire directory
                shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
        else:
            # Copy a single file
            shutil.copy2(source_path, destination_path)

    def _get_processes(self) -> ProcessesObservation:
        """Return a ProcessesObservation containing information about running processes."""
        processes_info = []

        # Get all running processes using psutil
        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "username",
                "memory_info",
                "cpu_percent",
                "create_time",
                "status",
            ]
        ):
            try:
                # Get process info as a dictionary
                proc_info = proc.info

                # Add additional information
                proc_info["memory_mb"] = (
                    proc_info["memory_info"].rss / (1024 * 1024)
                    if proc_info["memory_info"]
                    else 0
                )
                proc_info["cpu_percent"] = proc.cpu_percent(interval=0.1)

                # Format create time
                if proc_info["create_time"]:
                    proc_info["create_time"] = datetime.datetime.fromtimestamp(
                        proc_info["create_time"]
                    ).strftime("%Y-%m-%d %H:%M:%S")

                # Remove memory_info object as it's not JSON serializable
                if "memory_info" in proc_info:
                    del proc_info["memory_info"]

                # Add command line if available
                try:
                    proc_info["cmdline"] = proc.cmdline()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    proc_info["cmdline"] = []

                # Add executable path if available
                try:
                    proc_info["exe"] = proc.exe()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    proc_info["exe"] = ""

                processes_info.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        return ProcessesObservation(processes=processes_info)

    def _get_windows(self) -> WindowsObservation:
        """Return a WindowsObservation containing information about open windows."""
        system = platform.system()

        if system == "Windows":
            return self._get_windows_windows()
        elif system == "Darwin":
            return self._get_windows_macos()
        elif system == "Linux":
            return self._get_windows_linux()
        else:
            self.logger.warning(
                f"Windows information retrieval not implemented for {system}"
            )
            return WindowsObservation(windows=[])

    def _get_windows_windows(self) -> WindowsObservation:
        """Get information about open windows on Windows."""
        # Lazy import UIAutomation to avoid dependency issues on non-Windows
        # platforms
        if self._ui_automation is None:
            try:
                import uiautomation as auto

                self._ui_automation = auto
            except ImportError:
                self.logger.error(
                    "UIAutomation not available. Install with: pip install uiautomation"
                )
                return WindowsObservation(
                    windows=[{"error": "UIAutomation not available"}]
                )

        auto = self._ui_automation

        windows_info = []

        # Get all top-level windows
        desktop = auto.GetRootControl()
        for window in desktop.GetChildren():
            # Only include actual windows (not desktop elements)
            if window.ControlTypeName == "Window" and window.Name:
                window_info = {
                    "title": window.Name,
                    "class_name": window.ClassName,
                    "handle": window.NativeWindowHandle,
                    "is_minimized": not window.IsVisible,
                    "is_maximized": window.BoundingRectangle.width()
                    == desktop.BoundingRectangle.width()
                    and window.BoundingRectangle.height()
                    == desktop.BoundingRectangle.height(),
                    "position": {
                        "left": window.BoundingRectangle.left,
                        "top": window.BoundingRectangle.top,
                        "width": window.BoundingRectangle.width(),
                        "height": window.BoundingRectangle.height(),
                    },
                    "is_focused": window.HasKeyboardFocus,
                }
                windows_info.append(window_info)

        return WindowsObservation(windows=windows_info)

    def _get_windows_macos(self) -> WindowsObservation:
        """Get information about open windows on macOS."""
        windows_info = []

        # Try to use Quartz for window information
        import Quartz

        # Get all windows
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly
            | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID,
        )

        for window in window_list:
            try:
                # Extract window information
                window_info = {
                    "title": window.get("kCGWindowName", ""),
                    "owner_name": window.get("kCGWindowOwnerName", ""),
                    "window_id": window.get("kCGWindowNumber", 0),
                    "layer": window.get("kCGWindowLayer", 0),
                    "is_on_screen": window.get("kCGWindowIsOnscreen", False),
                    "memory_usage": window.get("kCGWindowMemoryUsage", 0),
                }

                # Get window bounds
                bounds = window.get("kCGWindowBounds", {})
                if bounds:
                    window_info["position"] = {
                        "left": bounds.get("X", 0),
                        "top": bounds.get("Y", 0),
                        "width": bounds.get("Width", 0),
                        "height": bounds.get("Height", 0),
                    }

                windows_info.append(window_info)
            except Exception as e:
                self.logger.warning(f"Error processing window: {e}")

        return WindowsObservation(windows=windows_info)

    def _get_windows_linux(self) -> WindowsObservation:
        """Get information about open windows on Linux using python-ewmh."""
        try:
            from ewmh import EWMH
            from Xlib.display import Display
        except ImportError as e:
            self.logger.warning(
                "python-ewmh or python-xlib not available, falling back to parsing output"
            )
            raise e

        ewmh = EWMH()
        display = Display()
        client_list = ewmh.getClientList()
        windows_info = []

        for win in client_list:
            try:
                window_info = {}
                # Get window title using EWMH
                title = ewmh.getWmName(win)
                if title:
                    window_info["title"] = title
                else:
                    window_info["title"] = ""

                # Get window geometry from Xlib
                geom = win.get_geometry()
                abs_pos = win.query_tree().parent.get_geometry()
                position = {
                    "left": geom.x + abs_pos.x,
                    "top": geom.y + abs_pos.y,
                    "width": geom.width,
                    "height": geom.height,
                }
                window_info["position"] = position

                # Other properties, store raw properties in platform_properties
                platform_props = {}
                # Try to get WM_CLASS
                try:
                    wm_class = win.get_wm_class()
                    if wm_class:
                        platform_props["wm_class"] = wm_class
                except Exception:
                    pass

                window_info.update(platform_props)

                windows_info.append(window_info)
            except Exception as e:
                self.logger.warning(f"Error processing window: {e}")

        return WindowsObservation(windows=windows_info)

    def _get_displays(self) -> DisplaysObservation:
        """Return a DisplaysObservation containing information about connected displays."""
        displays_info = []

        # Get display information using mss
        for i, monitor in enumerate(
            self._sct.monitors[1:]
        ):  # Skip the "all monitors" entry at index 0
            display_info = {
                "id": i,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"],
                "is_primary": i == 0,  # Assume first monitor is primary
            }

            # Add platform-specific information
            system = platform.system()
            if system == "Windows":
                display_info = self._get_windows_display_info(display_info)
            elif system == "Darwin":
                display_info = self._get_macos_display_info(display_info, i)
            elif system == "Linux":
                display_info = self._get_linux_display_info(display_info, i)

            displays_info.append(display_info)

        return DisplaysObservation(displays=displays_info)

    def _get_windows_display_info(self, display_info: dict) -> dict:
        """Get Windows-specific display information."""
        if self._ui_automation:
            # No additional info from UIAutomation for displays
            pass
        return display_info

    def _get_macos_display_info(self, display_info: dict, display_index: int) -> dict:
        """Get macOS-specific display information."""
        import Quartz

        main_display = Quartz.CGMainDisplayID()
        all_displays = Quartz.CGGetActiveDisplayList(10, None, None)[1]

        if display_index < len(all_displays):
            display_id = all_displays[display_index]
            display_info["is_primary"] = display_id == main_display

            # Get additional display properties
            display_info["model"] = Quartz.CGDisplayModelNumber(display_id)
            display_info["vendor"] = Quartz.CGDisplayVendorNumber(display_id)
            display_info["serial"] = Quartz.CGDisplaySerialNumber(display_id)
            display_info["is_builtin"] = Quartz.CGDisplayIsBuiltin(display_id)
            display_info["is_online"] = Quartz.CGDisplayIsOnline(display_id)

        return display_info

    def _get_linux_display_info(self, display_info: dict, display_index: int) -> dict:
        """Get Linux-specific display information."""
        # Try to get display information using xrandr
        result = subprocess.run(["xrandr", "--query"], capture_output=True, text=True)

        if result.returncode == 0:
            lines = result.stdout.splitlines()
            displays = []

            for line in lines:
                if " connected " in line:
                    parts = line.split()
                    name = parts[0]
                    is_primary = "primary" in line

                    # Extract resolution if available
                    resolution = None
                    for part in parts:
                        if "x" in part and part[0].isdigit():
                            resolution = part.split("+")[0]
                            break

                    displays.append(
                        {
                            "name": name,
                            "is_primary": is_primary,
                            "resolution": resolution,
                        }
                    )

            # Match xrandr displays with mss monitors based on resolution
            if display_index < len(displays):
                display_info.update(displays[display_index])
        return display_info

    def _open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ) -> LocalComputerFile:
        """Open a file on the local computer.

        Args:
            path: Path to the file on the local computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            A LocalComputerFile instance for the specified file
        """
        return LocalComputerFile(
            computer=self,
            path=path,
            mode=mode,
            encoding=encoding,
            errors=errors,
            buffering=buffering,
        )
