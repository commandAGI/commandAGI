from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple, Any, Literal

from commandAGI.computers.base_computer.applications.base_kicad import BaseKicad
from commandAGI.computers.remote_computer.remote_application import (
    RemoteApplication,
)


class RemoteKicad(BaseKicad, RemoteApplication):
    """Base class for KiCad operations.

    This class defines the interface for working with KiCad for electronic design.
    Implementations should provide methods to interact with KiCad's various tools
    including Eeschema (schematic), Pcbnew (PCB layout), and other utilities.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Application Management
    def launch_application(self) -> bool:
        """Launch the KiCad application.

        Returns:
            bool: True if application was launched successfully
        """
        raise NotImplementedError("Subclasses must implement launch_application")

    def close_application(self) -> bool:
        """Close all KiCad applications safely.

        Returns:
            bool: True if all applications were closed successfully
        """
        raise NotImplementedError("Subclasses must implement close_application")

    # Project Management
    def create_project(
        self, project_path: Union[str, Path], template: Optional[str] = None
    ) -> bool:
        """Create a new KiCad project.

        Args:
            project_path: Path where the project should be created
            template: Optional template name to use for project creation

        Returns:
            bool: True if project was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_project")

    def open_project(self, project_path: Union[str, Path]) -> bool:
        """Open a KiCad project.

        Args:
            project_path: Path to the KiCad project file (.pro)

        Returns:
            bool: True if project was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_project")

    def save_project(self, backup: bool = True) -> bool:
        """Save the current project.

        Args:
            backup: Whether to create a backup before saving

        Returns:
            bool: True if project was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_project")

    def get_project_settings(self) -> Dict[str, Any]:
        """Get current project settings.

        Returns:
            Dict containing project settings
        """
        raise NotImplementedError("Subclasses must implement get_project_settings")

    def set_project_settings(self, settings: Dict[str, Any]) -> bool:
        """Update project settings.

        Args:
            settings: Dictionary of settings to update

        Returns:
            bool: True if settings were updated successfully
        """
        raise NotImplementedError("Subclasses must implement set_project_settings")

    # Library Management
    def add_library(
        self, lib_path: Union[str, Path], lib_type: Literal["symbol", "footprint"]
    ) -> bool:
        """Add a library to the project.

        Args:
            lib_path: Path to the library file/directory
            lib_type: Type of library ("symbol" or "footprint")

        Returns:
            bool: True if library was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_library")

    def create_symbol(self, name: str, properties: Dict[str, Any]) -> str:
        """Create a new symbol in the project library.

        Args:
            name: Name of the symbol
            properties: Dictionary of symbol properties (pins, graphics, etc.)

        Returns:
            str: ID of the created symbol
        """
        raise NotImplementedError("Subclasses must implement create_symbol")

    def create_footprint(self, name: str, properties: Dict[str, Any]) -> str:
        """Create a new footprint in the project library.

        Args:
            name: Name of the footprint
            properties: Dictionary of footprint properties (pads, silkscreen, etc.)

        Returns:
            str: ID of the created footprint
        """
        raise NotImplementedError("Subclasses must implement create_footprint")

    # Schematic Operations (Eeschema)
    def open_schematic_editor(self) -> bool:
        """Open Eeschema (schematic editor).

        Returns:
            bool: True if Eeschema was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_schematic_editor")

    def create_sheet(self, name: str, size: Tuple[float, float]) -> str:
        """Create a new schematic sheet.

        Args:
            name: Name of the sheet
            size: (width, height) of the sheet in mm

        Returns:
            str: ID of the created sheet
        """
        raise NotImplementedError("Subclasses must implement create_sheet")

    def create_component(self, symbol_name: str, properties: Dict[str, Any]) -> str:
        """Create a new component in the schematic.

        Args:
            symbol_name: Name of the symbol to use
            properties: Dictionary of component properties (value, footprint, etc.)

        Returns:
            str: ID of the created component
        """
        raise NotImplementedError("Subclasses must implement create_component")

    def place_component_schematic(
        self,
        component_id: str,
        position: Tuple[float, float],
        rotation: float = 0,
        sheet_name: Optional[str] = None,
    ) -> bool:
        """Place a component in the schematic.

        Args:
            component_id: ID of the component to place
            position: (x, y) coordinates for placement
            rotation: Rotation angle in degrees
            sheet_name: Optional sheet name for hierarchical schematics

        Returns:
            bool: True if component was placed successfully
        """
        raise NotImplementedError("Subclasses must implement place_component_schematic")

    def add_wire(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        sheet_name: Optional[str] = None,
    ) -> str:
        """Add a wire connection in the schematic.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            sheet_name: Optional sheet name for hierarchical schematics

        Returns:
            str: ID of the created wire
        """
        raise NotImplementedError("Subclasses must implement add_wire")

    def add_bus(
        self, start: Tuple[float, float], end: Tuple[float, float], members: List[str]
    ) -> str:
        """Add a bus to the schematic.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            members: List of net names in the bus

        Returns:
            str: ID of the created bus
        """
        raise NotImplementedError("Subclasses must implement add_bus")

    def add_net_label(
        self,
        position: Tuple[float, float],
        name: str,
        style: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a net label in the schematic.

        Args:
            position: (x, y) coordinates for label
            name: Name of the net
            style: Optional dictionary of label style properties

        Returns:
            bool: True if label was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_net_label")

    def add_power_symbol(self, position: Tuple[float, float], power_type: str) -> bool:
        """Add a power symbol to the schematic.

        Args:
            position: (x, y) coordinates for symbol
            power_type: Type of power (GND, VCC, etc.)

        Returns:
            bool: True if symbol was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_power_symbol")

    def add_hierarchical_sheet(
        self,
        position: Tuple[float, float],
        size: Tuple[float, float],
        name: str,
        filename: str,
    ) -> str:
        """Add a hierarchical sheet to the schematic.

        Args:
            position: (x, y) coordinates for sheet
            size: (width, height) of the sheet
            name: Name of the sheet
            filename: Path to the sheet's schematic file

        Returns:
            str: ID of the created sheet
        """
        raise NotImplementedError("Subclasses must implement add_hierarchical_sheet")

    def run_erc(self, severity: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run Electrical Rules Check.

        Args:
            severity: Optional list of severity levels to check ("error", "warning", "info")

        Returns:
            Dict containing ERC results and any violations found
        """
        raise NotImplementedError("Subclasses must implement run_erc")

    def annotate_schematic(self, incremental: bool = True) -> bool:
        """Annotate components in the schematic.

        Args:
            incremental: Whether to perform incremental annotation

        Returns:
            bool: True if annotation was successful
        """
        raise NotImplementedError("Subclasses must implement annotate_schematic")

    # PCB Operations (Pcbnew)
    def open_pcb_editor(self) -> bool:
        """Open Pcbnew (PCB editor).

        Returns:
            bool: True if Pcbnew was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_pcb_editor")

    def setup_board_layers(self, layer_config: Dict[str, Any]) -> bool:
        """Configure PCB layers.

        Args:
            layer_config: Dictionary of layer configurations

        Returns:
            bool: True if layers were configured successfully
        """
        raise NotImplementedError("Subclasses must implement setup_board_layers")

    def set_board_outline(
        self, points: List[Tuple[float, float]], corner_radius: float = 0
    ) -> bool:
        """Set the PCB board outline.

        Args:
            points: List of (x, y) coordinates defining the outline
            corner_radius: Radius for rounded corners in mm

        Returns:
            bool: True if outline was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_board_outline")

    def update_pcb_from_schematic(
        self, mode: Literal["update", "rebuild"] = "update"
    ) -> bool:
        """Update PCB with changes from schematic.

        Args:
            mode: Update mode ("update" preserves layout, "rebuild" starts fresh)

        Returns:
            bool: True if PCB was updated successfully
        """
        raise NotImplementedError("Subclasses must implement update_pcb_from_schematic")

    def place_component_pcb(
        self,
        component_id: str,
        position: Tuple[float, float],
        layer: str,
        rotation: float = 0,
        side: Literal["top", "bottom"] = "top",
    ) -> bool:
        """Place a component on the PCB.

        Args:
            component_id: ID of the component to place
            position: (x, y) coordinates for placement
            layer: Name of the PCB layer
            rotation: Rotation angle in degrees
            side: Which side of the board ("top" or "bottom")

        Returns:
            bool: True if component was placed successfully
        """
        raise NotImplementedError("Subclasses must implement place_component_pcb")

    def route_track(
        self,
        points: List[Tuple[float, float]],
        net_name: str,
        layer: str,
        width: float,
        via_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a PCB track with optional vias.

        Args:
            points: List of (x, y) coordinates defining the track path
            net_name: Name of the net to route
            layer: Name of the PCB layer
            width: Width of the track in mm
            via_config: Optional configuration for automatic via placement

        Returns:
            bool: True if track was routed successfully
        """
        raise NotImplementedError("Subclasses must implement route_track")

    def add_via(
        self,
        position: Tuple[float, float],
        net_name: str,
        size: float,
        drill: float,
        layers: Tuple[str, str],
    ) -> bool:
        """Add a via to the PCB.

        Args:
            position: (x, y) coordinates for via
            net_name: Name of the net
            size: Via diameter in mm
            drill: Drill diameter in mm
            layers: (start_layer, end_layer) for the via

        Returns:
            bool: True if via was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_via")

    def add_zone(
        self,
        layer: str,
        net_name: str,
        points: List[Tuple[float, float]],
        properties: Dict[str, Any],
    ) -> bool:
        """Add a copper zone/pour to the PCB.

        Args:
            layer: Name of the PCB layer
            net_name: Name of the net (e.g. "GND")
            points: List of (x, y) coordinates defining zone boundary
            properties: Dictionary of zone properties (clearance, priority, etc.)

        Returns:
            bool: True if zone was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_zone")

    def add_text(
        self,
        text: str,
        position: Tuple[float, float],
        layer: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Add text to the PCB.

        Args:
            text: Text to add
            position: (x, y) coordinates for text
            layer: Name of the PCB layer
            properties: Dictionary of text properties (size, style, etc.)

        Returns:
            bool: True if text was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_text")

    def add_dimension(
        self, start: Tuple[float, float], end: Tuple[float, float], layer: str
    ) -> bool:
        """Add a dimension measurement to the PCB.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            layer: Name of the PCB layer

        Returns:
            bool: True if dimension was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_dimension")

    def run_drc(self, rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run Design Rules Check.

        Args:
            rules: Optional dictionary of custom DRC rules

        Returns:
            Dict containing DRC results and any violations found
        """
        raise NotImplementedError("Subclasses must implement run_drc")

    def run_length_tuning(
        self, nets: List[str], target_length: float, tolerance: float
    ) -> bool:
        """Perform length tuning on specified nets.

        Args:
            nets: List of net names to tune
            target_length: Target length in mm
            tolerance: Acceptable deviation in mm

        Returns:
            bool: True if tuning was successful
        """
        raise NotImplementedError("Subclasses must implement run_length_tuning")

    # Manufacturing Outputs
    def export_gerber(
        self,
        output_dir: Union[str, Path],
        layers: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Export Gerber files for PCB manufacturing.

        Args:
            output_dir: Directory to save Gerber files
            layers: Optional list of layers to export. If None, exports all.
            settings: Optional dictionary of export settings

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_gerber")

    def export_drill_files(
        self,
        output_dir: Union[str, Path],
        format: Literal["excellon", "gerber"] = "excellon",
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Export drill files for PCB manufacturing.

        Args:
            output_dir: Directory to save drill files
            format: Format of drill files
            options: Optional dictionary of export options

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_drill_files")

    def export_bom(
        self,
        output_path: Union[str, Path],
        format: str = "csv",
        grouping: Optional[List[str]] = None,
    ) -> bool:
        """Export Bill of Materials.

        Args:
            output_path: Path to save the BOM file
            format: Output format (csv, xml, etc.)
            grouping: Optional list of fields to group by

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_bom")

    def export_position_file(
        self, output_path: Union[str, Path], format: str = "csv"
    ) -> bool:
        """Export component position file for assembly.

        Args:
            output_path: Path to save the position file
            format: Output format (csv, txt, etc.)

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_position_file")

    # 3D Visualization
    def export_step(
        self, output_path: Union[str, Path], include_models: bool = True
    ) -> bool:
        """Export 3D model as STEP file.

        Args:
            output_path: Path to save the STEP file
            include_models: Whether to include 3D models for components

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_step")

    def render_3d(self, output_path: Union[str, Path], view: Dict[str, Any]) -> bool:
        """Generate a 3D render of the PCB.

        Args:
            output_path: Path to save the rendered image
            view: Dictionary defining view parameters (angle, zoom, etc.)

        Returns:
            bool: True if render was successful
        """
        raise NotImplementedError("Subclasses must implement render_3d")

    # Status and Validation
    def get_statistics(self) -> Dict[str, Any]:
        """Get project statistics.

        Returns:
            Dict containing statistics (component count, track length, etc.)
        """
        raise NotImplementedError("Subclasses must implement get_statistics")

    def validate_design(self) -> Dict[str, Any]:
        """Perform comprehensive design validation.

        Returns:
            Dict containing validation results from all checks
        """
        raise NotImplementedError("Subclasses must implement validate_design")

    def execute_command(self, command: str) -> bool:
        """Execute a KiCad command.

        Args:
            command: The command to execute

        Returns:
            bool: True if command was executed successfully
        """
        raise NotImplementedError("Subclasses must implement execute_command")
