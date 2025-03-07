import base64
import datetime
import io
import logging
import os
import platform
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from textwrap import dedent
from typing import IO, Any, AnyStr, Dict, List, Literal, Optional, Union

import psutil

from commandAGI._utils.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE
from commandAGI.computers.base_computer import (
    BaseComputer,
    BaseComputerFile,
    BaseJupyterNotebook,
    BaseShell,
)
from commandAGI.types import (
    DisplaysObservation,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    LayoutTreeObservation,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    Platform,
    ProcessesObservation,
    RunProcessAction,
    ScreenshotObservation,
    ShellCommandAction,
    TypeAction,
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
    import msvcrt

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
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError
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


class NbFormatJupyterNotebook(BaseJupyterNotebook):
    """Implementation of BaseJupyterNotebook using nbformat and nbclient libraries.

    This class provides methods to create, read, modify, and execute notebooks
    using the nbformat and nbclient libraries.
    """

    def __init__(self):
        """Initialize the notebook client."""
        super().__init__()
        self._client = None

    def _get_client(
        self, notebook: Dict[str, Any], timeout: int = 600
    ) -> NotebookClient:
        """Get or create a NotebookClient instance."""
        if self._client is None:
            self._client = NotebookClient(
                notebook, timeout=timeout, kernel_name="python3"
            )
        return self._client

    def create_notebook(self) -> Dict[str, Any]:
        """Create a new empty notebook and return the notebook object."""
        return nbformat.v4.new_notebook()

    def read_notebook(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Read a notebook from a file and return the notebook object."""
        path = Path(path) if isinstance(path, str) else path
        with open(path, "r", encoding="utf-8") as f:
            return nbformat.read(f, as_version=4)

    def save_notebook(
        self, notebook: Dict[str, Any], path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Save the notebook to a file and return the path."""
        if path is None:
            if self.notebook_path is None:
                raise ValueError("No path specified and no default notebook path set")
            path = self.notebook_path
        else:
            path = Path(path) if isinstance(path, str) else path
            self.notebook_path = path

        with open(path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)
        return path

    def add_markdown_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a markdown cell to the notebook and return the updated notebook."""
        cell = nbformat.v4.new_markdown_cell(source)
        if position is None:
            notebook.cells.append(cell)
        else:
            notebook.cells.insert(position, cell)
        return notebook

    def add_code_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a code cell to the notebook and return the updated notebook."""
        cell = nbformat.v4.new_code_cell(source)
        if position is None:
            notebook.cells.append(cell)
        else:
            notebook.cells.insert(position, cell)
        return notebook

    def update_cell(
        self, notebook: Dict[str, Any], index: int, source: str
    ) -> Dict[str, Any]:
        """Update the source of a cell at the given index and return the updated notebook."""
        if 0 <= index < len(notebook.cells):
            notebook.cells[index]["source"] = source
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )
        return notebook

    def remove_cell(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Remove a cell at the given index and return the updated notebook."""
        if 0 <= index < len(notebook.cells):
            notebook.cells.pop(index)
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )
        return notebook

    def list_cells(self, notebook: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return a list of cells in the notebook."""
        return [
            {
                "index": i,
                "cell_type": cell.get("cell_type", "unknown"),
                "source": cell.get("source", ""),
                "execution_count": (
                    cell.get("execution_count", None)
                    if cell.get("cell_type") == "code"
                    else None
                ),
                "has_output": (
                    bool(cell.get("outputs", []))
                    if cell.get("cell_type") == "code"
                    else False
                ),
            }
            for i, cell in enumerate(notebook.cells)
        ]

    def execute_notebook(
        self, notebook: Dict[str, Any], timeout: int = 600
    ) -> Dict[str, Any]:
        """Execute all cells in the notebook and return the executed notebook."""
        client = self._get_client(notebook, timeout)
        try:
            client.execute()
            return notebook
        except CellExecutionError as e:
            # Continue execution even if a cell fails
            return notebook

    def execute_cell(
        self, notebook: Dict[str, Any], index: int, timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a specific cell in the notebook and return the executed notebook."""
        if 0 <= index < len(notebook.cells):
            client = self._get_client(notebook, timeout)
            try:
                # Execute only the specified cell
                client.execute_cell(notebook.cells[index], index)
            except CellExecutionError:
                # Continue even if execution fails
                pass
            return notebook
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )

    def get_cell_output(
        self, notebook: Dict[str, Any], index: int
    ) -> List[Dict[str, Any]]:
        """Return the output of a cell at the given index."""
        if 0 <= index < len(notebook.cells):
            cell = notebook.cells[index]
            if cell.get("cell_type") == "code":
                return cell.get("outputs", [])
            else:
                return []
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )

    def clear_cell_output(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Clear the output of a cell at the given index and return the updated notebook."""
        if 0 <= index < len(notebook.cells):
            cell = notebook.cells[index]
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )
        return notebook

    def clear_all_outputs(self, notebook: Dict[str, Any]) -> Dict[str, Any]:
        """Clear the outputs of all cells in the notebook and return the updated notebook."""
        for cell in notebook.cells:
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
        return notebook


class LocalShell(BaseShell):
    """Implementation of BaseShell for local system shells.

    This class provides methods to interact with a persistent shell process
    on the local system.
    """

    _process: Optional[subprocess.Popen] = None
    _master_fd: Optional[int] = None
    _slave_fd: Optional[int] = None
    _output_buffer: str = ""
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        executable: str = DEFAULT_SHELL_EXECUTIBLE,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a LocalShell instance.

        Args:
            executable: Path to the shell executable
            cwd: Initial working directory
            env: Environment variables to set
            logger: Logger instance
        """
        super().__init__(
            executable=executable,
            cwd=Path(cwd) if cwd else Path.cwd(),
            env=env or {},
            logger=logger or logging.getLogger("commandAGI.shell"),
        )
        self._lock = threading.Lock()

    def start(self) -> bool:
        """Start the shell process.

        Returns:
            bool: True if the shell was started successfully, False otherwise.
        """
        if self.is_running():
            self._logger.info("Shell is already running")
            return True

        try:
            self._logger.info(
                f"Starting shell with executable: {
                    self.executable}"
            )

            # Set up environment
            env = os.environ.copy()
            if self.env:
                env.update(self.env)

            if platform.system() == "Windows":
                # Windows implementation using subprocess with pipes
                self._process = subprocess.Popen(
                    # Use cmd.exe as the shell
                    ["cmd.exe", "/c", self.executable],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,
                    env=env,
                    shell=False,  # Don't create another shell layer
                    text=True,
                    bufsize=0,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # New process group
                )
                self.pid = self._process.pid
            else:
                # Unix implementation using pty
                self._master_fd, self._slave_fd = pty.openpty()
                # Make the master file descriptor non-blocking
                flags = fcntl.fcntl(self._master_fd, fcntl.F_GETFL)
                fcntl.fcntl(self._master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                # Start the shell process
                self._process = subprocess.Popen(
                    [self.executable],
                    stdin=self._slave_fd,
                    stdout=self._slave_fd,
                    stderr=self._slave_fd,
                    cwd=self.cwd,
                    env=env,
                    preexec_fn=os.setsid,  # Create new session
                )
                self.pid = self._process.pid

            self._logger.info(f"Shell started with PID: {self.pid}")

            # Change to the initial working directory if specified
            if self.cwd:
                self.change_directory(self.cwd)

            return True
        except Exception as e:
            self._logger.error(f"Error starting shell: {e}")
            self._cleanup()
            return False

    def stop(self) -> bool:
        """Stop the shell process.

        Returns:
            bool: True if the shell was stopped successfully, False otherwise.
        """
        if not self.is_running():
            self._logger.info("Shell is not running")
            return True

        try:
            self._logger.info(f"Stopping shell with PID: {self.pid}")

            if platform.system() == "Windows":
                # Send exit command to gracefully exit
                self.execute("exit", timeout=1)

                # If still running, terminate
                if self._process and self._process.poll() is None:
                    self._process.terminate()
                    self._process.wait(timeout=3)
            else:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(self.pid), signal.SIGTERM)

                # Wait for the process to terminate
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # If still running, send SIGKILL
                    os.killpg(os.getpgid(self.pid), signal.SIGKILL)

            self._cleanup()
            self._logger.info("Shell stopped")
            return True
        except Exception as e:
            self._logger.error(f"Error stopping shell: {e}")
            self._cleanup()
            return False

    def _cleanup(self):
        """Clean up resources."""
        if platform.system() != "Windows" and self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

        if platform.system() != "Windows" and self._slave_fd is not None:
            try:
                os.close(self._slave_fd)
            except OSError:
                pass
            self._slave_fd = None

        self._process = None
        self.pid = None

    def execute(self, command: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute a command in the shell and return the result.

        Args:
            command: The command to execute
            timeout: Optional timeout in seconds

        Returns:
            Dict containing stdout, stderr, and return code
        """
        if not self.is_running():
            self.start()

        try:
            self._logger.debug(f"Executing command: {command}")

            # Clear the output buffer before sending the command
            with self._lock:
                self._output_buffer = ""

            # Send the command with a newline
            self.send_input(command + "\n")

            # Read the output
            start_time = time.time()
            output = ""

            # Wait for the command to complete
            while timeout is None or (time.time() - start_time) < timeout:
                new_output = self.read_output(timeout=0.1)
                if new_output:
                    output += new_output

                # Check if the command has completed (prompt is shown)
                if output and (output.endswith("$ ") or output.endswith("> ")):
                    break

                time.sleep(0.1)

            # Remove the command from the output
            lines = output.splitlines()
            if lines and command in lines[0]:
                output = "\n".join(lines[1:])

            return {
                "stdout": output,
                "stderr": "",  # We can't separate stdout and stderr with pty
                "returncode": 0,  # We can't easily get the return code
            }
        except Exception as e:
            self._logger.error(f"Error executing command: {e}")
            return {"stdout": "", "stderr": str(e), "returncode": 1}

    def read_output(self, timeout: Optional[float] = None) -> str:
        """Read any available output from the shell.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            str: The output from the shell
        """
        if not self.is_running():
            return ""

        with self._lock:
            if platform.system() == "Windows":
                # Windows implementation
                if not self._process:
                    return ""

                output = ""
                try:
                    # Use a non-blocking read approach for Windows
                    if self._process.stdout.readable():
                        # Read available output without blocking
                        while msvcrt.kbhit():
                            char = self._process.stdout.read(1)
                            if not char:
                                break
                            output += char
                except Exception as e:
                    self._logger.error(f"Error reading output: {e}")

                self._output_buffer += output
                return output
            else:
                # Unix implementation using pty
                if self._master_fd is None:
                    return ""

                # Check if there's any output available
                if timeout is not None:
                    ready_to_read, _, _ = select.select(
                        [self._master_fd], [], [], timeout
                    )
                    if not ready_to_read:
                        return ""

                # Read output
                output = ""
                try:
                    while True:
                        data = os.read(self._master_fd, 1024)
                        if not data:
                            break
                        output += data.decode("utf-8", errors="replace")
                except (OSError, IOError):
                    pass

                self._output_buffer += output
                return output

    def send_input(self, text: str) -> bool:
        """Send input to the shell.

        Args:
            text: The text to send to the shell

        Returns:
            bool: True if the input was sent successfully, False otherwise
        """
        if not self.is_running():
            self.start()

        try:
            if platform.system() == "Windows":
                # Windows implementation
                if not self._process or not self._process.stdin:
                    return False

                self._process.stdin.write(text)
                self._process.stdin.flush()
            else:
                # Unix implementation using pty
                if self._master_fd is None:
                    return False

                os.write(self._master_fd, text.encode("utf-8"))

            return True
        except Exception as e:
            self._logger.error(f"Error sending input: {e}")
            return False

    def change_directory(self, path: Union[str, Path]) -> bool:
        """Change the current working directory of the shell.

        Args:
            path: The path to change to

        Returns:
            bool: True if the directory was changed successfully, False otherwise
        """
        path_str = str(path)
        result = self.execute(f"cd {shlex.quote(path_str)}")

        # Update the internal cwd if the command was successful
        if result["returncode"] == 0:
            self.cwd = Path(path_str).resolve()
            return True
        return False

    def set_environment_variable(self, name: str, value: str) -> bool:
        """Set an environment variable in the shell.

        Args:
            name: The name of the environment variable
            value: The value to set

        Returns:
            bool: True if the variable was set successfully, False otherwise
        """
        if platform.system() == "Windows":
            cmd = f"set {name}={value}"
        else:
            cmd = f"export {name}={shlex.quote(value)}"

        result = self.execute(cmd)

        # Update the internal env if the command was successful
        if result["returncode"] == 0:
            self.env[name] = value
            return True
        return False

    def get_environment_variable(self, name: str) -> Optional[str]:
        """Get the value of an environment variable from the shell.

        Args:
            name: The name of the environment variable

        Returns:
            Optional[str]: The value of the environment variable, or None if it doesn't exist
        """
        if platform.system() == "Windows":
            cmd = f"echo %{name}%"
        else:
            cmd = f"echo ${name}"

        result = self.execute(cmd)

        if result["returncode"] == 0 and result["stdout"].strip():
            value = result["stdout"].strip()
            # If the variable doesn't exist, Windows will return the original
            # string
            if platform.system() == "Windows" and value == f"%{name}%":
                return None
            return value
        return None

    def is_running(self) -> bool:
        """Check if the shell process is running.

        Returns:
            bool: True if the shell is running, False otherwise
        """
        if self._process is None or self.pid is None:
            return False

        # Check if the process is still running
        try:
            if platform.system() == "Windows":
                return self._process.poll() is None
            else:
                # Check if the process exists
                os.kill(self.pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False

    @property
    def current_directory(self) -> Path:
        """Get the current working directory of the shell.

        Returns:
            Path: The current working directory
        """
        if platform.system() == "Windows":
            cmd = "cd"
        else:
            cmd = "pwd"

        result = self.execute(cmd)

        if result["returncode"] == 0 and result["stdout"].strip():
            return Path(result["stdout"].strip())
        return self.cwd  # Fall back to the stored cwd


class VideoStreamHandler(BaseHTTPRequestHandler):
    """HTTP request handler for video streaming."""

    def __init__(self, *args, computer=None, **kwargs):
        self.computer = computer
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests for video streaming."""
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            # Simple HTML page with auto-refreshing image
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Local Computer Stream</title>
                <style>
                    body {{ margin: 0; padding: 0; background: #000; }}
                    img {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
                </style>
                <meta http-equiv="refresh" content="1">
            </head>
            <body>
                <img src="/screenshot.jpg" alt="Screen Capture">
            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif self.path == "/screenshot.jpg":
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()

            # Get screenshot from the computer
            if self.computer:
                screenshot = self.computer._get_screenshot(format="PIL")
                if screenshot.image:
                    img_byte_arr = io.BytesIO()
                    screenshot.image.save(img_byte_arr, format="JPEG", quality=70)
                    self.wfile.write(img_byte_arr.getvalue())
                else:
                    # Send a blank image if screenshot failed
                    blank = Image.new("RGB", (800, 600), color="black")
                    img_byte_arr = io.BytesIO()
                    blank.save(img_byte_arr, format="JPEG")
                    self.wfile.write(img_byte_arr.getvalue())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to use the computer's logger instead of printing to stderr."""
        if self.computer and self.computer.logger:
            self.computer.logger.debug(f"VideoStreamHandler: {format % args}")


class ThreadedHTTPServer(HTTPServer):
    """Threaded HTTP server for video streaming."""

    def __init__(self, server_address, RequestHandlerClass, computer=None):
        self.computer = computer

        # Create a request handler class that includes a reference to the
        # computer
        class Handler(RequestHandlerClass):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, computer=computer, **kwargs)

        super().__init__(server_address, Handler)


class LocalComputerFile(BaseComputerFile):
    """Implementation of BaseComputerFile for local computer files.

    This class provides a direct passthrough to the built-in file object for local files.
    No temporary files or copying is used - we directly access the file in its original location.
    """

    def __init__(
        self,
        computer: "BaseComputer",
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ):
        """Initialize a local computer file.

        For local files, we directly open the file in its original location.

        Args:
            computer: The computer instance this file belongs to
            path: Path to the file on the computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)
        """
        # Store basic attributes
        self.computer = computer
        self.path = Path(path)
        self.mode = mode

        # Open the file directly
        kwargs = {}
        if encoding is not None and "b" not in mode:
            kwargs["encoding"] = encoding
        if errors is not None:
            kwargs["errors"] = errors
        if buffering != -1:
            kwargs["buffering"] = buffering

        # Just open the file directly - let the built-in open() handle all
        # errors
        self._file = open(path, mode, **kwargs)
        self._closed = False

    # Override base class methods to do nothing
    def _setup_temp_file(self):
        pass

    def _copy_from_computer(self):
        pass

    def _copy_to_computer(self):
        pass

    def _open_temp_file(self):
        pass

    # Delegate all file operations directly to the underlying file object
    def read(self, size=None):
        return self._file.read() if size is None else self._file.read(size)

    def write(self, data):
        return self._file.write(data)

    def seek(self, offset, whence=0):
        return self._file.seek(offset, whence)

    def tell(self):
        return self._file.tell()

    def flush(self):
        self._file.flush()

    def close(self):
        if not self._closed:
            self._file.close()
            self._closed = True

    def readable(self):
        return self._file.readable()

    def writable(self):
        return self._file.writable()

    def seekable(self):
        return self._file.seekable()

    def readline(self, size=-1):
        return self._file.readline(size)

    def readlines(self, hint=-1):
        return self._file.readlines(hint)

    def writelines(self, lines):
        self._file.writelines(lines)

    def __iter__(self):
        return self._file.__iter__()

    def __next__(self):
        return self._file.__next__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class LocalComputer(BaseComputer):
    """Base class for local computer implementations.

    This class provides common functionality for local computer implementations
    such as screenshot capture, command execution, and basic resource management.
    """

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
        return True

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
        return True

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> ScreenshotObservation:
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

    def _execute_shell_command(self, action: ShellCommandAction):
        """Execute a system command using subprocess."""
        self.logger.info(f"Executing command: {action.command}")
        result = subprocess.run(
            action.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=action.timeout if action.timeout is not None else 10,
        )
        if result.returncode == 0:
            self.logger.info("Command executed successfully")
        else:
            self.logger.warning(
                f"Command returned non-zero exit code: {result.returncode}"
            )
            raise RuntimeError(
                f"Command returned non-zero exit code: {result.returncode}"
            )

    def _run_process(self, action: RunProcessAction) -> bool:
        """Run a process with the specified parameters.

        Args:
            action: RunProcessAction containing the process parameters

        Returns:
            bool: True if the process was executed successfully
        """
        self.logger.info(
            f"Running process: {
                action.command} with args: {
                action.args}"
        )

        # Prepare environment variables
        env = os.environ.copy()
        if action.env:
            env.update(action.env)

        # Run the process
        result = subprocess.run(
            [action.command] + action.args,
            cwd=action.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=action.timeout,
        )

        if result.returncode == 0:
            self.logger.info("Process executed successfully")
            return True
        else:
            self.logger.warning(
                f"Process returned non-zero exit code: {result.returncode}"
            )
            raise RuntimeError(
                f"Process returned non-zero exit code: {result.returncode}"
            )

    def _pause(self):
        """Pause the local computer.

        For local computers, pausing doesn't have a specific implementation
        as it's running on the local machine.
        """
        self.logger.info(f"Pausing {self.__class__.__name__} (no-op)")
        # No specific pause implementation for local computers

    def _resume(self, timeout_hours: Optional[float] = None):
        """Resume the local computer.

        For local computers, resuming doesn't have a specific implementation
        as it's running on the local machine.

        Args:
            timeout_hours: Not used for local computer implementations.
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

        try:
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
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error starting Jupyter notebook server: {e}")
            self._jupyter_server_pid = None
            return False

    def stop_jupyter_server(self):
        """Stop the running Jupyter notebook server if one exists."""
        if self._jupyter_server_pid is None:
            self.logger.info("No Jupyter server is running")
            return True

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
            return True
        except psutil.NoSuchProcess:
            self.logger.info("Jupyter notebook server process no longer exists")
            self._jupyter_server_pid = None
            return True
        except Exception as e:
            self.logger.error(f"Error stopping Jupyter notebook server: {e}")
            return False

    def create_shell(
        self,
        executable: str = DEFAULT_SHELL_EXECUTIBLE,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> LocalShell:
        """Create and return a new LocalShell instance.

        This method creates a persistent shell that can be used to execute commands
        and interact with the system shell environment.

        Args:
            executable: Path to the shell executable to use
            cwd: Initial working directory for the shell
            env: Environment variables to set in the shell

        Returns:
            LocalShell: A shell instance for executing commands and interacting with the shell
        """
        self.logger.info(f"Creating new shell with executable: {executable}")
        shell = LocalShell(
            executable=executable,
            cwd=cwd,
            env=env,
            logger=self.logger.getChild("shell"),
        )

        # Start the shell
        if shell.start():
            self.logger.info(
                f"Shell started successfully with PID: {
                    shell.pid}"
            )
            return shell
        else:
            self.logger.error("Failed to start shell")
            raise RuntimeError("Failed to start shell")

    def _find_free_port(self) -> int:
        """Find a free port to use for the video server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the local computer instance.

        Returns:
            str: The URL for the video stream, or an empty string if video streaming is not active.
        """
        if self._video_streaming and self._video_server_port:
            return f"http://localhost:{self._video_server_port}/"
        return ""

    def start_video_stream(self) -> bool:
        """Start the video stream for the local computer instance.

        This starts a simple HTTP server that serves screenshots as a video stream.

        Returns:
            bool: True if the video stream was successfully started, False otherwise.
        """
        if self._video_streaming:
            self.logger.info("Video stream is already running")
            return True

        try:
            # Find a free port
            port = self._find_free_port()
            self._video_server_port = port

            # Create and start the HTTP server
            self.logger.info(f"Starting video stream server on port {port}")
            server = ThreadedHTTPServer(
                ("localhost", port), VideoStreamHandler, computer=self
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

            self.logger.info(f"Video stream started at http://localhost:{port}/")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start video stream: {e}")
            self._video_streaming = False
            self._video_server = None
            self._video_server_thread = None
            self._video_server_port = None
            return False

    def stop_video_stream(self) -> bool:
        """Stop the video stream for the local computer instance.

        Returns:
            bool: True if the video stream was successfully stopped, False otherwise.
        """
        if not self._video_streaming:
            self.logger.info("No video stream is running")
            return True

        try:
            if self._video_server:
                self.logger.info("Stopping video stream server")
                self._video_server.shutdown()
                self._video_server.server_close()
                self._video_server = None
                self._video_server_thread = None
                self._video_streaming = False
                self.logger.info("Video stream stopped")
                return True
        except Exception as e:
            self.logger.error(f"Error stopping video stream: {e}")
            return False

        return False

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
