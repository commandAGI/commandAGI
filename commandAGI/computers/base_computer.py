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
    TypedDict,
    Union,
)

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from commandAGI._internal.config import APPDIR, DEV_MODE
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
    _state: Literal["stopped", "started", "paused"] = (
        "stopped"  # Updated to include paused state
    )
    logger: Optional[logging.Logger] = None
    _file_handler: Optional[logging.FileHandler] = None
    num_retries: int = 3

    def __init__(self, name=None, **kwargs):
        name = (
            name
            or f"{self.__class__.__name__}-{next_for_cls(self.__class__.__name__):03d}"
        )
        super().__init__(name=name, **kwargs)

        # Initialize logger
        self.logger = logging.getLogger(f"commandAGI.computers.{self.name}")
        self.logger.setLevel(logging.INFO)

    def start(self):
        """Start the computer."""
        if self._state == "started":
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
        self._state = "started"
        self.logger.info(f"{self.__class__.__name__} computer started successfully")

    def _start(self):
        """Start the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.start")

    def stop(self):
        """Stop the computer."""
        if self._state == "stopped":
            self.logger.warning("Computer is already stopped")
            return

        if self._state == "paused":
            self.logger.info("Computer is paused, stopping anyway")

        self.logger.info(f"Stopping {self.__class__.__name__} computer")
        self._stop()
        self._state = "stopped"

        # Close and remove the file handler
        if self._file_handler:
            self.logger.info(f"{self.__class__.__name__} computer stopped successfully")
            self._file_handler.close()
            self.logger.removeHandler(self._file_handler)
            self._file_handler = None

    def _stop(self):
        """Stop the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.stop")

    def pause(self) -> bool:
        """Pause the computer.

        This method pauses the computer, which means it's still running but in a suspended state.

        Returns:
            bool: True if the computer was successfully paused, False otherwise.
        """
        if self._state != "started":
            self.logger.warning(f"Cannot pause computer in {self._state} state")
            return False

        self.logger.info(
            f"Attempting to pause {
                self.__class__.__name__} computer"
        )
        for attempt in range(self.num_retries):
            try:
                self._pause()
                self._state = "paused"
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

    def resume(self, timeout_hours: Optional[float] = None) -> bool:
        """Resume a paused computer.

        Args:
            timeout_hours: Optional timeout in hours after which the computer will be paused again.

        Returns:
            bool: True if the computer was successfully resumed, False otherwise.
        """
        if self._state != "paused":
            self.logger.warning(
                f"Cannot resume computer in {
                    self._state} state"
            )
            return False

        self.logger.info(
            f"Attempting to resume {self.__class__.__name__} computer"
            + (f" with {timeout_hours} hour timeout" if timeout_hours else "")
        )
        for attempt in range(self.num_retries):
            try:
                self._resume(timeout_hours)
                self._state = "started"
                self.logger.info(
                    f"{self.__class__.__name__} computer resumed successfully"
                )
                return True
            except Exception as e:
                self.logger.error(
                    f"Error resuming computer (attempt {attempt + 1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _resume(self, timeout_hours: Optional[float] = None):
        """Implementation of resume functionality.

        Args:
            timeout_hours: Optional timeout in hours after which the computer will automatically pause again.

        This method should be overridden by subclasses to implement computer-specific resume functionality.
        The default implementation does nothing.
        """
        self.logger.debug("Resume not implemented for this computer type")
        pass

    def ensure_running_state(
        self, target_state: Literal["running", "paused", "stopped"]
    ):
        """Ensure the computer is in the specified state.

        TODO: implement a timeout for the state transition or else raise an exception

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

    def reset_state(self):
        """Reset the computer state. If you just need ot reset the computer state without a full off-on, use this method. NOTE: in most cases, we just do a full off-on"""
        self.logger.info(f"Resetting {self.__class__.__name__} computer state")
        self.stop()
        self.start()

    _temp_dir: str = None

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

    @property
    def artifact_dir(self) -> Path:
        artifact_dir_path = APPDIR / self.name

        if not self._has_created_artifact_dir and not artifact_dir_path.exists():
            artifact_dir_path.mkdir(parents=True, exist_ok=True)
            self._has_created_artifact_dir = True
        return artifact_dir_path

    @property
    def logfile_path(self) -> Path:
        return self.artifact_dir / "logfile.log"

    @property
    def _new_screenshot_name(self) -> Path:
        return self.artifact_dir / f"screenshot-{datetime.now():%Y-%m-%d_%H-%M-%S-%f}"

    def wait(self, timeout: float = 5.0) -> bool:
        """Waits a specified amount of time"""
        time.sleep(timeout)
        return True

    @property
    def screenshot(self) -> Union[str, Image.Image, Path]:
        """Get a screenshot of the current display."""
        return self.get_screenshot()

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

    @property
    def mouse_position(self) -> tuple[int, int]:
        return self.get_mouse_position()

    @mouse_position.setter
    def mouse_position(self, value: tuple[int, int]):
        x, y = value
        self.execute_mouse_move(x=x, y=y, move_duration=0.0)

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
                self.execute_mouse_button_down(button=MouseButton[button_name.upper()])
            elif button_state is False:
                self.execute_mouse_button_up(button=MouseButton[button_name.upper()])

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
                self.execute_keyboard_key_down(key=KeyboardKey[key_name.upper()])
            elif key_state is False:
                self.execute_keyboard_key_release(key=KeyboardKey[key_name.upper()])

    def get_keyboard_key_states(self) -> dict[KeyboardKey, bool]:
        """Get the current state of keyboard keys."""
        return self._execute_with_retry(
            "get_keyboard_key_states", self._get_keyboard_key_states
        )

    def _get_keyboard_key_states(self) -> dict[KeyboardKey, bool]:
        """Get the current state of keyboard keys."""
        raise NotImplementedError(f"{self.__class__.__name__}.get_keyboard_key_states")

    @property
    def keyboard_key_states_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="get_keyboard_key_states",
            description="Get the current keyboard key states",
            func=self.get_keyboard_key_states,
        )

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
            self.execute_keyboard_key_release(key=key)

        # Press new keys that should be pressed
        for key in target - current:
            self.execute_keyboard_key_down(key=key)

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
            self.execute_keyboard_key_down(key=key)

        # Release new keys that should be released
        for key in target - current:
            self.execute_keyboard_key_release(key=key)

    @property
    def processes(self) -> List[ProcessInfo]:
        """Get information about running processes."""
        return self.get_processes()

    def get_processes(self) -> List[ProcessInfo]:
        """Get information about running processes."""
        return self._execute_with_retry("get_processes", self._get_processes)

    def _get_processes(self) -> List[ProcessInfo]:
        """Get information about running processes."""
        raise NotImplementedError(f"{self.__class__.__name__}._get_processes")

    @property
    def get_processes_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="get_processes",
            description="Get information about running processes",
            func=self.get_processes,
        )

    @property
    def windows(self) -> List[WindowInfo]:
        """Get information about open windows."""
        return self.get_windows()

    def get_windows(self) -> List[WindowInfo]:
        """Get information about open windows."""
        return self._execute_with_retry("get_windows", self._get_windows)

    def _get_windows(self) -> List[WindowInfo]:
        """Get information about open windows."""
        raise NotImplementedError(f"{self.__class__.__name__}._get_windows")

    @property
    def get_windows_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="get_windows",
            description="Get information about open windows",
            func=self.get_windows,
        )

    @property
    def displays(self) -> List[DisplayInfo]:
        """Get information about connected displays."""
        return self.get_displays()

    def get_displays(self) -> List[DisplayInfo]:
        """Get information about connected displays."""
        return self._execute_with_retry("get_displays", self._get_displays)

    def _get_displays(self) -> List[DisplayInfo]:
        """Get information about connected displays."""
        raise NotImplementedError(f"{self.__class__.__name__}._get_displays")

    @property
    def get_displays_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="get_displays",
            description="Get information about connected displays",
            func=self.get_displays,
        )

    @property
    def layout_tree(self) -> UIElement:
        """Get the current UI layout tree."""
        return self.get_layout_tree()

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
    def layout_tree_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="get_layout_tree",
            description="Get the current layout tree",
            func=self.get_layout_tree,
        )

    @property
    def sysinfo(self) -> SystemInfo:
        """Get information about the system."""
        return self.get_sysinfo()

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

    def start_jupyter_server(
        self, port: int = 8888, notebook_dir: Optional[str] = None
    ):
        """Start a Jupyter notebook server.

        Args:
            port: Port number to run the server on
            notebook_dir: Directory to serve notebooks from. If None, uses current directory.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_jupyter_server")

    def stop_jupyter_server(self):
        """Stop the running Jupyter notebook server if one exists."""
        raise NotImplementedError(f"{self.__class__.__name__}.stop_jupyter_server")

    def create_jupyter_notebook(self) -> BaseJupyterNotebook:
        """Create and return a new BaseJupyterNotebook instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseJupyterNotebook for the specific computer type.

        Returns:
            BaseJupyterNotebook: A notebook client instance for creating and manipulating notebooks.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.create_jupyter_notebook")

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

    @property
    def run_process_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="run_process",
            description="Run a process with the specified parameters",
            func=self.run_process,
        )

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
            self._execute_shell_command,
            ShellCommandAction(command=command, timeout=timeout, executible=executible),
        )

    def _execute_shell_command(
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

    @property
    def shell_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="shell",
            description="Execute a system command in the global shell environment",
            func=self.shell,
        )

    def execute_keyboard_key_press(
        self, key: KeyboardKey, duration: float = 0.1
    ) -> bool:
        """Execute pressing a keyboard key with a specified duration."""
        return self._execute_with_retry(
            "keyboard key press",
            self._execute_keyboard_key_press,
            key,
            duration,
        )

    def _execute_keyboard_key_press(self, key: KeyboardKey, duration: float = 0.1):
        """Execute pressing a keyboard key with a specified duration."""
        self.execute_keyboard_key_down(key)
        time.sleep(duration)
        self.execute_keyboard_key_release(key)

    @property
    def keyboard_key_press_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="keyboard_key_press",
            description="Execute pressing a keyboard key with a specified duration",
            func=self.execute_keyboard_key_press,
        )

    def execute_keyboard_key_down(self, key: KeyboardKey) -> bool:
        """Execute key down for a keyboard key."""
        return self._execute_with_retry(
            "keyboard key down",
            self._execute_keyboard_key_down,
            key,
        )

    def _execute_keyboard_key_down(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_keyboard_key_down"
        )

    @property
    def keyboard_key_down_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="keyboard_key_down",
            description="Execute key down for a keyboard key",
            func=self.execute_keyboard_key_down,
        )

    def execute_keyboard_key_release(self, key: KeyboardKey) -> bool:
        """Execute key release for a keyboard key."""
        return self._execute_with_retry(
            "keyboard key release",
            self._execute_keyboard_key_release,
            key,
        )

    def _execute_keyboard_key_release(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_keyboard_key_release"
        )

    @property
    def keyboard_key_release_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="keyboard_key_release",
            description="Execute key release for a keyboard key",
            func=self.execute_keyboard_key_release,
        )

    def execute_keyboard_hotkey(self, keys: List[KeyboardKey]) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        return self._execute_with_retry(
            "keyboard hotkey",
            self._execute_keyboard_hotkey,
            keys,
        )

    def _execute_keyboard_hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        for key in keys:
            self.execute_keyboard_key_down(key)
        for key in reversed(keys):
            self.execute_keyboard_key_release(key)

    @property
    def keyboard_hotkey_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="keyboard_hotkey",
            description="Execute a keyboard hotkey: press all keys in order and then release them in reverse order",
            func=self.execute_keyboard_hotkey,
        )

    def execute_type(self, text: str) -> bool:
        """Execute typing the given text."""
        return self._execute_with_retry("type", self._execute_type, text)

    def _execute_type(self, text: str):
        """Execute typing the given text."""
        for char in text:
            self.execute_keyboard_key_press(char)

    @property
    def type_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="type",
            description="Execute typing the given text",
            func=self.execute_type,
        )

    def execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5) -> bool:
        """Execute moving the mouse to (x, y) over the move duration."""
        return self._execute_with_retry(
            "mouse move",
            self._execute_mouse_move,
            x,
            y,
            move_duration,
        )

    def _execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5):
        """Execute moving the mouse to (x, y) over the move duration."""
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_move")

    @property
    def mouse_move_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="mouse_move",
            description="Execute moving the mouse to (x, y) over the move duration",
            func=self.execute_mouse_move,
        )

    def execute_mouse_scroll(self, amount: float) -> bool:
        """Execute mouse scroll by a given amount."""
        return self._execute_with_retry(
            "mouse scroll", self._execute_mouse_scroll, amount
        )

    def _execute_mouse_scroll(self, amount: float):
        """Execute mouse scroll by a given amount."""
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_scroll")

    @property
    def mouse_scroll_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="mouse_scroll",
            description="Execute mouse scroll by a given amount",
            func=self.execute_mouse_scroll,
        )

    def execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button down action."""
        return self._execute_with_retry(
            "mouse button down",
            self._execute_mouse_button_down,
            button,
        )

    def _execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button down action."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_mouse_button_down"
        )

    @property
    def mouse_button_down_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="mouse_button_down",
            description="Execute mouse button down action",
            func=self.execute_mouse_button_down,
        )

    def execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button up action."""
        return self._execute_with_retry(
            "mouse button up",
            self._execute_mouse_button_up,
            button,
        )

    def _execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button up action."""
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_button_up")

    @property
    def mouse_button_up_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="mouse_button_up",
            description="Execute mouse button up action",
            func=self.execute_mouse_button_up,
        )

    def execute_click(
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
            self._execute_click,
            x,
            y,
            move_duration,
            press_duration,
            button,
        )

    def _execute_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a click action at the given coordinates using press and release operations with a duration."""
        self.execute_mouse_move(x=x, y=y, move_duration=move_duration)
        self.execute_mouse_button_down(button=button)
        time.sleep(press_duration)
        self.execute_mouse_button_up(button=button)

    @property
    def click_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="click",
            description="Execute a click action at the given coordinates using press and release operations with a duration",
            func=self.execute_click,
        )

    def execute_double_click(
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
            self._execute_double_click,
            x,
            y,
            move_duration,
            press_duration,
            button,
            double_click_interval_seconds,
        )

    def _execute_double_click(
        self,
        x: int,
        y: int,
        move_duration: float = 0.5,
        press_duration: float = 0.1,
        button: MouseButton = MouseButton.LEFT,
        double_click_interval_seconds: float = 0.1,
    ):
        """Execute a double click action at the given coordinates using press and release operations with a duration."""
        self.execute_click(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
        )
        time.sleep(double_click_interval_seconds)
        self.execute_click(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
        )

    @property
    def double_click_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="double_click",
            description="Execute a double click action at the given coordinates using press and release operations with a duration",
            func=self.execute_double_click,
        )

    def execute_drag(
        self,
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
            self._execute_drag,
            start_x,
            start_y,
            end_x,
            end_y,
            move_duration,
            button,
        )

    def _execute_drag(
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
        self.execute_mouse_move(x=start_x, y=start_y, move_duration=move_duration)
        # Press the mouse button down
        self.execute_mouse_button_down(button=button)
        # Move to the ending position while holding down the mouse button
        self.execute_mouse_move(x=end_x, y=end_y, move_duration=move_duration)
        # Release the mouse button
        self.execute_mouse_button_up(button=button)

    @property
    def drag_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="drag",
            description="Execute a drag action using the primitive mouse operations",
            func=self.execute_drag,
        )

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the computer instance.

        Returns:
            str: The URL for the video stream, or an empty string if video streaming is not supported.
        """
        self.logger.debug("Video streaming not implemented for this computer type")
        return ""

    def start_video_stream(self) -> bool:
        """Start the video stream for the computer instance.

        Returns:
            bool: True if the video stream was successfully started, False otherwise.
        """
        self.logger.debug("Video streaming not implemented for this computer type")
        return False

    def stop_video_stream(self) -> bool:
        """Stop the video stream for the computer instance.

        Returns:
            bool: True if the video stream was successfully stopped, False otherwise.
        """
        self.logger.debug("Video streaming not implemented for this computer type")
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

    @property
    def copy_to_computer_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="copy_to_computer",
            description="Copy a file or directory to the computer",
            func=self.copy_to_computer,
        )

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

    @property
    def copy_from_computer_tool(self) -> BaseTool:
        return BaseTool.from_function(
            name="copy_from_computer",
            description="Copy a file or directory from the computer to the local machine",
            func=self.copy_from_computer,
        )

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

    def execute_mouse_action(
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
                return self.execute_click(position, button)
            case "double_click":
                return self.execute_double_click(position, button)
            case _:
                self.logger.error(f"Invalid mouse action: {action}")
                return False

    @property
    def mouse_action_tool(self) -> BaseTool:
        """Tool for executing mouse actions."""

        class MouseActionInput(BaseModel):
            action: Literal["move", "click", "double_click"] = Field(
                description="Mouse action to perform: 'move', 'click', or 'double_click'"
            )
            position: tuple[int, int] = Field(
                description="(x,y) coordinates for mouse action"
            )
            button: MouseButton = Field(
                default=MouseButton.LEFT,
                description="Mouse button to use: 'left', 'right', or 'middle'",
            )

        class MouseActionOutput(BaseModel):
            success: bool = Field(description="Whether the mouse action was successful")

        return BaseTool.from_function(
            name="mouse_action",
            description="Execute mouse actions like move, click, and double-click",
            func=self.execute_mouse_action,
            args_schema=MouseActionInput,
            return_direct=True,
        )

    def execute_computer_action(self, action: ComputerActionUnion) -> bool:
        """Execute a computer action based on the action type.

        Args:
            action: A ComputerActionUnion object representing the action to perform

        Returns:
            bool: True if action was successful, False otherwise
        """
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        try:
            match action.action_type:
                case ComputerActionType.SHELL.value:
                    return self.shell(action.command, timeout=action.timeout)

                case ComputerActionType.KEYBOARD_KEYS_PRESS.value:
                    return self.execute_keyboard_keys_press(
                        action.keys, action.duration
                    )

                case ComputerActionType.KEYBOARD_KEYS_DOWN.value:
                    return self.execute_keyboard_keys_down(action.keys)

                case ComputerActionType.KEYBOARD_KEYS_RELEASE.value:
                    return self.execute_keyboard_keys_release(action.keys)

                case ComputerActionType.KEYBOARD_KEY_PRESS.value:
                    return self.execute_keyboard_key_press(action.key, action.duration)

                case ComputerActionType.KEYBOARD_KEY_DOWN.value:
                    return self.execute_keyboard_key_down(action.key)

                case ComputerActionType.KEYBOARD_KEY_RELEASE.value:
                    return self.execute_keyboard_key_release(action.key)

                case ComputerActionType.KEYBOARD_HOTKEY.value:
                    return self.execute_keyboard_hotkey(action.keys)

                case ComputerActionType.TYPE.value:
                    return self.execute_type(action.text)

                case ComputerActionType.MOUSE_MOVE.value:
                    return self.execute_mouse_move(
                        action.x, action.y, action.move_duration
                    )

                case ComputerActionType.MOUSE_SCROLL.value:
                    return self.execute_mouse_scroll(action.amount)

                case ComputerActionType.MOUSE_BUTTON_DOWN.value:
                    return self.execute_mouse_button_down(action.button)

                case ComputerActionType.MOUSE_BUTTON_UP.value:
                    return self.execute_mouse_button_up(action.button)

                case ComputerActionType.CLICK.value:
                    return self.execute_click(
                        action.x,
                        action.y,
                        action.move_duration,
                        action.press_duration,
                        action.button,
                    )

                case ComputerActionType.DOUBLE_CLICK.value:
                    return self.execute_double_click(
                        action.x,
                        action.y,
                        action.move_duration,
                        action.press_duration,
                        action.button,
                        action.double_click_interval_seconds,
                    )

                case ComputerActionType.DRAG.value:
                    return self.execute_drag(
                        action.start_x,
                        action.start_y,
                        action.end_x,
                        action.end_y,
                        action.move_duration,
                        action.button,
                    )

                case ComputerActionType.RUN_PROCESS.value:
                    return self.run_process(
                        action.command,
                        action.args,
                        action.cwd,
                        action.env,
                        action.timeout,
                    )

                case ComputerActionType.FILE_COPY_TO_COMPUTER.value:
                    return self.copy_to_computer(
                        action.source_path, action.destination_path
                    )

                case ComputerActionType.FILE_COPY_FROM_COMPUTER.value:
                    return self.copy_from_computer(
                        action.source_path, action.destination_path
                    )

                case _:
                    self.logger.error(f"Unsupported action type: {action.action_type}")
                    return False

        except Exception as e:
            self.logger.error(f"Error executing computer action: {e}")
            return False

    @property
    def computer_action_tool(self) -> BaseTool:
        """Tool for executing any computer action."""
        return BaseTool.from_function(
            name="computer_action",
            description="Execute any computer action (keyboard, mouse, process, etc)",
            func=self.execute_computer_action,
            args_schema=ComputerActionUnion,
            return_direct=True,
        )

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

        for attempt in range(self.num_retries):
            try:
                operation(*args, **kwargs)
                return True
            except Exception as e:
                if DEV_MODE and attempt == self.num_retries - 1:
                    raise e
                self.logger.error(
                    f"Error executing {operation_name} (attempt {attempt + 1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False
