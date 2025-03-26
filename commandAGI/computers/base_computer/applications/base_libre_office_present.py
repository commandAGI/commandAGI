from pathlib import Path
from typing import Optional, Union

from commandAGI.computers.base_computer.base_application import BaseApplication


class BaseLibreOfficePresent(BaseApplication):
    """Base class for LibreOffice Impress presentation operations.

    This class defines the interface for working with LibreOffice Impress. Implementations
    should provide methods to create and modify presentations through the application's API.
    """

    model_config = {"arbitrary_types_allowed": True}

    def launch_application(self) -> bool:
        """Launch LibreOffice Impress application."""
        raise NotImplementedError("Subclasses must implement launch_application")

    def create_presentation(self) -> bool:
        """Create a new blank presentation."""
        raise NotImplementedError("Subclasses must implement create_presentation")

    def open_presentation(self, file_path: Union[str, Path]) -> bool:
        """Open a presentation file."""
        raise NotImplementedError("Subclasses must implement open_presentation")

    def save_presentation(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current presentation."""
        raise NotImplementedError("Subclasses must implement save_presentation")

    # Add same methods as BasePowerPointEditor for consistency
    # (add_slide, delete_slide, etc.)
