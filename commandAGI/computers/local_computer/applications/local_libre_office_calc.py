from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from commandAGI.computers.base_computer.applications.base_libreoffice_calc import (
    BaseLibreOfficeCalc,
)
from commandAGI.computers.local_computer.local_subprocess import LocalApplication


class LocalLibreOfficeCalc(BaseLibreOfficeCalc, LocalApplication):
    """Local class for spreadsheet operations.

    This class defines the interface for working with desktop spreadsheet applications
    like Microsoft Excel, Apple Numbers, etc. Implementations should provide methods
    to create and modify spreadsheets through the application's API.
    """

    model_config = {"arbitrary_types_allowed": True}

    def launch_application(self) -> bool:
        """Launch the spreadsheet application.

        Returns:
            bool: True if application was launched successfully
        """
        raise NotImplementedError("Subclasses must implement launch_application")

    def create_workbook(self) -> bool:
        """Create a new blank workbook.

        Returns:
            bool: True if workbook was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_workbook")

    def open_workbook(self, file_path: Union[str, Path]) -> bool:
        """Open a workbook file.

        Args:
            file_path: Path to the workbook file

        Returns:
            bool: True if workbook was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_workbook")

    def save_workbook(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current workbook.

        Args:
            file_path: Optional path to save to. If None, saves to current path.

        Returns:
            bool: True if workbook was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_workbook")

    def create_sheet(self, name: str, position: Optional[int] = None) -> bool:
        """Create a new worksheet.

        Args:
            name: Name of the new worksheet
            position: Optional position in the workbook tabs

        Returns:
            bool: True if worksheet was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_sheet")

    def delete_sheet(self, name: str) -> bool:
        """Delete a worksheet.

        Args:
            name: Name of the worksheet to delete

        Returns:
            bool: True if worksheet was deleted successfully
        """
        raise NotImplementedError("Subclasses must implement delete_sheet")

    def rename_sheet(self, old_name: str, new_name: str) -> bool:
        """Rename a worksheet.

        Args:
            old_name: Current name of the worksheet
            new_name: New name for the worksheet

        Returns:
            bool: True if worksheet was renamed successfully
        """
        raise NotImplementedError("Subclasses must implement rename_sheet")

    def get_active_sheet(self) -> str:
        """Get the name of the active worksheet.

        Returns:
            str: Name of the active worksheet
        """
        raise NotImplementedError("Subclasses must implement get_active_sheet")

    def select_sheet(self, name: str) -> bool:
        """Select/activate a worksheet.

        Args:
            name: Name of the worksheet to select

        Returns:
            bool: True if worksheet was selected successfully
        """
        raise NotImplementedError("Subclasses must implement select_sheet")

    def get_cell_value(self, cell: str) -> Any:
        """Get the value of a cell.

        Args:
            cell: Cell reference (e.g. 'A1')

        Returns:
            The cell value
        """
        raise NotImplementedError("Subclasses must implement get_cell_value")

    def set_cell_value(self, cell: str, value: Any) -> bool:
        """Set the value of a cell.

        Args:
            cell: Cell reference (e.g. 'A1')
            value: Value to set

        Returns:
            bool: True if value was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_cell_value")

    def get_range_values(self, range: str) -> List[List[Any]]:
        """Get values from a range of cells.

        Args:
            range: Cell range (e.g. 'A1:B10')

        Returns:
            List[List[Any]]: 2D array of cell values
        """
        raise NotImplementedError("Subclasses must implement get_range_values")

    def set_range_values(self, range: str, values: List[List[Any]]) -> bool:
        """Set values for a range of cells.

        Args:
            range: Cell range (e.g. 'A1:B10')
            values: 2D array of values to set

        Returns:
            bool: True if values were set successfully
        """
        raise NotImplementedError("Subclasses must implement set_range_values")

    def set_cell_formula(self, cell: str, formula: str) -> bool:
        """Set a formula in a cell.

        Args:
            cell: Cell reference (e.g. 'A1')
            formula: Formula string (should start with '=')

        Returns:
            bool: True if formula was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_cell_formula")

    def apply_cell_formatting(self, range: str, formatting: Dict[str, Any]) -> bool:
        """Apply formatting to a range of cells.

        Args:
            range: Cell range (e.g. 'A1:B10')
            formatting: Dictionary of formatting properties (font, color, borders, etc.)

        Returns:
            bool: True if formatting was applied successfully
        """
        raise NotImplementedError("Subclasses must implement apply_cell_formatting")

    def insert_chart(
        self,
        range: str,
        chart_type: str,
        position: Tuple[str, str],
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Insert a chart using data from specified range.

        Args:
            range: Data range for the chart (e.g. 'A1:B10')
            chart_type: Type of chart (line, bar, pie, etc.)
            position: (top_left_cell, bottom_right_cell) for chart placement
            properties: Optional dictionary of chart properties

        Returns:
            bool: True if chart was inserted successfully
        """
        raise NotImplementedError("Subclasses must implement insert_chart")

    def auto_filter(self, range: str) -> bool:
        """Apply auto-filter to a range.

        Args:
            range: Cell range to filter (e.g. 'A1:B10')

        Returns:
            bool: True if filter was applied successfully
        """
        raise NotImplementedError("Subclasses must implement auto_filter")

    def sort_range(self, range: str, sort_by: List[Tuple[int, bool]]) -> bool:
        """Sort a range of cells.

        Args:
            range: Cell range to sort (e.g. 'A1:B10')
            sort_by: List of (column_index, ascending) tuples defining sort order

        Returns:
            bool: True if range was sorted successfully
        """
        raise NotImplementedError("Subclasses must implement sort_range")

    def export_sheet(
        self,
        output_path: Union[str, Path],
        format: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Export worksheet to different format.

        Args:
            output_path: Path to save the exported file
            format: Target format (csv, pdf, xlsx, etc.)
            options: Optional dictionary of export options

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_sheet")

    def get_selected_range(self) -> Optional[str]:
        """Get the currently selected cell range.

        Returns:
            Optional[str]: Selected range (e.g. 'A1:B10') or None if no selection
        """
        raise NotImplementedError("Subclasses must implement get_selected_range")
