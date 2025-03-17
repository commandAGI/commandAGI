from pathlib import Path
from typing import Dict, Optional, List, Union, Any, Tuple

from commandAGI.computers.base_computer.applications.base_application import (
    BaseApplication,
)


class BaseTextEditor(BaseApplication):
    """Base class for Text Editor operations.

    This class defines the interface for working with text editors.
    Implementations should provide methods to edit and manipulate text files.
    """

    model_config = {"arbitrary_types_allowed": True}

    def open_file(self, file_path: Union[str, Path]) -> bool:
        """Open a file in the editor.

        Args:
            file_path: Path to the file to open

        Returns:
            bool: True if file was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_file")

    def save_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current file.

        Args:
            file_path: Optional path to save to. If None, saves to current path.

        Returns:
            bool: True if file was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_file")

    def get_text(self) -> Optional[str]:
        """Get entire text content.

        Returns:
            Optional[str]: Text content or None if not available
        """
        raise NotImplementedError("Subclasses must implement get_text")

    def set_text(self, text: str) -> bool:
        """Replace entire text content.

        Args:
            text: New text content

        Returns:
            bool: True if text was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_text")

    def insert_text(
        self, text: str, position: Optional[Tuple[int, int]] = None
    ) -> bool:
        """Insert text at position.

        Args:
            text: Text to insert
            position: Optional (line, column) tuple for insertion point

        Returns:
            bool: True if text was inserted successfully
        """
        raise NotImplementedError("Subclasses must implement insert_text")

    def delete_text(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> bool:
        """Delete text in range.

        Args:
            start_pos: (line, column) tuple for start of range
            end_pos: (line, column) tuple for end of range

        Returns:
            bool: True if text was deleted successfully
        """
        raise NotImplementedError("Subclasses must implement delete_text")

    def find_text(
        self, search_text: str, case_sensitive: bool = False
    ) -> List[Tuple[int, int]]:
        """Find all occurrences of text.

        Args:
            search_text: Text to search for
            case_sensitive: If True, match case

        Returns:
            List of (line, column) tuples for matches
        """
        raise NotImplementedError("Subclasses must implement find_text")

    def replace_text(
        self,
        search_text: str,
        replace_text: str,
        case_sensitive: bool = False,
        all_occurrences: bool = False,
    ) -> int:
        """Replace text occurrences.

        Args:
            search_text: Text to search for
            replace_text: Text to replace with
            case_sensitive: If True, match case
            all_occurrences: If True, replaces all matches

        Returns:
            Number of replacements made
        """
        raise NotImplementedError("Subclasses must implement replace_text")

    def get_line_count(self) -> int:
        """Get total number of lines.

        Returns:
            int: Number of lines
        """
        raise NotImplementedError("Subclasses must implement get_line_count")

    def get_line(self, line_number: int) -> Optional[str]:
        """Get text of specific line.

        Args:
            line_number: Line number (0-based)

        Returns:
            Optional[str]: Line text or None if invalid line
        """
        raise NotImplementedError("Subclasses must implement get_line")

    def set_line(self, line_number: int, text: str) -> bool:
        """Replace text of specific line.

        Args:
            line_number: Line number (0-based)
            text: New line text

        Returns:
            bool: True if line was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_line")

    def get_selection(self) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Get current text selection.

        Returns:
            Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
            ((start_line, start_col), (end_line, end_col)) or None if no selection
        """
        raise NotImplementedError("Subclasses must implement get_selection")

    def set_selection(
        self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]
    ) -> bool:
        """Set text selection.

        Args:
            start_pos: (line, column) tuple for selection start
            end_pos: (line, column) tuple for selection end

        Returns:
            bool: True if selection was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_selection")

    def undo(self) -> bool:
        """Undo last edit operation.

        Returns:
            bool: True if undo was successful
        """
        raise NotImplementedError("Subclasses must implement undo")

    def redo(self) -> bool:
        """Redo last undone operation.

        Returns:
            bool: True if redo was successful
        """
        raise NotImplementedError("Subclasses must implement redo")

    def is_running(self) -> bool:
        """Check if text editor is running.

        Returns:
            bool: True if editor is running
        """
        raise NotImplementedError("Subclasses must implement is_running")
