from pathlib import Path
from typing import Dict, Optional


from commandAGI.computers.base_computer.base_subprocess import (
    BaseSubprocess,
)


class RemoteSubprocess(BaseSubprocess):
    """Remote implementation of computer subprocess."""

    @property
    def cwd(self) -> Path:
        """Get the current working directory of the subprocess.

        Returns:
            Path: The current working directory
        """
        if not self._computer.client:
            raise RuntimeError("Client not initialized")

        response = self._computer.client.get_process_info(self.pid)
        if response and "cwd" in response:
            return Path(response["cwd"])
        raise RuntimeError("Failed to get process cwd from daemon")

    @property
    def env(self) -> Dict[str, str]:
        """Get environment variables from the subprocess.

        Returns:
            Dict[str, str]: Dictionary of environment variables
        """
        if not self._computer.client:
            raise RuntimeError("Client not initialized")

        response = self._computer.client.get_process_info(self.pid)
        if response and "env" in response:
            return response["env"]
        raise RuntimeError("Failed to get process env from daemon")

    def read_output(
        self, timeout: Optional[float] = None, *, encoding: Optional[str] = None
    ) -> str:
        """Read output from the subprocess.

        Args:
            timeout: Optional timeout in seconds
            encoding: Optional encoding to use

        Returns:
            str: Output from the subprocess
        """
        if not self._computer.client:
            raise RuntimeError("Client not initialized")

        response = self._computer.client.read_process_output(
            self.pid, timeout=timeout, encoding=encoding
        )
        if response:
            return response
        raise RuntimeError("Failed to read process output from daemon")

    def send_input(self, text: str, *, encoding: Optional[str] = None) -> bool:
        """Send input to the subprocess.

        Args:
            text: Text to send
            encoding: Optional encoding to use

        Returns:
            bool: True if input was sent successfully
        """
        if not self._computer.client:
            raise RuntimeError("Client not initialized")

        return self._computer.client.send_process_input(
            self.pid, text, encoding=encoding
        )

    def start(self) -> bool:
        """Start the subprocess.

        Returns:
            bool: True if started successfully
        """
        if not self._computer.client:
            raise RuntimeError("Client not initialized")

        return self._computer.client.start_process(self.pid)

    def stop(self) -> bool:
        """Stop the subprocess.

        Returns:
            bool: True if stopped successfully
        """
        if not self._computer.client:
            raise RuntimeError("Client not initialized")

        return self._computer.client.stop_process(self.pid)
