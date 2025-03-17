from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from commandAGI.computers.base_computer.base_application import BaseApplication


class BaseMicrosoftPowerPoint(BaseApplication):
    """Base class for PowerPoint presentation operations.

    This class defines the interface for working with Microsoft PowerPoint. Implementations
    should provide methods to create and modify presentations through PowerPoint's API.
    """

    model_config = {"arbitrary_types_allowed": True}

    def launch_application(self) -> bool:
        """Launch PowerPoint application."""
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

    def add_slide(self, layout: Optional[str] = None) -> bool:
        """Add a new slide to the presentation.

        Args:
            layout: Optional layout type for the new slide

        Returns:
            bool: True if slide was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_slide")

    def delete_slide(self, index: int) -> bool:
        """Delete a slide from the presentation.

        Args:
            index: Index of the slide to delete

        Returns:
            bool: True if slide was deleted successfully
        """
        raise NotImplementedError("Subclasses must implement delete_slide")

    def get_slide_count(self) -> int:
        """Get the number of slides in the presentation.

        Returns:
            int: Number of slides
        """
        raise NotImplementedError("Subclasses must implement get_slide_count")

    def select_slide(self, index: int) -> bool:
        """Select/activate a slide.

        Args:
            index: Index of the slide to select

        Returns:
            bool: True if slide was selected successfully
        """
        raise NotImplementedError("Subclasses must implement select_slide")

    def add_text_box(
        self, text: str, position: Tuple[float, float], size: Tuple[float, float]
    ) -> bool:
        """Add a text box to the current slide.

        Args:
            text: Text content
            position: (x, y) position coordinates
            size: (width, height) dimensions

        Returns:
            bool: True if text box was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_text_box")

    def add_shape(
        self,
        shape_type: str,
        position: Tuple[float, float],
        size: Tuple[float, float],
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a shape to the current slide.

        Args:
            shape_type: Type of shape to add
            position: (x, y) position coordinates
            size: (width, height) dimensions
            properties: Optional shape properties

        Returns:
            bool: True if shape was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_shape")

    def add_image(
        self,
        image_path: Union[str, Path],
        position: Tuple[float, float],
        size: Optional[Tuple[float, float]] = None,
    ) -> bool:
        """Add an image to the current slide.

        Args:
            image_path: Path to the image file
            position: (x, y) position coordinates
            size: Optional (width, height) dimensions

        Returns:
            bool: True if image was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_image")

    def add_chart(
        self,
        chart_type: str,
        data: List[List[Any]],
        position: Tuple[float, float],
        size: Tuple[float, float],
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a chart to the current slide.

        Args:
            chart_type: Type of chart to add
            data: 2D array of chart data
            position: (x, y) position coordinates
            size: (width, height) dimensions
            properties: Optional chart properties

        Returns:
            bool: True if chart was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_chart")

    def apply_template(self, template_path: Union[str, Path]) -> bool:
        """Apply a template to the presentation.

        Args:
            template_path: Path to the template file

        Returns:
            bool: True if template was applied successfully
        """
        raise NotImplementedError("Subclasses must implement apply_template")

    def export_presentation(
        self,
        output_path: Union[str, Path],
        format: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Export presentation to different format.

        Args:
            output_path: Path to save the exported file
            format: Target format (pdf, pptx, etc.)
            options: Optional dictionary of export options

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_presentation")
