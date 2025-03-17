from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple, Any, Literal

from commandAGI.computers.base_computer.applications.base_paint_editor import BasePaintEditor
from commandAGI.computers.remote_computer.remote_application import RemoteApplication


class RemotePaintEditor(BasePaintEditor, RemoteApplication):
    """Base class for paint/image editor operations.

    This class defines the interface for working with desktop paint/image editors
    like Photoshop, GIMP, Paint.NET, etc. Implementations should provide methods
    to create and modify images through the application's API.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Application Management
    def launch_application(self) -> bool:
        """Launch the image editor application.

        Returns:
            bool: True if application was launched successfully
        """
        raise NotImplementedError("Subclasses must implement launch_application")

    def close_application(self) -> bool:
        """Close the application safely.

        Returns:
            bool: True if application was closed successfully
        """
        raise NotImplementedError("Subclasses must implement close_application")

    # File Operations
    def create_new_image(
        self,
        width: int,
        height: int,
        resolution: int = 72,
        color_mode: Literal["RGB", "CMYK", "Grayscale"] = "RGB",
        background_color: Optional[Tuple[int, int, int]] = None,
        bit_depth: int = 8,
    ) -> bool:
        """Create a new image with specified properties.

        Args:
            width: Width in pixels
            height: Height in pixels
            resolution: Image resolution in DPI
            color_mode: Color mode of the image
            background_color: Optional (R,G,B) color. If None, uses transparent/white.
            bit_depth: Bits per channel

        Returns:
            bool: True if image was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_new_image")

    def open_image(self, file_path: Union[str, Path]) -> bool:
        """Open an image file.

        Args:
            file_path: Path to the image file

        Returns:
            bool: True if image was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_image")

    def save_image(
        self,
        file_path: Optional[Union[str, Path]] = None,
        format: Optional[str] = None,
        quality: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save the current image.

        Args:
            file_path: Optional path to save to. If None, saves to current path.
            format: Optional format override (jpg, png, etc.)
            quality: Optional quality setting (0-100)
            options: Optional format-specific save options

        Returns:
            bool: True if image was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_image")

    # Layer Operations
    def create_layer(
        self, name: str, blend_mode: str = "normal", opacity: float = 100.0
    ) -> str:
        """Create a new layer.

        Args:
            name: Name of the layer
            blend_mode: Blend mode for the layer
            opacity: Layer opacity (0-100)

        Returns:
            str: ID of the created layer
        """
        raise NotImplementedError("Subclasses must implement create_layer")

    def select_layer(self, layer_id: str) -> bool:
        """Select a layer as active.

        Args:
            layer_id: ID of the layer to select

        Returns:
            bool: True if layer was selected successfully
        """
        raise NotImplementedError("Subclasses must implement select_layer")

    def delete_layer(self, layer_id: str) -> bool:
        """Delete a layer.

        Args:
            layer_id: ID of the layer to delete

        Returns:
            bool: True if layer was deleted successfully
        """
        raise NotImplementedError("Subclasses must implement delete_layer")

    def merge_layers(self, layer_ids: List[str]) -> str:
        """Merge multiple layers.

        Args:
            layer_ids: List of layer IDs to merge

        Returns:
            str: ID of the resulting merged layer
        """
        raise NotImplementedError("Subclasses must implement merge_layers")

    # Selection Operations
    def create_selection(
        self,
        shape: Literal["rectangle", "ellipse", "polygon"],
        coordinates: List[Tuple[int, int]],
        feather: int = 0,
    ) -> str:
        """Create a selection area.

        Args:
            shape: Type of selection shape
            coordinates: List of coordinates defining the selection
            feather: Feather radius in pixels

        Returns:
            str: ID of the created selection
        """
        raise NotImplementedError("Subclasses must implement create_selection")

    def modify_selection(
        self,
        operation: Literal["add", "subtract", "intersect"],
        shape: Literal["rectangle", "ellipse", "polygon"],
        coordinates: List[Tuple[int, int]],
    ) -> bool:
        """Modify the current selection.

        Args:
            operation: Type of selection modification
            shape: Shape to use for modification
            coordinates: Coordinates for the modification shape

        Returns:
            bool: True if selection was modified successfully
        """
        raise NotImplementedError("Subclasses must implement modify_selection")

    def clear_selection(self) -> bool:
        """Clear the current selection.

        Returns:
            bool: True if selection was cleared successfully
        """
        raise NotImplementedError("Subclasses must implement clear_selection")

    # Drawing Operations
    def set_tool(
        self, tool_name: str, properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set the active tool and its properties.

        Args:
            tool_name: Name of the tool to activate
            properties: Optional dictionary of tool properties

        Returns:
            bool: True if tool was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_tool")

    def draw_shape(
        self,
        shape_type: str,
        coordinates: List[Tuple[int, int]],
        properties: Dict[str, Any],
    ) -> bool:
        """Draw a shape on the current layer.

        Args:
            shape_type: Type of shape (rectangle, circle, line, etc.)
            coordinates: List of coordinate points defining the shape
            properties: Dictionary of shape properties (color, stroke, fill, etc.)

        Returns:
            bool: True if shape was drawn successfully
        """
        raise NotImplementedError("Subclasses must implement draw_shape")

    def draw_brush_stroke(
        self, points: List[Tuple[int, int]], properties: Dict[str, Any]
    ) -> bool:
        """Draw a brush stroke.

        Args:
            points: List of points defining the stroke path
            properties: Dictionary of brush properties (size, hardness, etc.)

        Returns:
            bool: True if stroke was drawn successfully
        """
        raise NotImplementedError("Subclasses must implement draw_brush_stroke")

    def add_text(
        self, text: str, position: Tuple[int, int], properties: Dict[str, Any]
    ) -> bool:
        """Add text to the image.

        Args:
            text: Text to add
            position: (x, y) coordinates for text placement
            properties: Dictionary of text properties (font, size, color, etc.)

        Returns:
            bool: True if text was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_text")

    # Image Adjustments
    def apply_filter(
        self, filter_type: str, parameters: Dict[str, Any], selection_only: bool = False
    ) -> bool:
        """Apply an image filter.

        Args:
            filter_type: Type of filter to apply
            parameters: Dictionary of filter parameters
            selection_only: Whether to apply only to selected area

        Returns:
            bool: True if filter was applied successfully
        """
        raise NotImplementedError("Subclasses must implement apply_filter")

    def adjust_image(
        self,
        adjustment_type: str,
        parameters: Dict[str, Any],
        selection_only: bool = False,
    ) -> bool:
        """Apply an image adjustment.

        Args:
            adjustment_type: Type of adjustment (levels, curves, etc.)
            parameters: Dictionary of adjustment parameters
            selection_only: Whether to apply only to selected area

        Returns:
            bool: True if adjustment was applied successfully
        """
        raise NotImplementedError("Subclasses must implement adjust_image")

    def apply_color_correction(
        self, correction_type: str, parameters: Dict[str, Any]
    ) -> bool:
        """Apply color correction.

        Args:
            correction_type: Type of color correction
            parameters: Dictionary of correction parameters

        Returns:
            bool: True if correction was applied successfully
        """
        raise NotImplementedError("Subclasses must implement apply_color_correction")

    # Transform Operations
    def crop_image(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        maintain_aspect_ratio: bool = False,
    ) -> bool:
        """Crop the image to specified dimensions.

        Args:
            x: Starting x coordinate
            y: Starting y coordinate
            width: Width of crop area
            height: Height of crop area
            maintain_aspect_ratio: Whether to maintain aspect ratio

        Returns:
            bool: True if image was cropped successfully
        """
        raise NotImplementedError("Subclasses must implement crop_image")

    def resize_image(
        self,
        width: int,
        height: int,
        maintain_aspect_ratio: bool = True,
        resample_method: str = "bicubic",
    ) -> bool:
        """Resize the image.

        Args:
            width: New width in pixels
            height: New height in pixels
            maintain_aspect_ratio: Whether to maintain aspect ratio
            resample_method: Method to use for resampling

        Returns:
            bool: True if image was resized successfully
        """
        raise NotImplementedError("Subclasses must implement resize_image")

    def rotate_image(self, angle: float, expand: bool = True) -> bool:
        """Rotate the image.

        Args:
            angle: Rotation angle in degrees
            expand: Whether to expand canvas to fit rotated image

        Returns:
            bool: True if image was rotated successfully
        """
        raise NotImplementedError("Subclasses must implement rotate_image")

    def flip_image(self, direction: Literal["horizontal", "vertical"]) -> bool:
        """Flip the image.

        Args:
            direction: Direction to flip the image

        Returns:
            bool: True if image was flipped successfully
        """
        raise NotImplementedError("Subclasses must implement flip_image")

    # History Operations
    def undo(self) -> bool:
        """Undo the last operation.

        Returns:
            bool: True if undo was successful
        """
        raise NotImplementedError("Subclasses must implement undo")

    def redo(self) -> bool:
        """Redo the last undone operation.

        Returns:
            bool: True if redo was successful
        """
        raise NotImplementedError("Subclasses must implement redo")

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the operation history.

        Returns:
            List of dictionaries containing operation history
        """
        raise NotImplementedError("Subclasses must implement get_history")

    # Status and Information
    def get_image_info(self) -> Dict[str, Any]:
        """Get information about the current image.

        Returns:
            Dict containing image information (dimensions, color mode, etc.)
        """
        raise NotImplementedError("Subclasses must implement get_image_info")
