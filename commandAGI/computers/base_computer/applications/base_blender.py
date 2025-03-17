from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple, Any

from commandAGI.computers.base_computer.applications.base_application import (
    BaseApplication,
)


class BaseBlender(BaseApplication):
    """Base class for Blender operations.

    This class defines the interface for working with Blender for 3D modeling.
    Implementations should provide methods to create and modify 3D models,
    animations, and manage Blender projects through Blender's Python API.
    """

    model_config = {"arbitrary_types_allowed": True}

    def open_project(self, project_path: Union[str, Path]) -> bool:
        """Open a Blender project file.

        Args:
            project_path: Path to the .blend file

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

    def create_object(
        self, obj_type: str, name: str, parameters: Dict[str, Any]
    ) -> bool:
        """Create a new object in the scene.

        Args:
            obj_type: Type of object ('MESH', 'CURVE', 'LIGHT', etc.)
            name: Name for the new object
            parameters: Dictionary of parameters for object creation

        Returns:
            bool: True if object was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_object")

    def modify_object(
        self, obj_name: str, operation: str, parameters: Dict[str, Any]
    ) -> bool:
        """Apply a modifier or operation to an object.

        Args:
            obj_name: Name of the target object
            operation: Type of operation ('SUBSURF', 'BOOLEAN', 'ARRAY', etc.)
            parameters: Dictionary of parameters for the operation

        Returns:
            bool: True if modification was successful
        """
        raise NotImplementedError("Subclasses must implement modify_object")

    def set_material(self, obj_name: str, material_params: Dict[str, Any]) -> bool:
        """Create and assign a material to an object.

        Args:
            obj_name: Name of the target object
            material_params: Dictionary of material properties

        Returns:
            bool: True if material was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_material")

    def set_animation(self, obj_name: str, keyframes: List[Dict[str, Any]]) -> bool:
        """Set animation keyframes for an object.

        Args:
            obj_name: Name of the object to animate
            keyframes: List of keyframe data (frame, location, rotation, scale)

        Returns:
            bool: True if animation was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_animation")

    def render(self, output_path: Union[str, Path], parameters: Dict[str, Any]) -> bool:
        """Render the current scene.

        Args:
            output_path: Path to save the rendered output
            parameters: Dictionary containing render settings like:
                - resolution: Tuple[int, int] for width/height
                - engine: 'CYCLES' or 'EEVEE'
                - samples: int for render samples
                - format: 'PNG', 'JPEG', 'EXR', etc.

        Returns:
            bool: True if render was successful
        """
        raise NotImplementedError("Subclasses must implement render")

    def import_model(self, file_path: Union[str, Path], import_type: str) -> bool:
        """Import an external 3D model file.

        Args:
            file_path: Path to the model file
            import_type: Format type ('obj', 'fbx', 'gltf', etc.)

        Returns:
            bool: True if import was successful
        """
        raise NotImplementedError("Subclasses must implement import_model")

    def export_model(
        self, file_path: Union[str, Path], export_type: str, parameters: Dict[str, Any]
    ) -> bool:
        """Export the scene or selected objects.

        Args:
            file_path: Path to save the exported file
            export_type: Format type ('obj', 'fbx', 'gltf', etc.)
            parameters: Export parameters specific to the format

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_model")

    def send_command(self, command: str) -> bool:
        """Send a Python command to Blender's Python interpreter.

        Args:
            command: The Python command to execute in Blender's context

        Returns:
            bool: True if command was executed successfully
        """
        raise NotImplementedError("Subclasses must implement send_command")

    def run_script(self, script_path: Union[str, Path]) -> bool:
        """Execute a Python script in Blender's context.

        Args:
            script_path: Path to the Python script file

        Returns:
            bool: True if script executed successfully
        """
        raise NotImplementedError("Subclasses must implement run_script")
