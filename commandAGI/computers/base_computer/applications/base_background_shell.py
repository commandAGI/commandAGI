import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from commandAGI.computers.base_computer.applications.base_shell import BaseShell
from commandAGI.computers.base_computer.base_subprocess import BaseSubprocess


class BaseBackgroundShell(BaseSubprocess):
    """Base class for background shell operations.

    This class extends BaseShell to provide functionality for running shell commands
    in the background. Background shells are useful for long-running processes that
    shouldn't block the main execution thread.
    """

    def __init__(
        self,
        executable: str,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a BaseBackgroundShell instance.

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
            logger=logger or logging.getLogger("commandAGI.background_shell"),
        )

    def execute_background(self, command: str) -> Dict[str, Any]:
        """Execute a command in the background and return immediately.

        This method starts the command execution but doesn't wait for it to complete.
        The command continues running in the background.

        Args:
            command: The command to execute

        Returns:
            Dict containing initial process information
        """
        raise NotImplementedError("Subclasses must implement execute_background")

    def is_command_running(self, pid: int) -> bool:
        """Check if a background command is still running.

        Args:
            pid: Process ID of the background command

        Returns:
            bool: True if the command is still running, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_command_running")

    def get_command_output(self, pid: int) -> Dict[str, Any]:
        """Get the current output of a background command.

        Args:
            pid: Process ID of the background command

        Returns:
            Dict containing stdout, stderr, and status information
        """
        raise NotImplementedError("Subclasses must implement get_command_output")

    def stop_command(self, pid: int) -> bool:
        """Stop a background command.

        Args:
            pid: Process ID of the background command

        Returns:
            bool: True if the command was stopped successfully
        """
        raise NotImplementedError("Subclasses must implement stop_command")
