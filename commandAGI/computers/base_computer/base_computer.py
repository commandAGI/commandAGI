import logging
import os
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from itertools import tee
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypeAlias, TypedDict, Union

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from commandAGI._internal.config import APPDIR, DEV_MODE
from commandAGI._utils.annotations import annotation, gather_annotated_attr_keys
from commandAGI._utils.counter import next_for_cls
from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE
from commandAGI.computers.base_computer.applications.base_background_shell import (
    BaseBackgroundShell,
)
from commandAGI.computers.base_computer.applications.base_blender import BaseBlender
from commandAGI.computers.base_computer.applications.base_chrome_browser import (
    BaseChromeBrowser,
)
from commandAGI.computers.base_computer.applications.base_cursor_ide import (
    BaseCursorIDE,
)
from commandAGI.computers.base_computer.applications.base_file_explorer import (
    BaseFileExplorer,
)
from commandAGI.computers.base_computer.applications.base_freecad import BaseFreeCAD
from commandAGI.computers.base_computer.applications.base_kdenlive import BaseKdenlive
from commandAGI.computers.base_computer.applications.base_kicad import BaseKicad
from commandAGI.computers.base_computer.applications.base_libre_office_calc import (
    BaseLibreOfficeCalc,
)
from commandAGI.computers.base_computer.applications.base_libre_office_present import (
    BaseLibreOfficePresent,
)
from commandAGI.computers.base_computer.applications.base_libre_office_writer import (
    BaseLibraOfficeWriter,
)
from commandAGI.computers.base_computer.applications.base_microsoft_excel import (
    BaseMicrosoftExcel,
)
from commandAGI.computers.base_computer.applications.base_microsoft_powerpoint import (
    BaseMicrosoftPowerPoint,
)
from commandAGI.computers.base_computer.applications.base_microsoft_word import (
    BaseMicrosoftWord,
)
from commandAGI.computers.base_computer.applications.base_paint_editor import (
    BasePaintEditor,
)
from commandAGI.computers.base_computer.applications.base_shell import BaseShell
from commandAGI.computers.base_computer.applications.base_text_editor import (
    BaseTextEditor,
)
from commandAGI.computers.base_computer.base_keyboard import KeyboardKey
from commandAGI.computers.base_computer.base_mouse import MouseButton
from commandAGI.computers.base_computer.base_subprocess import BaseSubprocess
from commandAGI.computers.misc_types import (
    ComputerRunningState,
    DisplayInfo,
    ProcessInfo,
    SystemInfo,
    UIElement,
    WindowInfo,
)


