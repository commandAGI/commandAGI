from pathlib import Path
from typing import Any, Dict, Optional, Union

from commandAGI.computers.base_computer.base_subprocess import BaseSubprocess


class BaseFreeCAD(BaseSubprocess):
    """Base class for FreeCAD operations.

    This class defines the interface for working with FreeCAD application.
    Implementations should provide methods to interact with FreeCAD's Python API.
    """

    model_config = {"arbitrary_types_allowed": True}

    def open_project(self, file_path: Union[str, Path]) -> bool:
        """Open a FreeCAD project file.

        Args:
            file_path: Path to the FreeCAD file (.FCStd)

        Returns:
            bool: True if project was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_project")

    def save_project(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current project.

        Args:
            file_path: Optional path to save to. If None, saves to current path.

        Returns:
            bool: True if project was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_project")

    def create_document(self, name: str) -> bool:
        """Create a new FreeCAD document.

        Args:
            name: Name of the new document

        Returns:
            bool: True if document was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_document")

    def add_geometry(self, geometry_type: str, parameters: Dict[str, Any]) -> bool:
        """Add geometric objects to the active document.

        Args:
            geometry_type: Type of geometry to create (e.g., 'Box', 'Cylinder', 'Sphere')
            parameters: Dictionary of parameters specific to the geometry type

        Returns:
            bool: True if geometry was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_geometry")

    def execute_macro(self, macro_path: Union[str, Path]) -> bool:
        """Execute a FreeCAD macro file.

        Args:
            macro_path: Path to the macro file (.FCMacro)

        Returns:
            bool: True if macro executed successfully
        """
        raise NotImplementedError("Subclasses must implement execute_macro")

    def export_step(self, output_path: Union[str, Path]) -> bool:
        """Export the active document to STEP format.

        Args:
            output_path: Path where to save the STEP file

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_step")

    def send_command(self, command: str) -> bool:
        """Send a Python command to the FreeCAD application.

        Args:
            command: The Python command to execute in FreeCAD's context

        Returns:
            bool: True if command was executed successfully
        """
        raise NotImplementedError("Subclasses must implement send_command")
