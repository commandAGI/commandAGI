import logging
import os
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from io import FileIO
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TypeAlias,
    TypedDict,
    Union,
)

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from commandAGI._internal.config import APPDIR, DEV_MODE
from commandAGI._utils.annotations import annotation, gather_annotated_attr_keys
from commandAGI._utils.counter import next_for_cls
from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE
from commandAGI.types import (
    ComputerActionType,
    ComputerActionUnion,
    DisplayInfo,
    KeyboardKey,
    MouseButton,
    ProcessInfo,
    RunProcessAction,
    ShellCommandAction,
    WindowInfo,
)


class RunningState(Enum, str):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


# Platform enumeration
class Platform(str, Enum):
    """Operating system platform."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

    @classmethod
    def is_valid_button(cls, button: str) -> bool:
        """Check if a string is a valid mouse button."""
        return button in [b.value for b in cls]


class KeyboardKey(str, Enum):
    # Special Keys
    ENTER = "enter"
    TAB = "tab"
    SPACE = "space"
    BACKSPACE = "backspace"
    DELETE = "delete"
    ESCAPE = "escape"
    HOME = "home"
    END = "end"
    PAGE_UP = "pageup"
    PAGE_DOWN = "pagedown"

    # Arrow Keys
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    # Modifier Keys - generic and with left/right differentiation
    SHIFT = "shift"
    CTRL = "ctrl"
    LCTRL = "lctrl"
    RCTRL = "rctrl"
    ALT = "alt"
    LALT = "lalt"
    RALT = "ralt"
    META = "meta"  # Generic / non-specified meta key
    LMETA = "lmeta"
    RMETA = "rmeta"

    # Function Keys F1 - F12
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"

    # Common Alphabet Keys A - Z
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"

    # Number Keys 0 - 9 (using NUM_x naming)
    NUM_0 = "0"
    NUM_1 = "1"
    NUM_2 = "2"
    NUM_3 = "3"
    NUM_4 = "4"
    NUM_5 = "5"
    NUM_6 = "6"
    NUM_7 = "7"
    NUM_8 = "8"
    NUM_9 = "9"

    @classmethod
    def is_valid_key(cls, key: Union["KeyboardKey", str]) -> bool:
        """Check if a string is a valid keyboard key."""
        if isinstance(key, KeyboardKey):
            return True
        return key in [k.value for k in cls]


# Define component tree types
class UIElementCommonProperties(TypedDict, total=False):
    """Common properties of a UI element across all platforms."""

    name: Optional[str]  # Name/label of the element
    # Role/type of the element (normalized across platforms)
    role: Optional[str]
    value: Optional[Any]  # Current value of the element
    description: Optional[str]  # Description of the element

    # State properties
    enabled: Optional[bool]  # Whether the element is enabled
    focused: Optional[bool]  # Whether the element has keyboard focus
    visible: Optional[bool]  # Whether the element is visible
    offscreen: Optional[bool]  # Whether the element is off-screen

    # Position and size
    bounds: Optional[Dict[str, int]]  # {left, top, width, height}

    # Control-specific properties
    selected: Optional[bool]  # Whether the element is selected
    checked: Optional[bool]  # Whether the element is checked
    expanded: Optional[bool]  # Whether the element is expanded

    # For elements with range values (sliders, progress bars)
    current_value: Optional[float]  # Current value
    min_value: Optional[float]  # Minimum value
    max_value: Optional[float]  # Maximum value
    percentage: Optional[float]  # Value as percentage


class UIElement(TypedDict):
    """A UI element in the accessibility tree."""

    # Common properties normalized across platforms
    properties: UIElementCommonProperties
    # Platform-specific properties
    platform: Platform  # The platform this element was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties
    # Child elements
    children: List["UIElement"]


# Define process information type
class ProcessInfo(TypedDict):
    """Information about a running process."""

    # Common properties across platforms
    pid: int  # Process ID
    name: str  # Process name
    cpu_percent: float  # CPU usage percentage
    memory_mb: float  # Memory usage in MB
    status: str  # Process status (running, sleeping, etc.)
    # Platform-specific properties
    platform: Platform  # The platform this process was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties


# Define window information type
class WindowInfo(TypedDict):
    """Information about a window."""

    # Common properties across platforms
    title: str  # Window title
    bounds: Dict[str, int]  # {left, top, width, height}
    minimized: bool  # Whether the window is minimized
    maximized: bool  # Whether the window is maximized
    focused: bool  # Whether the window has focus
    # Platform-specific properties
    platform: Platform  # The platform this window was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties


# Define display information type
class DisplayInfo(TypedDict):
    """Information about a display."""

    # Common properties across platforms
    id: int  # Display ID
    bounds: Dict[str, int]  # {left, top, width, height}
    is_primary: bool  # Whether this is the primary display
    # Platform-specific properties
    platform: Platform  # The platform this display was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties


class SystemInfo(BaseModel):
    """Information about the system."""

    cpu_usage: float = Field(
        description="CPU usage percentage from system monitoring APIs"
    )
    memory_usage: float = Field(
        description="Memory usage percentage from system monitoring APIs"
    )
    disk_usage: float = Field(description="Disk usage percentage from filesystem APIs")
    uptime: float = Field(description="System uptime in seconds")
    hostname: str = Field(description="System hostname")
    ip_address: str = Field(description="Primary IP address from network interfaces")
    user: str = Field(description="Current username")
    os: str = Field(description="Operating system name")
    version: str = Field(description="Operating system version")
    architecture: str = Field(description="CPU architecture (x86_64, arm64, etc.)")


class BaseJupyterNotebook(BaseModel):
    """Base class for Jupyter notebook operations.

    This class defines the interface for working with Jupyter notebooks programmatically.
    Implementations should provide methods to create, read, modify, and execute notebooks.
    """

    model_config = {"arbitrary_types_allowed": True}

    notebook_path: Optional[Path] = None

    def create_notebook(self) -> Dict[str, Any]:
        """Create a new empty notebook and return the notebook object."""
        raise NotImplementedError("Subclasses must implement create_notebook")

    def read_notebook(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Read a notebook from a file and return the notebook object."""
        raise NotImplementedError("Subclasses must implement read_notebook")

    def save_notebook(
        self, notebook: Dict[str, Any], path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Save the notebook to a file and return the path."""
        raise NotImplementedError("Subclasses must implement save_notebook")

    def add_markdown_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a markdown cell to the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement add_markdown_cell")

    def add_code_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a code cell to the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement add_code_cell")

    def update_cell(
        self, notebook: Dict[str, Any], index: int, source: str
    ) -> Dict[str, Any]:
        """Update the source of a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement update_cell")

    def remove_cell(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Remove a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement remove_cell")

    def list_cells(self, notebook: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return a list of cells in the notebook."""
        raise NotImplementedError("Subclasses must implement list_cells")

    def execute_notebook(
        self, notebook: Dict[str, Any], timeout: int = 600
    ) -> Dict[str, Any]:
        """Execute all cells in the notebook and return the executed notebook."""
        raise NotImplementedError("Subclasses must implement execute_notebook")

    def execute_cell(
        self, notebook: Dict[str, Any], index: int, timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a specific cell in the notebook and return the executed notebook."""
        raise NotImplementedError("Subclasses must implement execute_cell")

    def get_cell_output(
        self, notebook: Dict[str, Any], index: int
    ) -> List[Dict[str, Any]]:
        """Return the output of a cell at the given index."""
        raise NotImplementedError("Subclasses must implement get_cell_output")

    def clear_cell_output(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Clear the output of a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement clear_cell_output")

    def clear_all_outputs(self, notebook: Dict[str, Any]) -> Dict[str, Any]:
        """Clear the outputs of all cells in the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement clear_all_outputs")


class BaseShell(BaseModel):
    """Base class for shell operations.

    This class defines the interface for working with a persistent shell/terminal session.
    Implementations should provide methods to execute commands and manage the shell environment.
    """

    model_config = {"arbitrary_types_allowed": True}

    executable: str = DEFAULT_SHELL_EXECUTIBLE
    cwd: Optional[Path] = None
    env: Dict[str, str] = Field(default_factory=dict)
    pid: Optional[int] = None
    _logger: Optional[logging.Logger] = None

    def start(self) -> bool:
        """Start the shell process.

        Returns:
            bool: True if the shell was started successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement start")

    def stop(self) -> bool:
        """Stop the shell process.

        Returns:
            bool: True if the shell was stopped successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement stop")

    def execute(self, command: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute a command in the shell and return the result.

        Args:
            command: The command to execute
            timeout: Optional timeout in seconds

        Returns:
            Dict containing stdout, stderr, and return code
        """
        raise NotImplementedError("Subclasses must implement execute")

    def read_output(self, timeout: Optional[float] = None) -> str:
        """Read any available output from the shell.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            str: The output from the shell
        """
        raise NotImplementedError("Subclasses must implement read_output")

    def send_input(self, text: str) -> bool:
        """Send input to the shell.

        Args:
            text: The text to send to the shell

        Returns:
            bool: True if the input was sent successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send_input")

    def change_directory(self, path: Union[str, Path]) -> bool:
        """Change the current working directory of the shell.

        Args:
            path: The path to change to

        Returns:
            bool: True if the directory was changed successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement change_directory")

    def set_environment_variable(self, name: str, value: str) -> bool:
        """Set an environment variable in the shell.

        Args:
            name: The name of the environment variable
            value: The value to set

        Returns:
            bool: True if the variable was set successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement set_environment_variable")

    def get_environment_variable(self, name: str) -> Optional[str]:
        """Get the value of an environment variable from the shell.

        Args:
            name: The name of the environment variable

        Returns:
            Optional[str]: The value of the environment variable, or None if it doesn't exist
        """
        raise NotImplementedError("Subclasses must implement get_environment_variable")

    def is_running(self) -> bool:
        """Check if the shell process is running.

        Returns:
            bool: True if the shell is running, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_running")

    @property
    def current_directory(self) -> Path:
        """Get the current working directory of the shell.

        Returns:
            Path: The current working directory
        """
        raise NotImplementedError("Subclasses must implement current_directory")


class BaseComputerFile(FileIO, ABC):
    """Base class for computer-specific file implementations.

    This class provides a file-like interface for working with files on remote computers.
    It mimics the built-in file object API to allow for familiar usage patterns.

    The implementation copies the file from the computer to a local temporary directory,
    performs operations on the local copy, and syncs changes back to the computer
    when flushing or closing the file.
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
        # Store basic attributes
        self.computer = computer
        self.path = Path(path)
        self.mode = mode
        self._closed = False
        self._modified = False

        # Create a unique filename in the temp directory
        import os

        temp_filename = f"{hash(str(self.path))}-{os.path.basename(self.path)}"
        self._temp_path = Path(self.computer.temp_dir) / temp_filename

        # Copy from remote to local temp file if needed
        if "r" in mode or "a" in mode or "+" in mode:
            try:
                if self.path.exists():
                    self.computer._copy_from_computer(self.path, self._temp_path)
            except Exception as e:
                if "r" in mode and not ("+" in mode or "a" in mode or "w" in mode):
                    # If we're only reading, this is an error
                    raise IOError(f"Could not copy file from computer: {e}")
                # Otherwise, we'll create a new file

        # Open the file
        kwargs = {}
        if encoding is not None and "b" not in mode:
            kwargs["encoding"] = encoding
        if errors is not None:
            kwargs["errors"] = errors
        if buffering != -1:
            kwargs["buffering"] = buffering

        self._file = open(self._temp_path, mode, **kwargs)

    def read(self, size=None):
        """Read from the file."""
        return self._file.read() if size is None else self._file.read(size)

    def write(self, data):
        """Write to the file."""
        self._modified = True
        return self._file.write(data)

    def seek(self, offset, whence=0):
        """Change the stream position."""
        return self._file.seek(offset, whence)

    def tell(self):
        """Return the current stream position."""
        return self._file.tell()

    def flush(self):
        """Flush the write buffers and sync changes back to the computer."""
        self._file.flush()
        if self.writable() and self._modified:
            try:
                # Ensure the directory exists
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.computer._copy_to_computer(self._temp_path, self.path)
                self._modified = False
            except Exception as e:
                raise IOError(f"Could not copy file to computer: {e}")

    def close(self):
        """Close the file and sync changes back to the computer."""
        if not self._closed:
            self.flush()
            self._file.close()
            self._closed = True

    def readable(self):
        """Return True if the file can be read."""
        return self._file.readable()

    def writable(self):
        """Return True if the file can be written."""
        return self._file.writable()

    def seekable(self):
        """Return True if the file supports random access."""
        return self._file.seekable()

    def readline(self, size=-1):
        """Read until newline or EOF."""
        return self._file.readline(size)

    def readlines(self, hint=-1):
        """Read until EOF using readline() and return a list of lines."""
        return self._file.readlines(hint)

    def writelines(self, lines):
        """Write a list of lines to the file."""
        self._modified = True
        self._file.writelines(lines)

    def __iter__(self):
        """Return an iterator over the file's lines."""
        return self._file.__iter__()

    def __next__(self):
        """Return the next line from the file."""
        return self._file.__next__()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class BaseComputer(BaseModel):

    model_config = {"arbitrary_types_allowed": True}

    name: str
    _state: RunningState = "stopped"
    logger: Optional[logging.Logger] = None
    _file_handler: Optional[logging.FileHandler] = None
    num_retries: int = 3
    error_handling: Literal["raise", "pass"] = "raise"

    def __init__(self, name=None, **kwargs):
        name = (
            name
            or f"{self.__class__.__name__}-{next_for_cls(self.__class__.__name__):03d}"
        )
        super().__init__(name=name, **kwargs)

        # Initialize logger
        self.logger = logging.getLogger(f"commandAGI.computers.{self.name}")
        self.logger.setLevel(logging.INFO)

    @annotation("endpoint", {})
    def start(self):
        """Start the computer."""
        if self._state == "running":
            self.logger.warning("Computer is already started")
            return
        elif self._state == "paused":
            self.logger.info("Resuming paused computer")
            self.resume()
            return

        # Ensure artifact directory exists
        os.makedirs(self.artifact_dir, exist_ok=True)

        # Setup file handler for logging if not already set up
        if not self._file_handler:
            self._file_handler = logging.FileHandler(self.logfile_path)
            self._file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            self._file_handler.setFormatter(formatter)
            self.logger.addHandler(self._file_handler)

        self.logger.info(f"Starting {self.__class__.__name__} computer")
        self._start()
        self._state = RunningState.RUNNING
        self.logger.info(f"{self.__class__.__name__} computer started successfully")

    def _start(self):
        """Start the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.start")

    @annotation("endpoint", {})
    def stop(self):
        """Stop the computer."""
        if self._state == "stopped":
            self.logger.warning("Computer is already stopped")
            return

        if self._state == "paused":
            self.logger.info("Computer is paused, stopping anyway")

        self.logger.info(f"Stopping {self.__class__.__name__} computer")
        self._stop()
        self._state = RunningState.STOPPED

        # Close and remove the file handler
        if self._file_handler:
            self.logger.info(f"{self.__class__.__name__} computer stopped successfully")
            self._file_handler.close()
            self.logger.removeHandler(self._file_handler)
            self._file_handler = None

    def _stop(self):
        """Stop the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.stop")

    @annotation("endpoint", {})
    def pause(self) -> bool:
        """Pause the computer.

        This method pauses the computer, which means it's still running but in a suspended state.

        Returns:
            bool: True if the computer was successfully paused, False otherwise.
        """
        if self._state != "running":
            self.logger.warning(f"Cannot pause computer in {self._state} state")
            return False

        self.logger.info(
            f"Attempting to pause {
                self.__class__.__name__} computer"
        )
        for attempt in range(self.num_retries):
            try:
                self._pause()
                self._state = RunningState.PAUSED
                self.logger.info(
                    f"{self.__class__.__name__} computer paused successfully"
                )
                return True
            except Exception as e:
                self.logger.error(
                    f"Error pausing computer (attempt {attempt + 1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _pause(self):
        """Implementation of pause functionality.

        This method should be overridden by subclasses to implement computer-specific pause functionality.
        The default implementation does nothing.
        """
        self.logger.debug("Pause not implemented for this computer type")
        pass

    @annotation("endpoint", {})
    def resume(self) -> bool:
        """Resume a paused computer."""
        if self._state != "paused":
            self.logger.warning(
                f"Cannot resume computer in {
                    self._state} state"
            )
            return False

        self.logger.info(f"Attempting to resume {self.__class__.__name__} computer")
        self._resume()
        self._state = RunningState.RUNNING
        self.logger.info(f"{self.__class__.__name__} computer resumed successfully")

    def _resume(self):
        """Implementation of resume functionality.

        This method should be overridden by subclasses to implement computer-specific resume functionality.
        The default implementation does nothing.
        """
        self.logger.debug("Resume not implemented for this computer type")
        pass

    @annotation("endpoint", {"use_getter": True, "use_setter": True})
    @property
    def state(self) -> RunningState:
        return self._state

    @state.setter
    def state(self, value: RunningState):
        self.ensure_running_state(value)

    @annotation("endpoint", {})
    def ensure_running_state(self, target_state: RunningState):
        """Ensure the computer is in the specified state.

        Args:
            target_state: The desired state ("running", "paused", or "stopped")
        """
        match (self._state, target_state):

            # Transitions to running state
            case ("running", "running"):
                pass
            case ("stopped", "running"):
                self.start()
            case ("paused", "running"):
                self.resume()

            # Transitions to paused state
            case ("running", "paused"):
                self.pause()
            case ("paused", "paused"):
                pass
            case ("stopped", "paused"):
                self.start()
                self.pause()

            # Transitions to stopped state
            case ("running", "stopped"):
                self.stop()
            case ("paused", "stopped"):
                self.stop()
            case ("stopped", "stopped"):
                pass

            # Invalid states/transitions
            case (current, target):
                raise ValueError(f"Invalid state transition: {current} -> {target}")

    @annotation("endpoint", {})
    def reset_state(self):
        """Reset the computer state. If you just need ot reset the computer state without a full off-on, use this method. NOTE: in most cases, we just do a full off-on"""
        self.logger.info(f"Resetting {self.__class__.__name__} computer state")
        self.stop()
        self.start()

    _temp_dir: str = None

    @annotation("endpoint", {"use_getter": True})
    @property
    def temp_dir(self) -> Path:
        """Get or create a temporary directory for this computer.

        This property ensures that a temporary directory exists for file operations
        and returns the path to it.

        Returns:
            Path: The path to the temporary directory
        """
        if not self._temp_dir:
            self._temp_dir = tempfile.mkdtemp()
        return Path(self._temp_dir)

    _has_created_artifact_dir = False

    @annotation("endpoint", {"use_getter": True})
    @property
    def artifact_dir(self) -> Path:
        artifact_dir_path = APPDIR / self.name

        if not self._has_created_artifact_dir and not artifact_dir_path.exists():
            artifact_dir_path.mkdir(parents=True, exist_ok=True)
            self._has_created_artifact_dir = True
        return artifact_dir_path

    @annotation("endpoint", {"use_getter": True})
    @property
    def logfile_path(self) -> Path:
        return self.artifact_dir / "logfile.log"

    @property
    def _new_screenshot_name(self) -> Path:
        return self.artifact_dir / f"screenshot-{datetime.now():%Y-%m-%d_%H-%M-%S-%f}"

    @annotation("endpoint", {})
    @annotation("mcp_tool", {})
    def wait(self, timeout: float = 5.0) -> bool:
        """Waits a specified amount of time"""
        time.sleep(timeout)
        return True

    @property
    def screenshot(self) -> Union[str, Image.Image, Path]:
        """Get a screenshot of the current display."""
        return self.get_screenshot()

    @annotation("endpoint", {"method": "get", "path": "/screenshot"})
    @annotation("mcp_resource", {"resource_name": "screenshot"})
    def get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> Union[str, Image.Image, Path]:
        """Return a screenshot in the specified format.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        return self._execute_with_retry(
            "get_screenshot",
            self._get_screenshot,
            display_id=display_id,
            format=format,
        )

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> Union[str, Image.Image, Path]:
        """Get a screenshot of the current state.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        raise NotImplementedError(f"{self.__class__.__name__}.get_screenshot")

    @annotation("endpoint", {"use_getter": True, "use_setter": True})
    @property
    def mouse_position(self) -> tuple[int, int]:
        return self.get_mouse_position()

    @mouse_position.setter
    def mouse_position(self, value: tuple[int, int]):
        x, y = value
        self.move(x=x, y=y, duration=0.0)

    @annotation("mcp_resource", {"resource_name": "mouse_position"})
    def get_mouse_position(self) -> tuple[int, int]:
        """Get the current mouse position."""
        return self._execute_with_retry("get_mouse_position", self._get_mouse_position)

    def _get_mouse_position(self) -> tuple[int, int]:
        """Get the current mouse position."""
        raise NotImplementedError(f"{self.__class__.__name__}.get_mouse_position")

    @property
    def mouse_button_states(self) -> dict[str, bool | None]:
        return self.get_mouse_button_states()

    @mouse_button_states.setter
    def mouse_button_states(self, value: dict[str, bool | None]):
        for button_name, button_state in value.items():
            if button_state is True:
                self.mouse_down(button=MouseButton[button_name.upper()])
            elif button_state is False:
                self.mouse_up(button=MouseButton[button_name.upper()])

    @annotation("endpoint", {"method": "get", "path": "/mouse_button_states"})
    @annotation("mcp_resource", {"resource_name": "mouse_button_states"})
    def get_mouse_button_states(self) -> dict[str, bool | None]:
        """Get the current state of mouse buttons."""
        return self._execute_with_retry(
            "get_mouse_button_states", self._get_mouse_button_states
        )

    def _get_mouse_button_states(self) -> dict[str, bool | None]:
        """Get the current state of mouse buttons."""
        raise NotImplementedError(f"{self.__class__.__name__}.get_mouse_button_states")

    @property
    def keyboard_key_states(self) -> dict[KeyboardKey, bool]:
        """Get the current state of all keyboard keys."""
        return self.get_keyboard_key_states()

    @keyboard_key_states.setter
    def keyboard_key_states(self, value: dict[str, bool | None]):
        """Set the state of keyboard keys.

        Args:
            value: Dictionary mapping key names to their states (True for pressed, False for released)
        """
        for key_name, key_state in value.items():
            if key_state is True:
                self.keydown(key=KeyboardKey[key_name.upper()])
            elif key_state is False:
                self.keyup(key=KeyboardKey[key_name.upper()])

    @annotation("endpoint", {"method": "get", "path": "/keyboard_key_states"})
    @annotation("mcp_resource", {"resource_name": "keyboard_key_states"})
    def get_keyboard_key_states(self) -> dict[KeyboardKey, bool]:
        """Get the current state of keyboard keys."""
        return self._execute_with_retry(
            "get_keyboard_key_states", self._get_keyboard_key_states
        )

    def _get_keyboard_key_states(self) -> dict[KeyboardKey, bool]:
        """Get the current state of keyboard keys."""
        raise NotImplementedError(f"{self.__class__.__name__}.get_keyboard_key_states")

    @property
    def keys_down(self) -> list[KeyboardKey]:
        """Get a list of currently pressed keyboard keys."""
        return [
            key for key, is_pressed in self.keyboard_key_states.items() if is_pressed
        ]

    @keys_down.setter
    def keys_down(self, value: list[KeyboardKey]):
        """Set which keyboard keys are pressed.

        This will release any currently pressed keys not in the new list,
        and press any new keys in the list that weren't already pressed.

        Args:
            value: List of KeyboardKey values that should be pressed
        """
        # Get current pressed keys
        current = set(self.keys_down)
        target = set(value)

        # Release keys that should no longer be pressed
        for key in current - target:
            self.keyup(key=key)

        # Press new keys that should be pressed
        for key in target - current:
            self.keydown(key=key)

    @property
    def keys_up(self) -> list[KeyboardKey]:
        """Get a list of currently released keyboard keys."""
        return [
            key
            for key, is_pressed in self.keyboard_key_states.items()
            if not is_pressed
        ]

    @keys_up.setter
    def keys_up(self, value: list[KeyboardKey]):
        """Set which keyboard keys are released.

        This will press any currently released keys not in the new list,
        and release any keys in the list that weren't already released.

        Args:
            value: List of KeyboardKey values that should be released
        """
        # Get current released keys
        current = set(self.keys_up)
        target = set(value)

        # Press keys that should no longer be released
        for key in current - target:
            self.keydown(key=key)

        # Release new keys that should be released
        for key in target - current:
            self.keyup(key=key)

    @property
    def processes(self) -> List[ProcessInfo]:
        """Get information about running processes."""
        return self.get_processes()

    @annotation("endpoint", {"method": "get", "path": "/processes"})
    @annotation("mcp_resource", {"resource_name": "processes"})
    def get_processes(self) -> List[ProcessInfo]:
        """Get information about running processes."""
        return self._execute_with_retry("get_processes", self._get_processes)

    def _get_processes(self) -> List[ProcessInfo]:
        """Get information about running processes."""
        raise NotImplementedError(f"{self.__class__.__name__}._get_processes")

    @property
    def windows(self) -> List[WindowInfo]:
        """Get information about open windows."""
        return self.get_windows()

    @annotation("endpoint", {"method": "get", "path": "/windows"})
    @annotation("mcp_resource", {"resource_name": "windows"})
    def get_windows(self) -> List[WindowInfo]:
        """Get information about open windows."""
        return self._execute_with_retry("get_windows", self._get_windows)

    def _get_windows(self) -> List[WindowInfo]:
        """Get information about open windows."""
        raise NotImplementedError(f"{self.__class__.__name__}._get_windows")

    @property
    def displays(self) -> List[DisplayInfo]:
        """Get information about connected displays."""
        return self.get_displays()

    @annotation("endpoint", {"method": "get", "path": "/displays"})
    @annotation("mcp_resource", {"resource_name": "displays"})
    def get_displays(self) -> List[DisplayInfo]:
        """Get information about connected displays."""
        return self._execute_with_retry("get_displays", self._get_displays)

    def _get_displays(self) -> List[DisplayInfo]:
        """Get information about connected displays."""
        raise NotImplementedError(f"{self.__class__.__name__}._get_displays")

    @property
    def layout_tree(self) -> UIElement:
        """Get the current UI layout tree."""
        return self.get_layout_tree()

    @annotation("endpoint", {"method": "get", "path": "/layout_tree"})
    @annotation("mcp_resource", {"resource_name": "layout_tree"})
    def get_layout_tree(self) -> UIElement:
        """Return a LayoutTreeObservation containing the accessibility tree of the current UI."""
        return self._execute_with_retry("get_layout_tree", self._get_layout_tree)

    def _get_layout_tree(self) -> UIElement:
        """Get the UI layout tree.

        Returns:
            LayoutTreeObservation containing UI component hierarchy
        """
        raise NotImplementedError(f"{self.__class__.__name__}._get_layout_tree")

    @property
    def sysinfo(self) -> SystemInfo:
        """Get information about the system."""
        return self.get_sysinfo()

    @annotation("endpoint", {"method": "get", "path": "/sysinfo"})
    @annotation("mcp_resource", {"resource_name": "sysinfo"})
    def get_sysinfo(self) -> SystemInfo:
        """Get information about the system."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_sysinfo()
        except Exception as e:
            self.logger.error(f"Error getting sysinfo: {e}")

    def _get_sysinfo(self) -> SystemInfo:
        """Get system information.

        Returns:
            SystemInfo object containing system metrics and details
        """
        raise NotImplementedError(f"{self.__class__.__name__}._get_sysinfo")

    _jupyter_server_pid: int | None = None

    @annotation("endpoint", {"method": "post", "path": "/start_jupyter_server"})
    def start_jupyter_server(
        self, port: int = 8888, notebook_dir: Optional[str] = None
    ):
        """Start a Jupyter notebook server.

        Args:
            port: Port number to run the server on
            notebook_dir: Directory to serve notebooks from. If None, uses current directory.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_jupyter_server")

    @annotation("endpoint", {"method": "post", "path": "/stop_jupyter_server"})
    def stop_jupyter_server(self):
        """Stop the running Jupyter notebook server if one exists."""
        raise NotImplementedError(f"{self.__class__.__name__}.stop_jupyter_server")

    @annotation("endpoint", {"method": "post", "path": "/create_jupyter_notebook"})
    def create_jupyter_notebook(self) -> BaseJupyterNotebook:
        """Create and return a new BaseJupyterNotebook instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseJupyterNotebook for the specific computer type.

        Returns:
            BaseJupyterNotebook: A notebook client instance for creating and manipulating notebooks.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.create_jupyter_notebook")

    @annotation("endpoint", {"method": "post", "path": "/run_process"})
    @annotation("mcp_tool", {"tool_name": "run_process"})
    def run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Run a process with the specified parameters and return True if successful."""
        return self._execute_with_retry(
            "run_process",
            self._run_process,
            RunProcessAction(
                command=command, args=args, cwd=cwd, env=env, timeout=timeout
            ),
        )

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Run a process with the specified parameters.

        Args:
            command: The command to run
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables for the process
            timeout: Optional timeout in seconds

        Returns:
            bool: True if process executed successfully
        """
        raise NotImplementedError(f"{self.__class__.__name__}._run_process")

    def _default_run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Default implementation of run_process using shell commands.

        This method is deliberately not wired up to the base _run_process to make
        subclasses think about what they really want. It defaults to using shell
        commands to execute the process.

        Args:
            command: The command to run
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables for the process
            timeout: Optional timeout in seconds

        Returns:
            bool: True if the process was executed successfully
        """
        self.logger.info(f"Running process via shell: {command} with args: {args}")

        # Change to the specified directory if provided
        if cwd:
            self.shell(f"cd {cwd}")

        # Build the command string
        cmd_parts = [command] + args
        cmd_shell_format = " ".join(cmd_parts)

        # Add environment variables if specified
        if env:
            # For Unix-like shells
            env_vars = " ".join([f"{k}={v}" for k, v in env.items()])
            cmd_shell_format = f"{env_vars} {cmd_shell_format}"

        # Execute the command with timeout if specified
        return self.shell(cmd_shell_format, timeout=timeout)

    @annotation("endpoint", {"method": "post", "path": "/create_shell"})
    def create_shell(
        self,
        executable: str = None,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> BaseShell:
        """Create and return a new shell instance.

        This method creates a persistent shell that can be used to execute commands
        and interact with the system shell environment.

        Args:
            executable: Path to the shell executable to use
            cwd: Initial working directory for the shell
            env: Environment variables to set in the shell

        Returns:
            BaseShell: A shell instance for executing commands and interacting with the shell
        """
        raise NotImplementedError(f"{self.__class__.__name__}.create_shell")

    @annotation("endpoint", {"method": "post", "path": "/shell"})
    @annotation("mcp_tool", {"tool_name": "shell"})
    def shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executible: Optional[str] = None,
    ) -> bool:
        """Execute a system command in the global shell environment and return True if successful.

        NOTE: its generally a better idea to use `create_shell` so you can run your shell in a separate processon the host machine
        (but also not that some computer shell implementations actually shove it all back into the system_shell and only pretend to be multiprocessed lol)

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """
        return self._execute_with_retry(
            "shell command",
            self._shell,
            ShellCommandAction(command=command, timeout=timeout, executible=executible),
        )

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executible: Optional[str] = None,
    ) -> bool:
        """Execute a shell command.

        Args:
            command: The command to execute
            timeout: Optional timeout in seconds
            executable: Optional shell executable to use
        """
        raise NotImplementedError(f"{self.__class__.__name__}.execute_shell_command")

    @annotation("endpoint", {"method": "post", "path": "/keypress"})
    @annotation("mcp_tool", {"tool_name": "keypress"})
    def keypress(self, key: KeyboardKey, duration: float = 0.1) -> bool:
        """Execute pressing a keyboard key with a specified duration."""
        return self._execute_with_retry(
            "keyboard key press",
            self._keypress,
            key,
            duration,
        )

    def _keypress(self, key: KeyboardKey, duration: float = 0.1):
        """Execute pressing a keyboard key with a specified duration."""
        self.keydown(key)
        time.sleep(duration)
        self.keyup(key)

    @annotation("endpoint", {"method": "post", "path": "/keydown"})
    @annotation("mcp_tool", {"tool_name": "keydown"})
    def keydown(self, key: KeyboardKey) -> bool:
        """Execute key down for a keyboard key."""
        return self._execute_with_retry(
            "keyboard key down",
            self._keydown,
            key,
        )

    def _keydown(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        raise NotImplementedError(f"{self.__class__.__name__}.keydown")

    @annotation("endpoint", {"method": "post", "path": "/keyup"})
    @annotation("mcp_tool", {"tool_name": "keyup"})
    def keyup(self, key: KeyboardKey) -> bool:
        """Execute key release for a keyboard key."""
        return self._execute_with_retry(
            "keyboard key release",
            self._keyup,
            key,
        )

    def _keyup(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        raise NotImplementedError(f"{self.__class__.__name__}.keyup")

    @annotation("endpoint", {"method": "post", "path": "/hotkey"})
    @annotation("mcp_tool", {"tool_name": "hotkey"})
    def hotkey(self, keys: List[KeyboardKey]) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        return self._execute_with_retry(
            "keyboard hotkey",
            self._hotkey,
            keys,
        )

    def _hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        for key in keys:
            self.keydown(key)
        for key in reversed(keys):
            self.keyup(key)

    @annotation("endpoint", {"method": "post", "path": "/type"})
    @annotation("mcp_tool", {"tool_name": "type"})
    def type(self, text: str) -> bool:
        """Execute typing the given text."""
        return self._execute_with_retry("type", self._type, text)

    def _type(self, text: str):
        """Execute typing the given text."""
        for char in text:
            self.keypress(char)

    @annotation("endpoint", {"method": "post", "path": "/move"})
    @annotation("mcp_tool", {"tool_name": "move"})
    def move(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Execute moving the mouse to (x, y) over the move duration."""
        return self._execute_with_retry(
            "mouse move",
            self._move,
            x,
            y,
            duration,
        )

    def _move(self, x: int, y: int, duration: float = 0.5):
        """Execute moving the mouse to (x, y) over the move duration."""
        raise NotImplementedError(f"{self.__class__.__name__}.move")

    @annotation("endpoint", {"method": "post", "path": "/scroll"})
    @annotation("mcp_tool", {"tool_name": "scroll"})
    def scroll(self, amount: float) -> bool:
        """Execute mouse scroll by a given amount."""
        return self._execute_with_retry("mouse scroll", self._scroll, amount)

    def _scroll(self, amount: float):
        """Execute mouse scroll by a given amount."""
        raise NotImplementedError(f"{self.__class__.__name__}.scroll")

    @annotation("endpoint", {"method": "post", "path": "/mouse_down"})
    @annotation("mcp_tool", {"tool_name": "mouse_down"})
    def mouse_down(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button down action."""
        return self._execute_with_retry(
            "mouse button down",
            self._mouse_down,
            button,
        )

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button down action."""
        raise NotImplementedError(f"{self.__class__.__name__}.mouse_down")

    @annotation("endpoint", {"method": "post", "path": "/mouse_up"})
    @annotation("mcp_tool", {"tool_name": "mouse_up"})
    def mouse_up(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button up action."""
        return self._execute_with_retry(
            "mouse button up",
            self._mouse_up,
            button,
        )

    def _mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button up action."""
        raise NotImplementedError(f"{self.__class__.__name__}.mouse_up")

    @annotation("endpoint", {"method": "post", "path": "/click"})
    @annotation("mcp_tool", {"tool_name": "click"})
    def click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
    ) -> bool:
        """Execute a click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        return self._execute_with_retry(
            "click",
            self._click,
            x,
            y,
            move_duration,
            press_duration,
            button,
        )

    def _click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a click action at the given coordinates using press and release operations with a duration."""
        self.move(x=x, y=y, duration=move_duration)
        self.mouse_down(button=button)
        time.sleep(press_duration)
        self.mouse_up(button=button)

    @annotation("endpoint", {"method": "post", "path": "/double_click"})
    @annotation("mcp_tool", {"tool_name": "double_click"})
    def double_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
        double_click_interval_seconds: float = 0.1,
    ) -> bool:
        """Execute a double click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        return self._execute_with_retry(
            "double click",
            self._double_click,
            x,
            y,
            move_duration,
            press_duration,
            button,
            double_click_interval_seconds,
        )

    def _double_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
        double_click_interval_seconds: float = 0.1,
    ):
        """Execute a double click action at the given coordinates using press and release operations with a duration."""
        self.click(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
        )
        time.sleep(double_click_interval_seconds)
        self.click(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
        )

    @annotation("endpoint", {"method": "post", "path": "/drag"})
    @annotation("mcp_tool", {"tool_name": "drag"})
    def drag(
        self,
        # TODO: maybe remove the start_x/y to align with openai's computer tool
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ) -> bool:
        """Execute a drag action using the primitive mouse operations."""
        return self._execute_with_retry(
            "drag",
            self._drag,
            start_x,
            start_y,
            end_x,
            end_y,
            move_duration,
            button,
        )

    def _drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a drag action using the primitive mouse operations."""
        # Move to the starting position
        self.move(x=start_x, y=start_y, duration=move_duration)
        # Press the mouse button down
        self.mouse_down(button=button)
        # Move to the ending position while holding down the mouse button
        self.move(x=end_x, y=end_y, duration=move_duration)
        # Release the mouse button
        self.mouse_up(button=button)

    @annotation("endpoint", {"use_getter": True, "path": "/http_video_stream"})
    @property
    def http_video_stream_url(self) -> str:
        """Get the URL for the HTTP video stream of the computer instance.

        Returns:
            str: The URL for the HTTP video stream, or an empty string if HTTP video streaming is not supported.
        """
        return self._get_http_video_stream_url()

    def _get_http_video_stream_url(self) -> str:
        """Internal method to get the HTTP video stream URL.

        Returns:
            str: The URL for the HTTP video stream, or an empty string if HTTP video streaming is not supported.
        """
        self.logger.debug("HTTP video streaming not implemented for this computer type")
        return ""

    @annotation("endpoint", {"method": "post", "path": "/start_http_video_stream"})
    def start_http_video_stream(
        self,
        host: str = 'localhost',
        port: int = 8080,
        frame_rate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg"
    ) -> bool:
        """Start the HTTP video stream for the computer instance.

        Args:
            host: HTTP server host address
            port: HTTP server port
            frame_rate: Target frame rate for the video stream
            quality: JPEG/PNG compression quality (0-100)
            scale: Scale factor for the video stream (0.1-1.0)
            compression: Image compression format to use

        Returns:
            bool: True if the HTTP video stream was successfully started, False otherwise.
        """
        return self._start_http_video_stream(
            host=host,
            port=port, 
            frame_rate=frame_rate,
            quality=quality,
            scale=scale,
            compression=compression
        )

    def _start_http_video_stream(
        self,
        host: str = 'localhost',
        port: int = 8080,
        frame_rate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg"
    ) -> bool:
        """Internal method to start the HTTP video stream.

        Args:
            host: HTTP server host address
            port: HTTP server port
            frame_rate: Target frame rate for the video stream
            quality: JPEG/PNG compression quality (0-100)
            scale: Scale factor for the video stream (0.1-1.0)
            compression: Image compression format to use

        Returns:
            bool: True if the HTTP video stream was successfully started, False otherwise.
        """
        self.logger.debug("HTTP video streaming not implemented for this computer type")
        return False

    @annotation("endpoint", {"method": "post", "path": "/stop_http_video_stream"})
    def stop_http_video_stream(self) -> bool:
        """Stop the HTTP video stream for the computer instance.

        Returns:
            bool: True if the HTTP video stream was successfully stopped, False otherwise.
        """
        return self._stop_http_video_stream()

    def _stop_http_video_stream(self) -> bool:
        """Internal method to stop the HTTP video stream.

        Returns:
            bool: True if the HTTP video stream was successfully stopped, False otherwise.
        """
        self.logger.debug("HTTP video streaming not implemented for this computer type")
        return False

    @annotation("endpoint", {"use_getter": True, "path": "/vnc_video_stream"})
    @property
    def vnc_video_stream_url(self) -> str:
        """Get the URL for the VNC video stream of the computer instance.

        Returns:
            str: The URL for the VNC video stream, or an empty string if VNC video streaming is not supported.
        """
        return self._get_vnc_video_stream_url()

    def _get_vnc_video_stream_url(self) -> str:
        """Internal method to get the VNC video stream URL.
        Creates a VNC server that proxies the HTTP video stream.

        Returns:
            str: The URL for the VNC video stream, or an empty string if VNC streaming is not supported.
        """
        # Check if VNC server is running using getattr to avoid attribute errors
        if getattr(self, '_vnc_server', None):
            host = getattr(self._vnc_server, 'host', 'localhost')
            port = getattr(self._vnc_server, 'port', 5900)
            return f"vnc://{host}:{port}"
        return ""

    

    @annotation("endpoint", {"method": "post", "path": "/start_vnc_video_stream"})
    def start_vnc_video_stream(
        self,
        host: str = 'localhost',
        port: int = 5900,
        password: str = 'commandagi',
        shared: bool = True,
        framerate: int = 30,
        quality: int = 80,
        encoding: Literal["raw", "tight", "zrle"] = "tight",
        compression_level: int = 6,
        scale: float = 1.0,
        allow_clipboard: bool = True,
        view_only: bool = False,
        allow_resize: bool = True
    ) -> bool:
        """Start the VNC video stream for the computer instance.

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

        Returns:
            bool: True if the VNC video stream was successfully started, False otherwise.
        """
        return self._start_vnc_video_stream(
            host=host,
            port=port,
            password=password,
            shared=shared,
            framerate=framerate,
            quality=quality,
            encoding=encoding,
            compression_level=compression_level,
            scale=scale,
            allow_clipboard=allow_clipboard,
            view_only=view_only,
            allow_resize=allow_resize
        )

    def _start_vnc_video_stream(
        self,
        host: str = 'localhost',
        port: int = 5900,
        password: str = 'commandagi',
        shared: bool = True,
        framerate: int = 30,
        quality: int = 80,
        encoding: Literal["raw", "tight", "zrle"] = "tight",
        compression_level: int = 6,
        scale: float = 1.0,
        allow_clipboard: bool = True,
        view_only: bool = False,
        allow_resize: bool = True
    ) -> bool:
        """Internal method to start the VNC video stream.
        Sets up a VNC server that proxies the HTTP video stream and handles input events.

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

        Returns:
            bool: True if the VNC video stream was successfully started, False otherwise.
        """
        try:
            # Start HTTP stream first if not already running
            if not self._start_http_video_stream():
                self.logger.error("Failed to start HTTP stream for VNC proxy")
                return False

            # Import VNC server implementation
            from commandAGI._utils.vnc import HTTPStreamVNCServer
            
            # Create VNC server instance
            self._vnc_server = HTTPStreamVNCServer(
                http_stream_url=self._get_http_video_stream_url(),
                host=host,
                port=port,
                password=password,
                shared=shared,
                framerate=framerate,
                quality=quality,
                encoding=encoding,
                compression_level=compression_level,
                scale=scale,
                allow_clipboard=allow_clipboard,
                view_only=view_only,
                allow_resize=allow_resize,
                # Input event handlers that map to computer methods
                on_mouse_move=lambda x, y: self.move(x, y),
                on_mouse_click=lambda x, y, button: self.click(x, y, button=button),
                on_mouse_down=lambda button: self.mouse_down(button=button),
                on_mouse_up=lambda button: self.mouse_up(button=button),
                on_key_press=lambda key: self.keypress(key),
                on_key_down=lambda key: self.keydown(key),
                on_key_up=lambda key: self.keyup(key)
            )

            # Start the VNC server
            self._vnc_server.start()
            self.logger.info(f"VNC server started on {host}:{port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start VNC server: {e}")
            self._vnc_server = None
            return False

    @annotation("endpoint", {"method": "post", "path": "/stop_vnc_video_stream"})
    def stop_vnc_video_stream(self) -> bool:
        """Stop the VNC video stream for the computer instance.

        Returns:
            bool: True if the VNC video stream was successfully stopped, False otherwise.
        """
        return self._stop_vnc_video_stream()

    def _stop_vnc_video_stream(self) -> bool:
        """Internal method to stop the VNC video stream.
        Shuts down the VNC server and stops proxying the HTTP stream.

        Returns:
            bool: True if the VNC video stream was successfully stopped, False otherwise.
        """
        # Check if VNC server exists using getattr to avoid attribute errors
        if getattr(self, '_vnc_server', None):
            try:
                self._vnc_server.stop()
                self._vnc_server = None
                self.logger.info("VNC server stopped")
                return True
            except Exception as e:
                self.logger.error(f"Error stopping VNC server: {e}")
        return False


    def copy_to_computer(
        self, source_path: Union[str, Path], destination_path: Union[str, Path]
    ) -> bool:
        """Copy a file or directory to the computer.

        Args:
            source_path: The path to the source file or directory.
            destination_path: The path to the destination file or directory on the computer.

        Returns:
            bool: True if the copy operation was successful, False otherwise.
        """
        return self._execute_with_retry(
            "copy to computer",
            self._copy_to_computer,
            Path(source_path) if isinstance(source_path, str) else source_path,
            (
                Path(destination_path)
                if isinstance(destination_path, str)
                else destination_path
            ),
        )

    def _copy_to_computer(self, source_path: Path, destination_path: Path) -> None:
        """Copy a file or directory to the computer.

        Args:
            source_path: Path to source file/directory on local machine
            destination_path: Path where to copy on the computer
        """
        raise NotImplementedError(f"{self.__class__.__name__}._copy_to_computer")

    def copy_from_computer(
        self, source_path: Union[str, Path], destination_path: Union[str, Path]
    ) -> bool:
        """Copy a file or directory from the computer to the local machine.

        This method copies a file or directory from the computer instance to the local machine.
        It handles retries and ensures the computer is started if needed.

        Args:
            source_path: Path to the source file or directory on the computer
            destination_path: Path where the file or directory should be copied on the local machine

        Returns:
            bool: True if the copy operation was successful, False otherwise
        """
        return self._execute_with_retry(
            "copy from computer",
            self._copy_from_computer,
            Path(source_path) if isinstance(source_path, str) else source_path,
            (
                Path(destination_path)
                if isinstance(destination_path, str)
                else destination_path
            ),
        )

    def _copy_from_computer(self, source_path: Path, destination_path: Path) -> None:
        """Copy a file or directory from the computer to the local machine.

        Args:
            source_path: Path to source file/directory on the computer
            destination_path: Path where to copy on local machine
        """
        raise NotImplementedError(f"{self.__class__.__name__}._copy_from_computer")

    def open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ) -> BaseComputerFile:
        """Open a file on the computer.

        This method returns a file-like object that can be used to read from or write to
        a file on the computer. The returned object mimics the built-in file object API.

        Args:
            path: Path to the file on the computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            A file-like object for the specified file
        """
        return self._execute_with_retry(
            "open", self._open, path, mode, encoding, errors, buffering
        )

    @abstractmethod
    def _open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ) -> BaseComputerFile:
        """Implementation-specific method to open a file on the computer.

        Args:
            path: Path to the file on the computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)

        Returns:
            A file-like object for the specified file
        """
        raise NotImplementedError(f"{self.__class__.__name__}._open")

    @annotation("endpoint", {"method": "post", "path": "/locate_text_on_screen"})
    @annotation("mcp_tool", {"tool_name": "locate_text_on_screen"})
    def locate_text_on_screen(
        self,
        text: str,
        ocr_engine: Literal["screenparse", "pytesseract"] = "pytesseract",
        additional_ocr_args: dict = {},
    ) -> tuple[int, int] | None:
        """Find text on screen and return coordinates.

        Args:
            text: The text to locate on screen
            ocr_engine: OCR engine to use ("pytesseract" or "screenparse")
            additional_ocr_args: Additional arguments to pass to the OCR engine

        Returns:
            tuple[int, int] | None: (x,y) coordinates of the text if found, None if not found
        """
        # Get screenshot in base64 format
        screenshot = self.get_screenshot(format="base64")

        # Select OCR engine and parse screenshot
        match ocr_engine.lower():
            case "screenparse":
                from commandAGI.processors.screen_parser.screenparse_ai_screen_parser import (
                    parse_screenshot,
                )

                # Note: This would require api_key to be passed or configured
                parsed = parse_screenshot(screenshot, **additional_ocr_args)

            case "pytesseract" | _:  # Default to pytesseract
                from commandAGI.processors.screen_parser.pytesseract_screen_parser import (
                    parse_screenshot,
                )

                parsed = parse_screenshot(screenshot, **additional_ocr_args)

        # Search through parsed elements for matching text
        for element in parsed.elements:
            if text.lower() in element.text.lower():
                # Return center point of bounding box
                left, top, right, bottom = element.bounding_box
                center_x = (left + right) // 2
                center_y = (top + bottom) // 2
                return (center_x, center_y)

        # Text not found
        return None

    @annotation("endpoint", {"method": "post", "path": "/locate_object_on_screen"})
    @annotation("mcp_tool", {"tool_name": "locate_object_on_screen"})
    def locate_object_on_screen(
        self,
        template: Union[str, Path, Image.Image],
        threshold: float = 0.8,
        method: str = "cv2.TM_CCOEFF_NORMED",
        region: Optional[tuple[int, int, int, int]] = None,
    ) -> tuple[int, int] | None:
        """Find an image/icon on screen and return coordinates.

        Args:
            template: Path to template image or PIL Image object to locate
            threshold: Matching threshold (0-1), higher is more strict
            method: Template matching method to use:
                - cv2.TM_CCOEFF_NORMED (default): Normalized correlation coefficient
                - cv2.TM_SQDIFF_NORMED: Normalized squared difference
                - cv2.TM_CCORR_NORMED: Normalized cross correlation
            region: Optional tuple (x, y, width, height) to limit search area

        Returns:
            tuple[int, int] | None: (x,y) coordinates of center of best match if found above threshold, None if not found
        """
        import cv2
        import numpy as np
        from PIL import Image

        # Get screenshot as PIL Image
        screenshot = self.get_screenshot(format="PIL")

        # Convert template path/PIL Image to cv2 format
        if isinstance(template, (str, Path)):
            template = Image.open(template)
        if isinstance(template, Image.Image):
            template = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)

        # Convert screenshot to cv2 format
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Crop screenshot to region if specified
        if region:
            x, y, w, h = region
            screenshot = screenshot[y : y + h, x : x + w]

        # Get template dimensions
        template_h, template_w = template.shape[:2]

        # Perform template matching
        method = getattr(cv2, method.split(".")[-1])
        result = cv2.matchTemplate(screenshot, template, method)

        # Get best match location
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Different methods have different optimal values
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            match_val = 1 - min_val  # Convert to similarity score
            match_loc = min_loc
        else:
            match_val = max_val
            match_loc = max_loc

        # Check if match exceeds threshold
        if match_val >= threshold:
            # Calculate center point of match
            center_x = match_loc[0] + template_w // 2
            center_y = match_loc[1] + template_h // 2

            # Adjust coordinates if region was specified
            if region:
                center_x += region[0]
                center_y += region[1]

            return (center_x, center_y)

        # No match found above threshold
        return None

    @annotation("endpoint", {"method": "post", "path": "/mouse_action"})
    @annotation("mcp_tool", {"tool_name": "mouse_action"})
    def mouse_action(
        self,
        action: Literal["move", "click", "double_click"],
        position: tuple[int, int],
        button: MouseButton = MouseButton.LEFT,
    ) -> bool:
        """Execute a mouse action at the specified position with the given button.

        Args:
            action: The mouse action to perform ("move", "click", or "double_click")
            position: (x,y) coordinates for the mouse action
            button: Mouse button to use ("left", "right", or "middle")

        Returns:
            bool: True if action was successful, False otherwise
        """
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        match action:
            case "move":
                return self.execute_move_mouse(position)
            case "click":
                return self.click(position, button)
            case "double_click":
                return self.double_click(position, button)
            case _:
                self.logger.error(f"Invalid mouse action: {action}")
                return False

    @property
    def tools(self) -> list[BaseTool]:
        mcp_tool_names = gather_annotated_attr_keys(self, "mcp_tool")
        tools = []
        for mcp_tool_name in mcp_tool_names:
            tool_method = getattr(self, mcp_tool_name)
            tool = BaseTool.from_function(
                name=tool_method.__name__,
                description=tool_method.__doc__,
                func=tool_method,
                return_direct=True,
            )
            tools.append(tool)
        return tools

    def get_mcp_server(self):
        """Create and return a FastMCP server with tools and resources based on annotations."""
        from fastmcp import FastMCP
        from commandAGI._utils.annotations import gather_annotated_attrs

        # Create FastMCP server with the computer's name
        mcp = FastMCP(self.name)

        # Gather all tool and resource annotated attributes
        tools = gather_annotated_attrs(self, "mcp_tool")
        resources = gather_annotated_attrs(self, "mcp_resource")

        # Register tools (POST endpoints)
        for attr_name, annotation_data in tools.items():
            method = getattr(self, attr_name)

            @mcp.tool()
            def tool_endpoint(*args, method=method, **kwargs):
                try:
                    return method(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error executing tool {attr_name}: {e}")
                    raise

        # Register resources (GET endpoints)
        for attr_name, annotation_data in resources.items():
            method = getattr(self, attr_name)
            resource_name = annotation_data.get("mcp_resource", {}).get(
                "resource_name", attr_name
            )

            @mcp.resource(name=resource_name)
            def resource_endpoint(*args, method=method, **kwargs):
                try:
                    return method(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error getting resource {attr_name}: {e}")
                    raise

        return mcp

    def get_http_server(self):
        """Create and return a FastAPI server with endpoints based on annotations."""
        from fastapi import FastAPI, HTTPException
        from typing import Any, Dict
        from enum import Enum
        from commandAGI._utils.annotations import gather_annotated_attrs

        class HTTPMethod(str, Enum):
            GET = "GET"
            POST = "POST"
            PUT = "PUT"
            DELETE = "DELETE"
            PATCH = "PATCH"
            HEAD = "HEAD"
            OPTIONS = "OPTIONS"

        app = FastAPI()

        # Gather all endpoint-annotated attributes
        endpoints = gather_annotated_attrs(self, "endpoint")

        def create_endpoint(path: str, http_method: HTTPMethod, handler: callable):
            """Helper function to create FastAPI endpoints with consistent error handling"""

            async def endpoint_wrapper(**kwargs) -> Any:
                try:
                    return await handler(**kwargs)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))

            app.add_api_route(
                path=path,
                endpoint=endpoint_wrapper,
                methods=[http_method],
                name=f"{http_method.lower()}_{path.replace('/', '_')}",
            )

        for attr_name, annotation_data in endpoints.items():
            endpoint_config = annotation_data.get("endpoint", {})
            path = endpoint_config.get("path", f"/{attr_name}")
            method = HTTPMethod(endpoint_config.get("method", "POST").upper())
            use_getter = endpoint_config.get("use_getter", False)
            use_setter = endpoint_config.get("use_setter", False)

            # Handle property getters/setters
            if use_getter or use_setter:
                if use_getter:

                    async def getter_handler(attr_name=attr_name):
                        return getattr(self, attr_name)

                    create_endpoint(path, HTTPMethod.GET, getter_handler)

                if use_setter:

                    async def setter_handler(value: Any, attr_name=attr_name):
                        setattr(self, attr_name, value)
                        return {"status": "success"}

                    create_endpoint(path, HTTPMethod.PUT, setter_handler)
                continue

            # Handle regular method endpoints
            async def method_handler(method=getattr(self, attr_name), **kwargs):
                return method(**kwargs)

            create_endpoint(path, method, method_handler)

        return app

    def _execute_with_retry(
        self, operation_name: str, operation: callable, *args, **kwargs
    ) -> bool:
        """Execute an operation with retry mechanism.

        Args:
            operation_name: Name of the operation for logging
            operation: Callable to execute
            *args: Positional arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation

        Returns:
            bool: True if operation succeeded, False if all retries failed
        """
        if not self.ensure_running_state("running"):
            return False

        if self.error_handling == "raise":
            operation(*args, **kwargs)
        elif self.error_handling == "pass":
            try:
                operation(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error executing {operation_name}: {e}")
                return False
        else:
            raise ValueError(f"Invalid error handling: {self.error_handling}")

        return False
