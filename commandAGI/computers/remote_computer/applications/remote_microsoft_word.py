from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from commandAGI.computers.base_computer.applications.base_microsoft_word import (
    BaseMicrosoftWord,
)
from commandAGI.computers.remote_computer.remote_application import RemoteApplication


class RemoteMicrosoftWord(BaseMicrosoftWord, RemoteApplication):
    """Base class for document editor operations.

    This class defines the interface for working with desktop document editors
    like Microsoft Word, WordPad, Apple Pages, etc. Implementations should provide
    methods to create, edit and format documents through the application's API.
    """

    model_config = {"arbitrary_types_allowed": True}

    def launch_application(self) -> bool:
        """Launch the document editor application.

        Returns:
            bool: True if application was launched successfully
        """
        raise NotImplementedError("Subclasses must implement launch_application")

    def create_document(self) -> bool:
        """Create a new blank document.

        Returns:
            bool: True if document was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_document")

    def open_document(self, file_path: Union[str, Path]) -> bool:
        """Open a document file.

        Args:
            file_path: Path to the document file

        Returns:
            bool: True if document was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_document")

    def save_document(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current document.

        Args:
            file_path: Optional path to save to. If None, saves to current path.

        Returns:
            bool: True if document was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_document")

    def get_text(
        self,
        start: Optional[Tuple[int, int]] = None,
        end: Optional[Tuple[int, int]] = None,
    ) -> str:
        """Get text from the document.

        Args:
            start: Optional (paragraph, character) start position
            end: Optional (paragraph, character) end position

        Returns:
            str: The text content
        """
        raise NotImplementedError("Subclasses must implement get_text")

    def insert_text(
        self, text: str, position: Optional[Tuple[int, int]] = None
    ) -> bool:
        """Insert text at specified position.

        Args:
            text: Text to insert
            position: Optional (paragraph, character) position. If None, inserts at cursor.

        Returns:
            bool: True if text was inserted successfully
        """
        raise NotImplementedError("Subclasses must implement insert_text")

    def delete_text(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Delete text in the specified range.

        Args:
            start: (paragraph, character) start position
            end: (paragraph, character) end position

        Returns:
            bool: True if text was deleted successfully
        """
        raise NotImplementedError("Subclasses must implement delete_text")

    def apply_character_formatting(
        self, start: Tuple[int, int], end: Tuple[int, int], formatting: Dict[str, Any]
    ) -> bool:
        """Apply character-level formatting to a range of text.

        Args:
            start: (paragraph, character) start position
            end: (paragraph, character) end position
            formatting: Dictionary of formatting properties (bold, italic, font, size, etc.)

        Returns:
            bool: True if formatting was applied successfully
        """
        raise NotImplementedError(
            "Subclasses must implement apply_character_formatting"
        )

    def apply_paragraph_formatting(
        self, start_para: int, end_para: int, formatting: Dict[str, Any]
    ) -> bool:
        """Apply paragraph-level formatting.

        Args:
            start_para: Start paragraph number
            end_para: End paragraph number
            formatting: Dictionary of formatting properties (alignment, spacing, etc.)

        Returns:
            bool: True if formatting was applied successfully
        """
        raise NotImplementedError(
            "Subclasses must implement apply_paragraph_formatting"
        )

    def insert_image(
        self,
        image_path: Union[str, Path],
        position: Optional[Tuple[int, int]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Insert an image into the document.

        Args:
            image_path: Path to the image file
            position: Optional (paragraph, character) position. If None, inserts at cursor.
            properties: Optional dictionary of image properties (size, layout, etc.)

        Returns:
            bool: True if image was inserted successfully
        """
        raise NotImplementedError("Subclasses must implement insert_image")

    def insert_table(
        self, rows: int, columns: int, position: Optional[Tuple[int, int]] = None
    ) -> bool:
        """Insert a table into the document.

        Args:
            rows: Number of rows
            columns: Number of columns
            position: Optional (paragraph, character) position. If None, inserts at cursor.

        Returns:
            bool: True if table was inserted successfully
        """
        raise NotImplementedError("Subclasses must implement insert_table")

    def add_header(self, text: str, level: int) -> bool:
        """Add a header to the document.

        Args:
            text: Header text
            level: Header level (1-9)

        Returns:
            bool: True if header was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_header")

    def add_footnote(self, text: str, reference_position: Tuple[int, int]) -> bool:
        """Add a footnote to the document.

        Args:
            text: Footnote text
            reference_position: (paragraph, character) position for footnote reference

        Returns:
            bool: True if footnote was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_footnote")

    def export_document(
        self,
        output_path: Union[str, Path],
        format: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Export document to different format.

        Args:
            output_path: Path to save the exported file
            format: Target format (pdf, docx, rtf, etc.)
            options: Optional dictionary of export options

        Returns:
            bool: True if export was successful
        """
        raise NotImplementedError("Subclasses must implement export_document")

    def get_cursor_position(self) -> Tuple[int, int]:
        """Get the current cursor position.

        Returns:
            Tuple[int, int]: Current (paragraph, character) position
        """
        raise NotImplementedError("Subclasses must implement get_cursor_position")

    def set_cursor_position(self, position: Tuple[int, int]) -> bool:
        """Set the cursor position.

        Args:
            position: (paragraph, character) position

        Returns:
            bool: True if cursor was moved successfully
        """
        raise NotImplementedError("Subclasses must implement set_cursor_position")
