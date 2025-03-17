import os
import platform
from pathlib import Path
from typing import Dict, Optional

import psutil

from commandAGI.computers.base_computer import BaseComputer
from commandAGI.computers.base_computer.base_subprocess import (
    BaseApplication,
    BaseSubprocess,
)


class LocalSubprocess(BaseSubprocess):
    """Implementation of BaseComputerSubprocess for local system processes."""

    def __init__(self, pid: int, computer: BaseComputer):
        """Initialize the process handler.

        Args:
            pid: Process ID to monitor/control
            computer: Reference to the computer instance
        """
        super().__init__(pid=pid, _computer=computer)
        self._process = psutil.Process(pid)

    @property
    def cwd(self) -> Path:
        """Get the current working directory of the process.

        Returns:
            Path: The current working directory
        """
        try:
            return Path(self._process.cwd())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return Path.cwd()

    @property
    def env(self) -> Dict[str, str]:
        """Get environment variables from the process.

        Returns:
            Dict[str, str]: Dictionary of environment variables
        """
        try:
            return self._process.environ()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}

    def read_output(
        self, timeout: Optional[float] = None, *, encoding: Optional[str] = None
    ) -> str:
        """Read output from the process.
        Note: This is not implemented for generic processes as there's no standard way to read output.

        Returns:
            str: Empty string as generic process output cannot be read
        """
        return ""

    def send_input(self, text: str, *, encoding: Optional[str] = None) -> bool:
        """Send input to the process.
        Note: This is not implemented for generic processes as there's no standard way to send input.

        Returns:
            bool: False as generic process input is not supported
        """
        return False

    def start(self) -> bool:
        """Start monitoring the process.

        Returns:
            bool: True if process exists and can be monitored
        """
        try:
            return self._process.is_running()
        except psutil.NoSuchProcess:
            return False

    def stop(self) -> bool:
        """Stop/terminate the process.

        Returns:
            bool: True if process was successfully terminated
        """
        try:
            self._process.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
