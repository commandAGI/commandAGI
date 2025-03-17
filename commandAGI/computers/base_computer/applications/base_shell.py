from pathlib import Path
from typing import Dict, Optional, Union

from commandAGI.computers.base_computer.base_subprocess import BaseSubprocess


class BaseShell(BaseSubprocess):
    """Base class for shell operations.

    This class defines the interface for working with a persistent shell/terminal session.
    Implementations should provide methods to execute commands and manage the shell environment.
    """

    model_config = {"arbitrary_types_allowed": True}

    def execute(self, command: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute a command in the shell and return the result.

        Args:
            command: The command to execute
            timeout: Optional timeout in seconds

        Returns:
            Dict containing stdout, stderr, and return code
        """
        raise NotImplementedError("Subclasses must implement execute")

    @property
    def cwd(self) -> Path:
        """Get the current working directory of the shell.

        Returns:
            Path: The current working directory
        """
        raise NotImplementedError("Subclasses must implement cwd getter")

    @cwd.setter
    def cwd(self, path: Union[str, Path]) -> None:
        """Set the current working directory of the shell.

        Args:
            path: The path to set as the current working directory
        """
        raise NotImplementedError("Subclasses must implement cwd setter")

    @property
    def shell_env(self) -> Dict[str, str]:
        """Get all environment variables from the shell.

        Returns:
            Dict[str, str]: Dictionary mapping environment variable names to their values
        """
        raise NotImplementedError("Subclasses must implement env getter")

    def get_shell_var(self, name: str) -> Optional[str]:
        """Get the value of an environment variable from the shell.

        Args:
            name: The name of the environment variable

        Returns:
            Optional[str]: The value of the environment variable, or None if it doesn't exist
        """
        raise NotImplementedError("Subclasses must implement get_shell_var")

    def set_shell_var(self, name: str, value: str) -> bool:
        """Set an environment variable in the shell.

        Args:
            name: The name of the environment variable
            value: The value to set

        Returns:
            bool: True if the variable was set successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement set_shell_var")

    def get_envtee(self, name: str) -> Optional[str]:
        """Get the value of an environment variable from the shell.

        Args:
            name: The name of the environment variable

        Returns:
            Optional[str]: The value of the environment variable, or None if it doesn't exist
        """
        raise NotImplementedError("Subclasses must implement get_envvar")

    def set_envvar(self, name: str, value: str) -> bool:
        """Set an environment variable in the shell.

        Args:
            name: The name of the environment variable
            value: The value to set

        Returns:
            bool: True if the variable was set successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement set_envvar")

    def is_running(self) -> bool:
        """Check if the shell process is running.

        Returns:
            bool: True if the shell is running, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_running")
