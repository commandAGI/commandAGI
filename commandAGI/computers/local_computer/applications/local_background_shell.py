import logging
import os
import platform
import shlex
import signal
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE
from commandAGI.computers.base_computer.applications.base_background_shell import (
    BaseBackgroundShell,
)
from commandAGI.computers.local_computer.local_subprocess import (
    LocalApplication,
    LocalSubprocess,
)


class LocalBackgroundShell(BaseBackgroundShell, LocalSubprocess):
    """Implementation of BaseBackgroundShell for local system shells.

    This class provides methods to run shell commands in the background on the local system.
    """

    _background_processes: Dict[int, subprocess.Popen] = {}
    _output_buffers: Dict[int, Dict[str, str]] = {}
    _locks: Dict[int, threading.Lock] = {}

    def __init__(
        self,
        executable: str = DEFAULT_SHELL_EXECUTIBLE,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a LocalBackgroundShell instance.

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
        try:
            # Set up environment
            env = os.environ.copy()
            if self.env:
                env.update(self.env)

            # Start the process
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    ["cmd.exe", "/c", command],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,
                    env=env,
                    shell=False,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                process = subprocess.Popen(
                    [self.executable, "-c", command],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,
                    env=env,
                    preexec_fn=os.setsid,
                    text=True,
                )

            pid = process.pid
            self._background_processes[pid] = process
            self._output_buffers[pid] = {"stdout": "", "stderr": ""}
            self._locks[pid] = threading.Lock()

            self._logger.info(f"Started background command with PID: {pid}")
            return {
                "pid": pid,
                "command": command,
                "status": "running",
            }

        except Exception as e:
            self._logger.error(f"Error starting background command: {e}")
            return {
                "pid": None,
                "command": command,
                "status": "failed",
                "error": str(e),
            }

    def is_command_running(self, pid: int) -> bool:
        """Check if a background command is still running.

        Args:
            pid: Process ID of the background command

        Returns:
            bool: True if the command is still running, False otherwise
        """
        process = self._background_processes.get(pid)
        if not process:
            return False

        return process.poll() is None

    def get_command_output(self, pid: int) -> Dict[str, Any]:
        """Get the current output of a background command.

        Args:
            pid: Process ID of the background command

        Returns:
            Dict containing stdout, stderr, and status information
        """
        process = self._background_processes.get(pid)
        if not process:
            return {
                "stdout": "",
                "stderr": "Process not found",
                "status": "not_found",
                "returncode": None,
            }

        with self._locks[pid]:
            # Read any new output
            stdout, stderr = "", ""
            try:
                if process.stdout and process.stdout.readable():
                    stdout = process.stdout.read1().decode("utf-8", errors="replace")
                if process.stderr and process.stderr.readable():
                    stderr = process.stderr.read1().decode("utf-8", errors="replace")
            except Exception as e:
                self._logger.error(f"Error reading output for PID {pid}: {e}")

            # Update buffers
            self._output_buffers[pid]["stdout"] += stdout
            self._output_buffers[pid]["stderr"] += stderr

            # Get process status
            returncode = process.poll()
            status = "running" if returncode is None else "completed"

            return {
                "stdout": self._output_buffers[pid]["stdout"],
                "stderr": self._output_buffers[pid]["stderr"],
                "status": status,
                "returncode": returncode,
            }

    def stop_command(self, pid: int) -> bool:
        """Stop a background command.

        Args:
            pid: Process ID of the background command

        Returns:
            bool: True if the command was stopped successfully
        """
        process = self._background_processes.get(pid)
        if not process:
            return False

        try:
            if platform.system() == "Windows":
                # Windows implementation
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            else:
                # Unix implementation
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)

            # Clean up
            self._cleanup_process(pid)
            return True

        except Exception as e:
            self._logger.error(f"Error stopping command with PID {pid}: {e}")
            return False

    def _cleanup_process(self, pid: int):
        """Clean up resources for a background process.

        Args:
            pid: Process ID of the background command
        """
        if pid in self._background_processes:
            del self._background_processes[pid]
        if pid in self._output_buffers:
            del self._output_buffers[pid]
        if pid in self._locks:
            del self._locks[pid]
