from commandAGI.computers.base_computer.base_application import BaseApplication
from commandAGI.computers.local_computer.local_subprocess import LocalApplication


class LocalApplication(BaseApplication, LocalApplication):
    """Local class for application operations.

    This class defines the interface for working with applications.
    Implementations should provide methods to control application windows,
    execute commands, and interact with application interfaces.
    """

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> Union[str, Image.Image, Path]:
        """Get screenshot of the subprocess window.

        Args:
            display_id: Display ID to capture
            format: Format to return screenshot in  

        Returns:
            Screenshot in requested format
        """
        return super()._get_screenshot(display_id=display_id, format=format)
