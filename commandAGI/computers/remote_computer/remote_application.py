from commandAGI.computers.base_computer.base_application import BaseApplication
from commandAGI.computers.base_computer.base_subprocess import BaseSubprocess
from commandAGI.computers.remote_computer.remote_subprocess import RemoteSubprocess


class RemoteApplication(BaseApplication, RemoteSubprocess):
    """Base class for application operations.

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
        if not self._computer.client:
            raise RuntimeError("Client not initialized")

        response = self._computer.client.get_window_screenshot(
            self.window_title, display_id=display_id, format=format
        )
        if response:
            return response
        raise RuntimeError("Failed to get window screenshot from daemon")