class BaseComputer(BaseModel):

    model_config = {"arbitrary_types_allowed": True}

    name: str
    _state: ComputerRunningState = "stopped"
    logger: Optional[logging.Logger] = None
    _log_file_handler: Optional[logging.FileHandler] = None
    num_retries: int = 3
    error_handling: Literal["raise", "pass"] = "raise"
    preferred_video_stream_mode: Literal["vnc", "http"] = "http"
    """Used  to indicate which video stream mode is more efficient (ie, to avoid using proxy streams)"""

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
        if not self._log_file_handler:
            self._log_file_handler = logging.FileHandler(self.logfile_path)
            self._log_file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            self._log_file_handler.setFormatter(formatter)
            self.logger.addHandler(self._log_file_handler)

        self.logger.info(f"Starting {self.__class__.__name__} computer")
        self._start()
        self._state = ComputerRunningState.RUNNING
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
        self._state = ComputerRunningState.STOPPED

        # Close and remove the file handler
        if self._log_file_handler:
            self.logger.info(f"{self.__class__.__name__} computer stopped successfully")
            self._log_file_handler.close()
            self.logger.removeHandler(self._log_file_handler)
            self._log_file_handler = None

    def _stop(self):
        """Stop the computer."""
        raise NotImplementedError(f"{self.__class__.__name__}.stop")

    @annotation("endpoint", {})
    def pause(self):
        """Pause the computer.

        This method pauses the computer, which means it's still running but in a suspended state.
        """
        if self._state != "running":
            self.logger.warning(f"Cannot pause computer in {self._state} state")
            return

        self.logger.info(
            f"Attempting to pause {
                self.__class__.__name__} computer"
        )
        for attempt in range(self.num_retries):
            try:
                self._pause()
                self._state = ComputerRunningState.PAUSED
                self.logger.info(
                    f"{self.__class__.__name__} computer paused successfully"
                )
                return
            except Exception as e:
                self.logger.error(
                    f"Error pausing computer (attempt {attempt + 1}/{self.num_retries}): {e}"
                )
                if attempt == self.num_retries - 1:
                    raise

    def _pause(self):
        """Implementation of pause functionality.

        This method should be overridden by subclasses to implement computer-specific pause functionality.
        The default implementation does nothing.
        """
        self.logger.debug("Pause not implemented for this computer type")
        pass

    @annotation("endpoint", {})
    def resume(self):
        """Resume a paused computer."""
        if self._state != "paused":
            self.logger.warning(
                f"Cannot resume computer in {
                    self._state} state"
            )
            return

        self.logger.info(f"Attempting to resume {self.__class__.__name__} computer")
        self._resume()
        self._state = ComputerRunningState.RUNNING
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
    def state(self) -> ComputerRunningState:
        return self._state

    @state.setter
    def state(self, value: ComputerRunningState):
        self.ensure_running_state(value)

    @annotation("endpoint", {})
    def ensure_running_state(self, target_state: ComputerRunningState):
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
    def wait(self, timeout: float = 5.0):
        """Waits a specified amount of time"""
        time.sleep(timeout)

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

    @annotation("endpoint", {"method": "post", "path": "/shell"})
    @annotation("mcp_tool", {"tool_name": "shell"})
    def shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executible: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
    ):
        """Execute a system command in the global shell environment.

        NOTE: its generally a better idea to use `start_shell` so you can run your shell in a separate processon the host machine
        (but also not that some computer shell implementations actually shove it all back into the system_shell and only pretend to be multiprocessed lol)

        The timeout parameter indicates how long (in seconds) to wait before giving up,
        with None meaning no timeout.
        """
        self._execute_with_retry(
            "shell command",
            self._shell,
            command=command,
            timeout=timeout,
            executible=executible,
            cwd=cwd,
            env=env,
        )

    @annotation("endpoint", {"method": "post", "path": "/run_process"})
    @annotation("mcp_tool", {"tool_name": "run_process"})
    def run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> BaseSubprocess:
        """Run a process with the specified parameters."""
        self._execute_with_retry(
            "run_process",
            self._run_process,
            command=command,
            args=args,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )

    def _run_process(
        self,
        command: str,
        args: List[str] = [],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> BaseSubprocess:
        """Run a process with the specified parameters.

        Args:
            command: The command to run
            args: List of command arguments
            cwd: Working directory for the process
            env: Environment variables for the process
            timeout: Optional timeout in seconds
        """
        raise NotImplementedError(f"{self.__class__.__name__}._run_process")

    @annotation("endpoint", {"method": "post", "path": "/start_shell"})
    def start_shell(
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
        return self._start_shell(executable=executable, cwd=cwd, env=env)

    def _start_shell(
        self,
        executable: str = None,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> BaseShell:
        raise NotImplementedError(f"{self.__class__.__name__}.start_shell")

    @annotation("endpoint", {"method": "post", "path": "/start_background_shell"})
    def start_background_shell(
        self,
        executable: str = None,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> BaseBackgroundShell:
        """Create and return a new background shell instance.

        This method creates a persistent background shell that can be used to execute
        commands that run in the background without blocking the main execution thread.

        Args:
            executable: Path to the shell executable to use
            cwd: Initial working directory for the shell
            env: Environment variables to set in the shell

        Returns:
            BaseBackgroundShell: A background shell instance for executing background commands
        """
        return self._start_background_shell(executable=executable, cwd=cwd, env=env)

    def _start_background_shell(
        self,
        executable: str = None,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> BaseBackgroundShell:
        raise NotImplementedError(f"{self.__class__.__name__}.start_background_shell")

    @annotation("endpoint", {"method": "post", "path": "/start_cursor_ide"})
    def start_cursor_ide(self) -> BaseCursorIDE:
        """Create and return a new BaseCursorIDE instance.

        implementation of BaseCursorIDE for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_cursor_ide")

    def _start_cursor_ide(self) -> BaseCursorIDE:
        """Create and return a new BaseCursorIDE instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseCursorIDE for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_cursor_ide")

    @annotation("endpoint", {"method": "post", "path": "/start_kicad"})
    def start_kicad(self) -> BaseKicad:
        """Create and return a new BaseKicad instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseKicad for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_kicad")

    def _start_kicad(self) -> BaseKicad:
        """Create and return a new BaseKicad instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseKicad for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_kicad")

    @annotation("endpoint", {"method": "post", "path": "/start_blender"})
    def start_blender(self) -> BaseBlender:
        """Create and return a new BaseBlender instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseBlender for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_blender")

    def _start_blender(self) -> BaseBlender:
        """Create and return a new BaseBlender instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseBlender for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_blender")

    @annotation("endpoint", {"method": "post", "path": "/start_file_explorer"})
    def start_file_explorer(self) -> BaseFileExplorer:
        """Create and return a new BaseFileExplorer instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseFileExplorer for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_file_explorer")

    def _start_file_explorer(self) -> BaseFileExplorer:
        """Create and return a new BaseFileExplorer instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseFileExplorer for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_file_explorer")

    @annotation("endpoint", {"method": "post", "path": "/start_chrome_browser"})
    def start_chrome_browser(self) -> BaseChromeBrowser:
        """Create and return a new BaseChromeBrowser instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseChromeBrowser for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_chrome_browser")

    def _start_chrome_browser(self) -> BaseChromeBrowser:
        """Create and return a new BaseChromeBrowser instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseChromeBrowser for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_chrome_browser")

    @annotation("endpoint", {"method": "post", "path": "/start_text_editor"})
    def start_text_editor(self) -> BaseTextEditor:
        """Create and return a new BaseTextEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseTextEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_text_editor")

    def _start_text_editor(self) -> BaseTextEditor:
        """Create and return a new BaseTextEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseTextEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_text_editor")

    @annotation("endpoint", {"method": "post", "path": "/start_libre_office_writer"})
    def start_libre_office_writer(self) -> BaseLibraOfficeWriter:
        """Create and return a new LibreOffice Writer instance."""
        return self._start_libre_office_writer()

    def _start_libre_office_writer(self) -> BaseLibraOfficeWriter:
        """Create and return a new LibreOffice Writer instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_libre_office_writer"
        )

    @annotation("endpoint", {"method": "post", "path": "/start_libre_office_calc"})
    def start_libre_office_calc(self) -> BaseLibreOfficeCalc:
        """Create and return a new LibreOffice Calc instance."""
        return self._start_libre_office_calc()

    def _start_libre_office_calc(self) -> BaseLibreOfficeCalc:
        """Create and return a new LibreOffice Calc instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_libre_office_calc")

    @annotation("endpoint", {"method": "post", "path": "/start_libre_office_present"})
    def start_libre_office_present(self) -> BaseLibreOfficePresent:
        """Create and return a new LibreOffice Impress instance."""
        return self._start_libre_office_present()

    def _start_libre_office_present(self) -> BaseLibreOfficePresent:
        """Create and return a new LibreOffice Impress instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_libre_office_present"
        )

    @annotation("endpoint", {"method": "post", "path": "/start_microsoft_word"})
    def start_microsoft_word(self) -> BaseMicrosoftWord:
        """Create and return a new Word instance."""
        return self._start_microsoft_word()

    def _start_microsoft_word(self) -> BaseMicrosoftWord:
        """Create and return a new Word instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_microsoft_word")

    @annotation("endpoint", {"method": "post", "path": "/start_microsoft_excel"})
    def start_microsoft_excel(self) -> BaseMicrosoftExcel:
        """Create and return a new Excel instance."""
        return self._start_microsoft_excel()

    def _start_microsoft_excel(self) -> BaseMicrosoftExcel:
        """Create and return a new Excel instance."""
        raise NotImplementedError(f"{self.__class__.__name__}._start_microsoft_excel")

    @annotation("endpoint", {"method": "post", "path": "/start_microsoft_powerpoint"})
    def start_microsoft_powerpoint(self) -> BaseMicrosoftPowerPoint:
        """Create and return a new PowerPoint instance."""
        return self._start_microsoft_powerpoint()

    def _start_microsoft_powerpoint(self) -> BaseMicrosoftPowerPoint:
        """Create and return a new PowerPoint instance."""
        raise NotImplementedError(
            f"{self.__class__.__name__}._start_microsoft_powerpoint"
        )

    @annotation("endpoint", {"method": "post", "path": "/start_paint_editor"})
    def start_paint_editor(self) -> BasePaintEditor:
        """Create and return a new BasePaintEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BasePaintEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_paint_editor")

    def _start_paint_editor(self) -> BasePaintEditor:
        """Create and return a new BasePaintEditor instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BasePaintEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_paint_editor")

    @annotation("endpoint", {"method": "post", "path": "/start_cad"})
    def start_freecad(self) -> BaseFreeCAD:
        """Create and return a new BaseFreeCAD instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseCAD for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_cad")

    def _start_freecad(self) -> BaseFreeCAD:
        """Create and return a new BaseFreeCAD instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseCAD for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_cad")

    @annotation("endpoint", {"method": "post", "path": "/start_video_editor"})
    def start_kdenlive(self) -> BaseKdenlive:
        """Create and return a new BaseKdenlive instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseKdenlive for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.start_kdenlive")

    def _start_kdenlive(self) -> BaseKdenlive:
        """Create and return a new BaseKdenlive instance.

        This method should be implemented by subclasses to return an appropriate
        implementation of BaseVideoEditor for the specific computer type.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._start_video_editor")

    @annotation("endpoint", {"method": "post", "path": "/keypress"})
    @annotation("mcp_tool", {"tool_name": "keypress"})
    def keypress(self, key: KeyboardKey, duration: float = 0.1):
        """Execute pressing a keyboard key with a specified duration."""
        self._execute_with_retry(
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
    def keydown(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        self._execute_with_retry(
            "keyboard key down",
            self._keydown,
            key,
        )

    def _keydown(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        raise NotImplementedError(f"{self.__class__.__name__}.keydown")

    @annotation("endpoint", {"method": "post", "path": "/keyup"})
    @annotation("mcp_tool", {"tool_name": "keyup"})
    def keyup(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        self._execute_with_retry(
            "keyboard key release",
            self._keyup,
            key,
        )

    def _keyup(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        raise NotImplementedError(f"{self.__class__.__name__}.keyup")

    @annotation("endpoint", {"method": "post", "path": "/hotkey"})
    @annotation("mcp_tool", {"tool_name": "hotkey"})
    def hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey: press all keys in order and then release them in reverse order."""
        self._execute_with_retry(
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
    def type(self, text: str):
        """Execute typing the given text."""
        self._execute_with_retry("type", self._type, text)

    def _type(self, text: str):
        """Execute typing the given text."""
        for char in text:
            self.keypress(char)

    @annotation("endpoint", {"method": "post", "path": "/move"})
    @annotation("mcp_tool", {"tool_name": "move"})
    def move(self, x: int, y: int, duration: float = 0.5):
        """Execute moving the mouse to (x, y) over the move duration."""
        self._execute_with_retry(
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
    def scroll(self, amount: float):
        """Execute mouse scroll by a given amount."""
        self._execute_with_retry("mouse scroll", self._scroll, amount)

    def _scroll(self, amount: float):
        """Execute mouse scroll by a given amount."""
        raise NotImplementedError(f"{self.__class__.__name__}.scroll")

    @annotation("endpoint", {"method": "post", "path": "/mouse_down"})
    @annotation("mcp_tool", {"tool_name": "mouse_down"})
    def mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button down action."""
        self._execute_with_retry(
            "mouse button down",
            self._mouse_down,
            button,
        )

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button down action."""
        raise NotImplementedError(f"{self.__class__.__name__}.mouse_down")

    @annotation("endpoint", {"method": "post", "path": "/mouse_up"})
    @annotation("mcp_tool", {"tool_name": "mouse_up"})
    def mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Execute mouse button up action."""
        self._execute_with_retry(
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
    ):
        """Execute a click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        self._execute_with_retry(
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
    ):
        """Execute a double click action at the given coordinates using press and release operations with a duration.
        It constructs MouseMoveAction, MouseButtonDownAction, and MouseButtonUpAction objects and calls the corresponding implementations.
        """
        self._execute_with_retry(
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
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a drag action using the primitive mouse operations."""
        self._execute_with_retry(
            "drag",
            self._drag,
            end_x,
            end_y,
            move_duration,
            button,
        )

    def _drag(
        self,
        end_x: int,
        end_y: int,
        move_duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ):
        """Execute a drag action using the primitive mouse operations."""
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
        host: str = "localhost",
        port: int = 8080,
        frame_rate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg",
    ):
        """Start the HTTP video stream for the computer instance.

        Args:
            host: HTTP server host address
            port: HTTP server port
            frame_rate: Target frame rate for the video stream
            quality: JPEG/PNG compression quality (0-100)
            scale: Scale factor for the video stream (0.1-1.0)
            compression: Image compression format to use
        """
        self._start_http_video_stream(
            host=host,
            port=port,
            frame_rate=frame_rate,
            quality=quality,
            scale=scale,
            compression=compression,
        )

    def _start_http_video_stream(
        self,
        host: str = "localhost",
        port: int = 8080,
        frame_rate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg",
    ):
        """Internal method to start the HTTP video stream.

        Args:
            host: HTTP server host address
            port: HTTP server port
            frame_rate: Target frame rate for the video stream
            quality: JPEG/PNG compression quality (0-100)
            scale: Scale factor for the video stream (0.1-1.0)
            compression: Image compression format to use
        """
        self.logger.debug("HTTP video streaming not implemented for this computer type")

    @annotation("endpoint", {"method": "post", "path": "/stop_http_video_stream"})
    def stop_http_video_stream(self):
        """Stop the HTTP video stream for the computer instance."""
        self._stop_http_video_stream()

    def _stop_http_video_stream(self):
        """Internal method to stop the HTTP video stream."""
        self.logger.debug("HTTP video streaming not implemented for this computer type")

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
        if getattr(self, "_vnc_server", None):
            host = getattr(self._vnc_server, "host", "localhost")
            port = getattr(self._vnc_server, "port", 5900)
            return f"vnc://{host}:{port}"
        return ""

    @annotation("endpoint", {"method": "post", "path": "/start_vnc_video_stream"})
    def start_vnc_video_stream(
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
        """
        self._start_vnc_video_stream(
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
        )

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
        """
        try:
            # Start HTTP stream first if not already running
            self._start_http_video_stream()

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
                on_key_up=lambda key: self.keyup(key),
            )

            # Start the VNC server
            self._vnc_server.start()
            self.logger.info(f"VNC server started on {host}:{port}")

        except Exception as e:
            self.logger.error(f"Failed to start VNC server: {e}")
            self._vnc_server = None
            raise

    @annotation("endpoint", {"method": "post", "path": "/stop_vnc_video_stream"})
    def stop_vnc_video_stream(self):
        """Stop the VNC video stream for the computer instance."""
        self._stop_vnc_video_stream()

    def _stop_vnc_video_stream(self):
        """Internal method to stop the VNC video stream.
        Shuts down the VNC server and stops proxying the HTTP stream.
        """
        # Check if VNC server exists using getattr to avoid attribute errors
        if getattr(self, "_vnc_server", None):
            try:
                self._vnc_server.stop()
                self._vnc_server = None
                self.logger.info("VNC server stopped")
            except Exception as e:
                self.logger.error(f"Error stopping VNC server: {e}")
                raise

    def copy_to_computer(
        self, source_path: Union[str, Path], destination_path: Union[str, Path]
    ):
        """Copy a file or directory to the computer.

        Args:
            source_path: The path to the source file or directory.
            destination_path: The path to the destination file or directory on the computer.
        """
        self._execute_with_retry(
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
    ):
        """Copy a file or directory from the computer to the local machine.

        This method copies a file or directory from the computer instance to the local machine.
        It handles retries and ensures the computer is started if needed.

        Args:
            source_path: Path to the source file or directory on the computer
            destination_path: Path where the file or directory should be copied on the local machine
        """
        self._execute_with_retry(
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
    ):
        """Execute a mouse action at the specified position with the given button.

        Args:
            action: The mouse action to perform ("move", "click", or "double_click")
            position: (x,y) coordinates for the mouse action
            button: Mouse button to use ("left", "right", or "middle")
        """
        if self._state == "stopped":
            self._start()
        elif self._state == "paused":
            self.resume()

        match action:
            case "move":
                self.execute_move_mouse(position)
            case "click":
                self.click(position, button)
            case "double_click":
                self.double_click(position, button)
            case _:
                self.logger.error(f"Invalid mouse action: {action}")
                raise ValueError(f"Invalid mouse action: {action}")

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
        from enum import Enum
        from typing import Any, Dict

        from fastapi import FastAPI, HTTPException

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
