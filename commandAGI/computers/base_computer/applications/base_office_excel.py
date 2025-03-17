from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple, Any

from commandAGI.computers.base_computer.applications.base_application import BaseApplication


class BaseExcel(BaseApplication):
    """Base class for Excel spreadsheet operations.

    This class defines the interface for working with Microsoft Excel. Implementations
    should provide methods to create and modify spreadsheets through Excel's API.
    """

    model_config = {"arbitrary_types_allowed": True}

    def launch_application(self) -> bool:
        """Launch Excel application."""
        raise NotImplementedError("Subclasses must implement launch_application")

    def create_workbook(self) -> bool:
        """Create a new blank workbook."""
        raise NotImplementedError("Subclasses must implement create_workbook")

    def open_workbook(self, file_path: Union[str, Path]) -> bool:
        """Open an Excel workbook."""
        raise NotImplementedError("Subclasses must implement open_workbook")

    def save_workbook(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current workbook."""
        raise NotImplementedError("Subclasses must implement save_workbook")

    def create_sheet(self, name: str, position: Optional[int] = None) -> bool:
        """Create a new worksheet."""
        raise NotImplementedError("Subclasses must implement create_sheet")

    def delete_sheet(self, name: str) -> bool:
        """Delete a worksheet."""
        raise NotImplementedError("Subclasses must implement delete_sheet")

    def rename_sheet(self, old_name: str, new_name: str) -> bool:
        """Rename a worksheet."""
        raise NotImplementedError("Subclasses must implement rename_sheet")

    def get_active_sheet(self) -> str:
        """Get the name of the active worksheet."""
        raise NotImplementedError("Subclasses must implement get_active_sheet")

    def select_sheet(self, name: str) -> bool:
        """Select/activate a worksheet."""
        raise NotImplementedError("Subclasses must implement select_sheet")

    def get_cell_value(self, cell: str) -> Any:
        """Get the value of a cell."""
        raise NotImplementedError("Subclasses must implement get_cell_value")

    def set_cell_value(self, cell: str, value: Any) -> bool:
        """Set the value of a cell."""
        raise NotImplementedError("Subclasses must implement set_cell_value")

    def get_range_values(self, range: str) -> List[List[Any]]:
        """Get values from a range of cells."""
        raise NotImplementedError("Subclasses must implement get_range_values")

    def set_range_values(self, range: str, values: List[List[Any]]) -> bool:
        """Set values for a range of cells."""
        raise NotImplementedError("Subclasses must implement set_range_values")

    def set_cell_formula(self, cell: str, formula: str) -> bool:
        """Set a formula in a cell."""
        raise NotImplementedError("Subclasses must implement set_cell_formula")

    def apply_cell_formatting(self, range: str, formatting: Dict[str, Any]) -> bool:
        """Apply formatting to a range of cells."""
        raise NotImplementedError("Subclasses must implement apply_cell_formatting")

    def insert_chart(self, range: str, chart_type: str,
                    position: Tuple[str, str],
                    properties: Optional[Dict[str, Any]] = None) -> bool:
        """Insert a chart using data from specified range."""
        raise NotImplementedError("Subclasses must implement insert_chart")

    def auto_filter(self, range: str) -> bool:
        """Apply auto-filter to a range."""
        raise NotImplementedError("Subclasses must implement auto_filter")

    def sort_range(self, range: str, sort_by: List[Tuple[int, bool]]) -> bool:
        """Sort a range of cells."""
        raise NotImplementedError("Subclasses must implement sort_range")

    def export_sheet(self, output_path: Union[str, Path],
                    format: str,
                    options: Optional[Dict[str, Any]] = None) -> bool:
        """Export worksheet to different format."""
        raise NotImplementedError("Subclasses must implement export_sheet")

    def get_selected_range(self) -> Optional[str]:
        """Get the currently selected cell range."""
        raise NotImplementedError("Subclasses must implement get_selected_range")
