
import logging
from pathlib import Path
from typing import Dict, Literal, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field

from commandAGI._utils.annotations import annotation
from commandAGI.computers.misc_types import ProcessInfo
from commandAGI._utils.platform import DEFAULT_SHELL_EXECUTIBLE

if TYPE_CHECKING:
    from commandAGI.computers.base_computer.base_computer import BaseComputer


class BaseComputerSubprocess(BaseModel):
    """Base class for computer processes."""

    pid: int = Field(description="Process ID")
    executable: str = DEFAULT_SHELL_EXECUTIBLE
    _logger: Optional[logging.Logger] = None
    last_pinfo: Optional[ProcessInfo] = Field(None, description="Last process info")
    _computer: BaseComputer = Field(description="Computer instance")

    @property
    def cwd(self) -> Path:
        """Get the current working directory of the shell.

        Returns:
            Path: The current working directory
        """
        raise NotImplementedError("Subclasses must implement cwd getter")
    
    @property
    def env(self) -> Dict[str, str]:
        """Get all environment variables from the shell.

        Returns:
            Dict[str, str]: Dictionary mapping environment variable names to their values
        """
        raise NotImplementedError("Subclasses must implement env getter")

    def read_output(self, timeout: Optional[float] = None, *, encoding: Optional[str] = None) -> str:
        """Read any available output from the shell.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            str: The output from the shell
        """
        raise NotImplementedError("Subclasses must implement read_output")

    def send_input(self, text: str, *, encoding: Optional[str] = None) -> bool:
        """Send input to the shell.

        Args:
            text: The text to send to the shell

        Returns:
            bool: True if the input was sent successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send_input")

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

class BaseComputerWindowedSubprocess(BaseComputerSubprocess):
    """Base class for computer processes that run in a window."""

    window_title: str = Field(description="Window title")
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

