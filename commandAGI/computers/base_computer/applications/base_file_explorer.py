from pathlib import Path
from typing import Any, Dict, List, Literal, Union

from commandAGI.computers.base_computer.base_application import BaseApplication


class BaseFileExplorer(BaseApplication):
    """Base class for File Explorer operations.

    This class defines the interface for working with the system's file explorer.
    Implementations should provide methods to navigate, manipulate files and folders,
    and handle file system operations.
    """

    model_config = {"arbitrary_types_allowed": True}

    def open_folder(
        self, folder_path: Union[str, Path], new_window: bool = False
    ) -> bool:
        """Open a folder in file explorer.

        Args:
            folder_path: Path to the folder to open
            new_window: If True, opens in new window

        Returns:
            bool: True if folder was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_folder")

    def select_file(self, file_path: Union[str, Path]) -> bool:
        """Select a file in the current explorer window.

        Args:
            file_path: Path to the file to select

        Returns:
            bool: True if file was selected successfully
        """
        raise NotImplementedError("Subclasses must implement select_file")

    def copy_files(
        self, source_paths: List[Union[str, Path]], destination: Union[str, Path]
    ) -> bool:
        """Copy files or folders to destination.

        Args:
            source_paths: List of paths to copy
            destination: Destination path

        Returns:
            bool: True if copy operation was successful
        """
        raise NotImplementedError("Subclasses must implement copy_files")

    def move_files(
        self, source_paths: List[Union[str, Path]], destination: Union[str, Path]
    ) -> bool:
        """Move files or folders to destination.

        Args:
            source_paths: List of paths to move
            destination: Destination path

        Returns:
            bool: True if move operation was successful
        """
        raise NotImplementedError("Subclasses must implement move_files")

    def delete_files(
        self, paths: List[Union[str, Path]], permanent: bool = False
    ) -> bool:
        """Delete files or folders.

        Args:
            paths: List of paths to delete
            permanent: If True, bypasses recycle bin/trash

        Returns:
            bool: True if deletion was successful
        """
        raise NotImplementedError("Subclasses must implement delete_files")

    def create_folder(self, path: Union[str, Path]) -> bool:
        """Create a new folder.

        Args:
            path: Path where to create the folder

        Returns:
            bool: True if folder was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_folder")

    def rename_item(self, path: Union[str, Path], new_name: str) -> bool:
        """Rename a file or folder.

        Args:
            path: Path to the item to rename
            new_name: New name for the item

        Returns:
            bool: True if rename was successful
        """
        raise NotImplementedError("Subclasses must implement rename_item")

    def get_properties(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Get properties of a file or folder.

        Args:
            path: Path to the item

        Returns:
            Dictionary containing item properties
        """
        raise NotImplementedError("Subclasses must implement get_properties")

    def search(
        self, query: str, location: Union[str, Path], recursive: bool = True
    ) -> List[Path]:
        """Search for files and folders.

        Args:
            query: Search query
            location: Path to search in
            recursive: If True, searches in subfolders

        Returns:
            List of matching paths
        """
        raise NotImplementedError("Subclasses must implement search")

    def get_drive_info(self) -> List[Dict[str, Any]]:
        """Get information about available drives.

        Returns:
            List of drive information dictionaries
        """
        raise NotImplementedError("Subclasses must implement get_drive_info")

    def compress_items(
        self,
        paths: List[Union[str, Path]],
        archive_path: Union[str, Path],
        format: Literal["zip", "7z", "tar", "rar"] = "zip",
    ) -> bool:
        """Compress files and folders into an archive.

        Args:
            paths: List of paths to compress
            archive_path: Path for the resulting archive
            format: Archive format to use

        Returns:
            bool: True if compression was successful
        """
        raise NotImplementedError("Subclasses must implement compress_items")

    def extract_archive(
        self, archive_path: Union[str, Path], destination: Union[str, Path]
    ) -> bool:
        """Extract an archive.

        Args:
            archive_path: Path to the archive
            destination: Extraction destination path

        Returns:
            bool: True if extraction was successful
        """
        raise NotImplementedError("Subclasses must implement extract_archive")

    def get_folder_size(self, folder_path: Union[str, Path]) -> int:
        """Calculate total size of a folder.

        Args:
            folder_path: Path to the folder

        Returns:
            Size in bytes
        """
        raise NotImplementedError("Subclasses must implement get_folder_size")

    def set_attributes(
        self, path: Union[str, Path], attributes: Dict[str, Any]
    ) -> bool:
        """Set file or folder attributes.

        Args:
            path: Path to the item
            attributes: Dictionary of attributes to set

        Returns:
            bool: True if attributes were set successfully
        """
        raise NotImplementedError("Subclasses must implement set_attributes")

    def is_running(self) -> bool:
        """Check if file explorer process is running.

        Returns:
            bool: True if file explorer is running
        """
        raise NotImplementedError("Subclasses must implement is_running")
