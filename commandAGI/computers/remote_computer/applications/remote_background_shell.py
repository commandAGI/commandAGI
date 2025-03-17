import logging
import platform
import shlex
from pathlib import Path
from typing import Dict, Optional, Union, Any

from commandAGI.computers.base_computer.applications.base_background_shell import BaseBackgroundShell
from commandAGI.computers.remote_computer.remote_subprocess import RemoteApplication, RemoteSubprocess
from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE


class RemoteBackgroundShell(BaseBackgroundShell, RemoteSubprocess):
    """Implementation of BaseBackgroundShell for remote system shells.

    This class provides methods to run shell commands in the background on a remote system.
    """

    def __init__(
        self,
        executable: str = DEFAULT_SHELL_EXECUTIBLE,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a RemoteBackgroundShell instance.

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

        Args:
            command: The command to execute

        Returns:
            Dict containing initial process information
        """
        # For remote shells, we need to modify the command to run in background
        if platform.system() == "Windows":
            # Windows implementation using START
            bg_command = f"START /B {command}"
        else:
            # Unix implementation using nohup
            bg_command = f"nohup {command} > /dev/null 2>&1 & echo $!"

        result = self.execute(bg_command)

        if result["returncode"] == 0:
            # On Unix, the output will be the PID of the background process
            pid = int(result["stdout"].strip()) if not platform.system() == "Windows" else None
            return {
                "pid": pid,
                "command": command,
                "status": "running",
            }
        else:
            return {
                "pid": None,
                "command": command,
                "status": "failed",
                "error": result["stderr"],
            }

    def is_command_running(self, pid: int) -> bool:
        """Check if a background command is still running.

        Args:
            pid: Process ID of the background command

        Returns:
            bool: True if the command is still running, False otherwise
        """
        if platform.system() == "Windows":
            # Windows implementation using TASKLIST
            result = self.execute(f"TASKLIST /FI \"PID eq {pid}\" /NH")
            return str(pid) in result["stdout"]
        else:
            # Unix implementation using ps
            result = self.execute(f"ps -p {pid} -o pid=")
            return bool(result["stdout"].strip())

    def get_command_output(self, pid: int) -> Dict[str, Any]:
        """Get the current output of a background command.

        Args:
            pid: Process ID of the background command

        Returns:
            Dict containing stdout, stderr, and status information
        """
        if not self.is_command_running(pid):
            return {
                "stdout": "",
                "stderr": "Process not found or completed",
                "status": "not_found",
                "returncode": None,
            }

        # Note: For remote background processes, we can't easily get the output
        # unless the command was started with output redirection
        return {
            "stdout": "",
            "stderr": "Output not available for remote background processes",
            "status": "running",
            "returncode": None,
        }

    def stop_command(self, pid: int) -> bool:
        """Stop a background command.

        Args:
            pid: Process ID of the background command

        Returns:
            bool: True if the command was stopped successfully
        """
        if not self.is_command_running(pid):
            return False

        if platform.system() == "Windows":
            # Windows implementation using TASKKILL
            result = self.execute(f"TASKKILL /F /PID {pid}")
        else:
            # Unix implementation using kill
            result = self.execute(f"kill -TERM {pid} || kill -KILL {pid}")

        return result["returncode"] == 0 