from datetime import datetime
from pathlib import Path
import time
import logging
import os
from abc import abstractmethod
from typing import ClassVar, Literal, List, Optional, Dict, Any, Union
from commandLAB._utils.config import APPDIR, SCREENSHOTS_DIR
from commandLAB._utils.counter import next_for_cls

from commandLAB._utils.platform import DEFAULT_SHELL_EXECUTIBLE
from commandLAB.types import (
    ClickAction,
    ShellCommandAction,
    DoubleClickAction,
    DragAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysDownAction,
    KeyboardKeysPressAction,
    KeyboardKeysReleaseAction,
    KeyboardStateObservation,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
    TypeAction,
    LayoutTreeObservation,
    ProcessesObservation,
    WindowsObservation,
    DisplaysObservation,
    RunProcessAction,
    KeyboardKey,
    MouseButton,
)
from pydantic import BaseModel, Field


class BaseJupyterNotebook(BaseModel):
    """Base class for Jupyter notebook operations.
    
    This class defines the interface for working with Jupyter notebooks programmatically.
    Implementations should provide methods to create, read, modify, and execute notebooks.
    """
    
    notebook_path: Optional[Path] = None
    
    def create_notebook(self) -> Dict[str, Any]:
        """Create a new empty notebook and return the notebook object."""
        raise NotImplementedError("Subclasses must implement create_notebook")
    
    def read_notebook(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Read a notebook from a file and return the notebook object."""
        raise NotImplementedError("Subclasses must implement read_notebook")
    
    def save_notebook(self, notebook: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> Path:
        """Save the notebook to a file and return the path."""
        raise NotImplementedError("Subclasses must implement save_notebook")
    
    def add_markdown_cell(self, notebook: Dict[str, Any], source: str, position: Optional[int] = None) -> Dict[str, Any]:
        """Add a markdown cell to the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement add_markdown_cell")
    
    def add_code_cell(self, notebook: Dict[str, Any], source: str, position: Optional[int] = None) -> Dict[str, Any]:
        """Add a code cell to the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement add_code_cell")
    
    def update_cell(self, notebook: Dict[str, Any], index: int, source: str) -> Dict[str, Any]:
        """Update the source of a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement update_cell")
    
    def remove_cell(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Remove a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement remove_cell")
    
    def list_cells(self, notebook: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return a list of cells in the notebook."""
        raise NotImplementedError("Subclasses must implement list_cells")
    
    def execute_notebook(self, notebook: Dict[str, Any], timeout: int = 600) -> Dict[str, Any]:
        """Execute all cells in the notebook and return the executed notebook."""
        raise NotImplementedError("Subclasses must implement execute_notebook")
    
    def execute_cell(self, notebook: Dict[str, Any], index: int, timeout: int = 60) -> Dict[str, Any]:
        """Execute a specific cell in the notebook and return the executed notebook."""
        raise NotImplementedError("Subclasses must implement execute_cell")
    
    def get_cell_output(self, notebook: Dict[str, Any], index: int) -> List[Dict[str, Any]]:
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
    
    executable: str = DEFAULT_SHELL_EXECUTIBLE
    cwd: Optional[Path] = None
    env: Dict[str, str] = Field(default_factory=dict)
    pid: Optional[int] = None
    logger: Optional[logging.Logger] = None
    
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


class BaseComputer(BaseModel):

    name: str
    _state: Literal["stopped", "started", "paused"] = "stopped"  # Updated to include paused state
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
        self.logger = logging.getLogger(f"commandLAB.computers.{self.name}")
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

        self.logger.info(f"Attempting to pause {self.__class__.__name__} computer")
        for attempt in range(self.num_retries):
            try:
                self._pause()
                self._state = "paused"
                self.logger.info(f"{self.__class__.__name__} computer paused successfully")
                return True
            except Exception as e:
                self.logger.error(
                    f"Error pausing computer (attempt {attempt+1}/{self.num_retries}): {e}"
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
            self.logger.warning(f"Cannot resume computer in {self._state} state")
            return False

        self.logger.info(f"Attempting to resume {self.__class__.__name__} computer" + (f" with {timeout_hours} hour timeout" if timeout_hours else ""))
        for attempt in range(self.num_retries):
            try:
                self._resume(timeout_hours)
                self._state = "started"
                self.logger.info(f"{self.__class__.__name__} computer resumed successfully")
                return True
            except Exception as e:
                self.logger.error(
                    f"Error resuming computer (attempt {attempt+1}/{self.num_retries}): {e}"
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

    def reset_state(self):
        """Reset the computer state. If you just need ot reset the computer state without a full off-on, use this method. NOTE: in most cases, we just do a full off-on"""
        self.logger.info(f"Resetting {self.__class__.__name__} computer state")
        self.stop()
        self.start()

    _checked_and_created_artifact_dir = False

    @property
    def artifact_dir(self) -> Path:
        artifact_dir_path = APPDIR / self.name

        if (
            not self._checked_and_created_artifact_dir
            and not artifact_dir_path.exists()
        ):
            artifact_dir_path.mkdir(parents=True, exist_ok=True)
            self._checked_and_created_artifact_dir = True
        return artifact_dir_path

    @property
    def logfile_path(self) -> Path:
        return self.artifact_dir / "logfile.log"

    @property
    def _new_screenshot_name(self) -> Path:
        return self.artifact_dir / f"screenshot-{datetime.now():%Y-%m-%d_%H-%M-%S-%f}"

    def get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> ScreenshotObservation:
        """Return a ScreenshotObservation containing the screenshot encoded as a base64 string.

        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_screenshot(display_id=display_id, format=format)
        except Exception as e:
            self.logger.error(f"Error getting screenshot: {e}")
            return ScreenshotObservation()

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> ScreenshotObservation:
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
        return self.get_mouse_state().position

    @mouse_position.setter
    def mouse_position(self, value: tuple[int, int]):
        x, y = value
        self.execute_mouse_move(x=x, y=y, move_duration=0.0)

    @property
    def mouse_button_states(self) -> dict[str, bool | None]:
        return self.get_mouse_state().buttons

    @mouse_button_states.setter
    def mouse_button_states(self, value: dict[str, bool | None]):
        for button_name, button_state in value.items():
            if button_state is True:
                self.execute_mouse_button_down(button=MouseButton[button_name.upper()])
            elif button_state is False:
                self.execute_mouse_button_up(button=MouseButton[button_name.upper()])

    @property
    def keyboard_key_states(self) -> dict[KeyboardKey, bool]:
        """Get the current state of all keyboard keys."""
        return self.get_keyboard_state().keys

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
    def screenshot(self) -> ScreenshotObservation:
        """Get a screenshot of the current display."""
        return self.get_screenshot()

    @property
    def layout_tree(self) -> LayoutTreeObservation:
        """Get the current UI layout tree."""
        return self.get_layout_tree()

    @property
    def processes(self) -> ProcessesObservation:
        """Get information about running processes."""
        return self.get_processes()

    @property
    def windows(self) -> WindowsObservation:
        """Get information about open windows."""
        return self.get_windows()

    @property
    def displays(self) -> DisplaysObservation:
        """Get information about connected displays."""
        return self.get_displays()

    def get_mouse_state(self) -> MouseStateObservation:
        """Return a MouseStateObservation containing the current mouse button states and position."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_mouse_state()
        except Exception as e:
            self.logger.error(f"Error getting mouse state: {e}")
            return MouseStateObservation()

    def _get_mouse_state(self) -> MouseStateObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_mouse_state")

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return a KeyboardStateObservation with the current keyboard keys mapped to their states."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_keyboard_state()
        except Exception as e:
            self.logger.error(f"Error getting keyboard state: {e}")
            return KeyboardStateObservation()

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_keyboard_state")

    def get_layout_tree(self) -> LayoutTreeObservation:
        """Return a LayoutTreeObservation containing the accessibility tree of the current UI."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_layout_tree()
        except Exception as e:
            self.logger.error(f"Error getting layout tree: {e}")
            return LayoutTreeObservation()

    def _get_layout_tree(self) -> LayoutTreeObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_layout_tree")

    def get_processes(self) -> ProcessesObservation:
        """Return a ProcessesObservation containing information about running processes."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_processes()
        except Exception as e:
            self.logger.error(f"Error getting processes: {e}")
            return ProcessesObservation()

    def _get_processes(self) -> ProcessesObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_processes")

    def get_windows(self) -> WindowsObservation:
        """Return a WindowsObservation containing information about open windows."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_windows()
        except Exception as e:
            self.logger.error(f"Error getting windows: {e}")
            return WindowsObservation()

    def _get_windows(self) -> WindowsObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_windows")

    def get_displays(self) -> DisplaysObservation:
        """Return a DisplaysObservation containing information about connected displays."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()
        try:
            return self._get_displays()
        except Exception as e:
            self.logger.error(f"Error getting displays: {e}")
            return DisplaysObservation()

    def _get_displays(self) -> DisplaysObservation:
        raise NotImplementedError(f"{self.__class__.__name__}.get_displays")

    _jupyter_server_pid: int|None = None
    def start_jupyter_server(self, port: int = 8888, notebook_dir: Optional[str] = None):
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
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = RunProcessAction(
            command=command, args=args, cwd=cwd, env=env, timeout=timeout
        )

        for attempt in range(self.num_retries):
            try:
                self._run_process(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error running process (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _run_process(self, action: RunProcessAction) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__}._run_process")

    def _default_run_process(self, action: RunProcessAction) -> bool:
        """Default implementation of run_process using shell commands.
        
        This method is deliberately not wired up to the base _run_process to make
        subclasses think about what they really want. It defaults to using shell
        commands to execute the process.
        
        Args:
            action: RunProcessAction containing the process parameters
            
        Returns:
            bool: True if the process was executed successfully
        """
        self.logger.info(f"Running process via shell: {action.command} with args: {action.args}")
        
        # Change to the specified directory if provided
        if action.cwd:
            self.shell(f'cd {action.cwd}')
        
        # Build the command string
        cmd_parts = [action.command] + action.args
        cmd_shell_format = ' '.join(cmd_parts)
        
        # Add environment variables if specified
        if action.env:
            # For Unix-like shells
            env_vars = ' '.join([f'{k}={v}' for k, v in action.env.items()])
            cmd_shell_format = f'{env_vars} {cmd_shell_format}'
        
        # Execute the command with timeout if specified
        return self.shell(cmd_shell_format, timeout=action.timeout)

    def create_shell(self, executable: str = None, cwd: Optional[Union[str, Path]] = None, env: Optional[Dict[str, str]] = None) -> BaseShell:
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

    def shell(self, command: str, timeout: Optional[float] = None, executible: Optional[str] = None) -> bool:
        """Execute a system command in the global shell environment and return True if successful.

        NOTE: its generally a better idea to use `create_shell` so you can run your shell in a separate processon the host machine
        (but also not that some computer shell implementations actually shove it all back into the system_shell and only pretend to be multiprocessed lol)

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = ShellCommandAction(command=command, timeout=timeout,executible=executible)

        for attempt in range(self.num_retries):
            try:
                self._execute_shell_command(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing command (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_shell_command(self, action: ShellCommandAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_command")

    def execute_keyboard_keys_press(
        self, keys: List[KeyboardKey], duration: float = 0.1
    ) -> bool:
        """Execute pressing keyboard keys."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = KeyboardKeysPressAction(keys=keys, duration=duration)

        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_keys_press(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing keyboard keys press (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_keyboard_keys_press(self, action: KeyboardKeysPressAction):
        self.execute_keyboard_keys_down(action.keys)
        self.execute_keyboard_keys_release(action.keys)

    def execute_keyboard_keys_down(self, keys: List[KeyboardKey]) -> bool:
        """Execute key down for each keyboard key."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = KeyboardKeysDownAction(keys=keys)

        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_keys_down(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing keyboard keys down (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_keyboard_keys_down(self, action: KeyboardKeysDownAction):
        for key in action.keys:
            self.execute_keyboard_key_down(key)

    def execute_keyboard_keys_release(self, keys: List[KeyboardKey]) -> bool:
        """Execute key release for each keyboard key."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = KeyboardKeysReleaseAction(keys=keys)

        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_keys_release(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing keyboard keys release (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_keyboard_keys_release(self, action: KeyboardKeysReleaseAction):
        for key in action.keys:
            self.execute_keyboard_key_release(key)

    def execute_keyboard_key_press(
        self, key: KeyboardKey, duration: float = 0.1
    ) -> bool:
        """Execute pressing a keyboard key with a specified duration."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = KeyboardKeyPressAction(key=key, duration=duration)

        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_key_press(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing keyboard key press (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction):
        self.execute_keyboard_key_down(KeyboardKeyDownAction(key=action.key))
        time.sleep(action.duration)
        self.execute_keyboard_key_release(KeyboardKeyReleaseAction(key=action.key))

    def execute_keyboard_key_down(self, key: KeyboardKey) -> bool:
        """Execute key down for a keyboard key."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = KeyboardKeyDownAction(key=key)

        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_key_down(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing keyboard key down (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_keyboard_key_down"
        )

    def execute_keyboard_key_release(self, key: KeyboardKey) -> bool:
        """Execute key release for a keyboard key."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = KeyboardKeyReleaseAction(key=key)

        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_key_release(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing keyboard key release (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_keyboard_key_release"
        )

    def execute_keyboard_hotkey(self, keys: List[KeyboardKey]) -> bool:
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = KeyboardHotkeyAction(keys=keys)

        for attempt in range(self.num_retries):
            try:
                self._execute_keyboard_hotkey(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing keyboard hotkey (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction):
        for key in action.keys:
            self.execute_keyboard_key_down(key)
        for key in reversed(action.keys):
            self.execute_keyboard_key_release(key)

    def execute_type(self, text: str) -> bool:
        """Execute typing the given text."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = TypeAction(text=text)

        for attempt in range(self.num_retries):
            try:
                self._execute_type(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing type (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_type(self, action: TypeAction):
        for char in action.text:
            self.execute_keyboard_key_press(KeyboardKeyPressAction(key=char))

    def execute_mouse_move(self, x: int, y: int, move_duration: float = 0.5) -> bool:
        """Execute moving the mouse to (x, y) over the move duration."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = MouseMoveAction(x=x, y=y, move_duration=move_duration)

        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_move(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing mouse move (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_mouse_move(self, action: MouseMoveAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_move")

    def execute_mouse_scroll(self, amount: float) -> bool:
        """Execute mouse scroll by a given amount."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = MouseScrollAction(amount=amount)

        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_scroll(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing mouse scroll (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_mouse_scroll(self, action: MouseScrollAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_scroll")

    def execute_mouse_button_down(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button down action."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = MouseButtonDownAction(button=button)

        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_button_down(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing mouse button down (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_mouse_button_down(self, action: MouseButtonDownAction):
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute_mouse_button_down"
        )

    def execute_mouse_button_up(self, button: MouseButton = MouseButton.LEFT) -> bool:
        """Execute mouse button up action."""
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = MouseButtonUpAction(button=button)

        for attempt in range(self.num_retries):
            try:
                self._execute_mouse_button_up(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing mouse button up (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_mouse_button_up(self, action: MouseButtonUpAction):
        raise NotImplementedError(f"{self.__class__.__name__}.execute_mouse_button_up")

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
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = ClickAction(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
        )

        for attempt in range(self.num_retries):
            try:
                self._execute_click(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing click (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_click(self, action: ClickAction):
        move_action = MouseMoveAction(
            x=action.x, y=action.y, move_duration=action.move_duration
        )
        self.execute_mouse_move(move_action)
        down_action = MouseButtonDownAction(button=action.button)
        self.execute_mouse_button_down(down_action)
        time.sleep(action.press_duration)
        up_action = MouseButtonUpAction(button=action.button)
        self.execute_mouse_button_up(up_action)

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
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = DoubleClickAction(
            x=x,
            y=y,
            move_duration=move_duration,
            press_duration=press_duration,
            button=button,
            double_click_interval_seconds=double_click_interval_seconds,
        )

        for attempt in range(self.num_retries):
            try:
                self._execute_double_click(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing double click (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_double_click(self, action: DoubleClickAction):
        self.execute_click(
            ClickAction(
                x=action.x,
                y=action.y,
                move_duration=action.move_duration,
                press_duration=action.press_duration,
                button=action.button,
            )
        )
        time.sleep(action.double_click_interval_seconds)
        self.execute_click(
            ClickAction(
                x=action.x,
                y=action.y,
                move_duration=action.move_duration,
                press_duration=action.press_duration,
                button=action.button,
            )
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
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        action = DragAction(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            move_duration=move_duration,
            button=button,
        )

        for attempt in range(self.num_retries):
            try:
                self._execute_drag(action)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error executing drag (attempt {attempt+1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    return False

        return False

    def _execute_drag(self, action: DragAction):
        # Move to the starting position
        self.execute_mouse_move(
            x=action.start_x, y=action.start_y, move_duration=action.move_duration
        )
        # Press the mouse button down
        self.execute_mouse_button_down(button=action.button)
        # Move to the ending position while holding down the mouse button
        self.execute_mouse_move(
            x=action.end_x, y=action.end_y, move_duration=action.move_duration
        )
        # Release the mouse button
        self.execute_mouse_button_up(button=action.button)

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
