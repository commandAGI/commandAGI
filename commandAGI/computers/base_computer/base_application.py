from commandAGI.computers.base_computer.base_subprocess import BaseSubprocess


class BaseApplication(BaseSubprocess):
    """Base class for application operations.

    This class defines the interface for working with applications.
    Implementations should provide methods to control application windows,
    execute commands, and interact with application interfaces.
    """

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
