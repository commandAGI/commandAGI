import logging
import platform
import shlex
from pathlib import Path
from typing import Dict, Optional, Union, Any

from commandAGI.computers.base_computer.applications.base_shell import BaseShell
from commandAGI.computers.remote_computer.remote_subprocess import RemoteApplication


class RemoteShell(BaseShell, RemoteApplication):
    """Implementation of BaseShell for remote system shells.

    This class provides methods to interact with a persistent shell process
    on a remote system.
    """

    def __init__(
        self,
        executable: str = DEFAULT_SHELL_EXECUTIBLE,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a RemoteShell instance.

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

            # Send the command with a newline
            self.send_input(command + "\n")

            # Read the output
            output = self.read_output(timeout=timeout)

            # Remove the command from the output
            lines = output.splitlines()
            if lines and command in lines[0]:
                output = "\n".join(lines[1:])

            return {
                "stdout": output,
                "stderr": "",  # We can't separate stdout and stderr
                "returncode": 0,  # We can't easily get the return code
            }
        except Exception as e:
            self._logger.error(f"Error executing command: {e}")
            return {"stdout": "", "stderr": str(e), "returncode": 1}

    def change_directory(self, path: Union[str, Path]) -> bool:
        """Change the current working directory of the shell.

        Args:
            path: The path to change to

        Returns:
            bool: True if the directory was changed successfully
        """
        path_str = str(path)
        result = self.execute(f"cd {shlex.quote(path_str)}")

        if result["returncode"] == 0:
            self.cwd = Path(path_str).resolve()
            return True
        return False

    def set_envvar(self, name: str, value: str) -> bool:
        """Set an environment variable in the shell.

        Args:
            name: The name of the environment variable
            value: The value to set

        Returns:
            bool: True if the variable was set successfully
        """
        if platform.system() == "Windows":
            cmd = f"set {name}={value}"
        else:
            cmd = f"export {name}={shlex.quote(value)}"

        result = self.execute(cmd)

        if result["returncode"] == 0:
            self.env[name] = value
            return True
        return False

    def get_envvar(self, name: str) -> Optional[str]:
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
            if platform.system() == "Windows" and value == f"%{name}%":
                return None
            return value
        return None

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
        return self.cwd
