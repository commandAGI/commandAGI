from pathlib import Path
from typing import Dict, Optional, List, Union, Any, Tuple, Literal

from commandAGI.computers.base_computer.applications.base_application import BaseApplication


class BaseCursorIDE(BaseApplication):
    """Base class for VSCode IDE operations.

    This class defines the interface for working with VSCode.
    Implementations should provide methods to control VSCode through its extension API,
    command-line interface, and remote development features.
    """

    model_config = {"arbitrary_types_allowed": True}

    def open_file(self, file_path: Union[str, Path], preview: bool = False) -> bool:
        """Open a file in VSCode.

        Args:
            file_path: Path to the file to open
            preview: If True, opens in preview mode

        Returns:
            bool: True if file was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_file")

    def save_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the currently active file.

        Args:
            file_path: Optional path to save to. If None, saves to current path.

        Returns:
            bool: True if file was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_file")

    def save_all(self) -> bool:
        """Save all open files.

        Returns:
            bool: True if all files were saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_all")

    def close_file(self, file_path: Union[str, Path]) -> bool:
        """Close a file in VSCode.

        Args:
            file_path: Path to the file to close

        Returns:
            bool: True if file was closed successfully
        """
        raise NotImplementedError("Subclasses must implement close_file")

    def get_open_files(self) -> List[Path]:
        """Get list of currently open files.

        Returns:
            List[Path]: List of paths to open files
        """
        raise NotImplementedError("Subclasses must implement get_open_files")

    def get_active_file(self) -> Optional[Path]:
        """Get the currently active file.

        Returns:
            Optional[Path]: Path to active file, or None if no file is active
        """
        raise NotImplementedError("Subclasses must implement get_active_file")

    def open_folder(self, folder_path: Union[str, Path], new_window: bool = False) -> bool:
        """Open a folder in VSCode.

        Args:
            folder_path: Path to the folder to open
            new_window: If True, opens in new window

        Returns:
            bool: True if folder was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_folder")

    def get_workspace_folders(self) -> List[Path]:
        """Get list of open workspace folders.

        Returns:
            List[Path]: List of workspace folder paths
        """
        raise NotImplementedError("Subclasses must implement get_workspace_folders")

    def execute_command(self, command_id: str, args: Optional[List[Any]] = None) -> bool:
        """Execute a VSCode command.

        Args:
            command_id: ID of the command to execute
            args: Optional arguments for the command

        Returns:
            bool: True if command was executed successfully
        """
        raise NotImplementedError("Subclasses must implement execute_command")

    def get_editor_selection(self) -> Optional[Tuple[int, int, int, int]]:
        """Get current text selection in active editor.

        Returns:
            Optional[Tuple[int, int, int, int]]: (startLine, startCol, endLine, endCol)
            or None if no selection
        """
        raise NotImplementedError("Subclasses must implement get_editor_selection")

    def insert_text(self, text: str, position: Optional[Tuple[int, int]] = None) -> bool:
        """Insert text at current cursor position or specified position.

        Args:
            text: Text to insert
            position: Optional (line, column) tuple for insertion point

        Returns:
            bool: True if text was inserted successfully
        """
        raise NotImplementedError("Subclasses must implement insert_text")

    def replace_text(self, text: str, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> bool:
        """Replace text in specified range.

        Args:
            text: New text
            start_pos: (line, column) tuple for start of range
            end_pos: (line, column) tuple for end of range

        Returns:
            bool: True if text was replaced successfully
        """
        raise NotImplementedError("Subclasses must implement replace_text")

    def run_task(self, task_name: str) -> bool:
        """Run a VSCode task.

        Args:
            task_name: Name of the task to run

        Returns:
            bool: True if task was started successfully
        """
        raise NotImplementedError("Subclasses must implement run_task")

    def debug_start(self, config_name: str) -> bool:
        """Start debugging with specified launch configuration.

        Args:
            config_name: Name of the launch configuration to use

        Returns:
            bool: True if debug session started successfully
        """
        raise NotImplementedError("Subclasses must implement debug_start")

    def debug_stop(self) -> bool:
        """Stop current debug session.

        Returns:
            bool: True if debug session was stopped successfully
        """
        raise NotImplementedError("Subclasses must implement debug_stop")

    def get_problems(self) -> List[Dict[str, Any]]:
        """Get current diagnostic problems.

        Returns:
            List of problem dictionaries containing severity, message, line, etc.
        """
        raise NotImplementedError("Subclasses must implement get_problems")

    def search_files(self, query: str, include_pattern: Optional[str] = None) -> List[Path]:
        """Search for files in workspace.

        Args:
            query: Search query
            include_pattern: Optional glob pattern to filter files

        Returns:
            List[Path]: Matching file paths
        """
        raise NotImplementedError("Subclasses must implement search_files")

    def install_extension(self, extension_id: str) -> bool:
        """Install a VSCode extension.

        Args:
            extension_id: ID of extension to install

        Returns:
            bool: True if extension was installed successfully
        """
        raise NotImplementedError("Subclasses must implement install_extension")

    def is_running(self) -> bool:
        """Check if VSCode process is running.

        Returns:
            bool: True if VSCode is running, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_running")

    def get_file_contents(self, file_path: Union[str, Path]) -> Optional[str]:
        """Get contents of a file.

        Args:
            file_path: Path to the file

        Returns:
            Optional[str]: File contents or None if file cannot be read
        """
        raise NotImplementedError("Subclasses must implement get_file_contents")

    def create_terminal(self, name: Optional[str] = None, cwd: Optional[Union[str, Path]] = None) -> bool:
        """Create a new integrated terminal.

        Args:
            name: Optional name for the terminal
            cwd: Optional working directory for the terminal

        Returns:
            bool: True if terminal was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_terminal")

    def send_terminal_command(self, command: str, terminal_name: Optional[str] = None) -> bool:
        """Send command to integrated terminal.

        Args:
            command: Command to execute
            terminal_name: Optional terminal name to target specific terminal

        Returns:
            bool: True if command was sent successfully
        """
        raise NotImplementedError("Subclasses must implement send_terminal_command")

    def get_language_at_position(self, file_path: Union[str, Path], position: Tuple[int, int]) -> Optional[str]:
        """Get programming language at specified position.

        Args:
            file_path: Path to the file
            position: (line, column) tuple

        Returns:
            Optional[str]: Language ID or None if unknown
        """
        raise NotImplementedError("Subclasses must implement get_language_at_position")

    def format_document(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Format document using configured formatter.

        Args:
            file_path: Optional path to format specific file, otherwise formats active file

        Returns:
            bool: True if formatting was successful
        """
        raise NotImplementedError("Subclasses must implement format_document")

    def get_code_actions(self, file_path: Union[str, Path], range: Tuple[int, int, int, int]) -> List[Dict[str, Any]]:
        """Get available code actions for specified range.

        Args:
            file_path: Path to the file
            range: (startLine, startCol, endLine, endCol) tuple

        Returns:
            List of available code actions with their details
        """
        raise NotImplementedError("Subclasses must implement get_code_actions")

    def apply_code_action(self, file_path: Union[str, Path], action_id: str) -> bool:
        """Apply a specific code action.

        Args:
            file_path: Path to the file
            action_id: ID of the code action to apply

        Returns:
            bool: True if action was applied successfully
        """
        raise NotImplementedError("Subclasses must implement apply_code_action")

    def get_symbol_references(self, file_path: Union[str, Path], position: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Get all references to symbol at position.

        Args:
            file_path: Path to the file
            position: (line, column) tuple

        Returns:
            List of reference locations with their details
        """
        raise NotImplementedError("Subclasses must implement get_symbol_references")

    def rename_symbol(self, file_path: Union[str, Path], position: Tuple[int, int], new_name: str) -> bool:
        """Rename symbol at position across workspace.

        Args:
            file_path: Path to the file
            position: (line, column) tuple
            new_name: New name for the symbol

        Returns:
            bool: True if rename was successful
        """
        raise NotImplementedError("Subclasses must implement rename_symbol")

    def get_hover_info(self, file_path: Union[str, Path], position: Tuple[int, int]) -> Optional[str]:
        """Get hover information at position.

        Args:
            file_path: Path to the file
            position: (line, column) tuple

        Returns:
            Optional[str]: Hover information or None if not available
        """
        raise NotImplementedError("Subclasses must implement get_hover_info")

    def get_completion_items(self, file_path: Union[str, Path], position: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Get completion items at position.

        Args:
            file_path: Path to the file
            position: (line, column) tuple

        Returns:
            List of completion items with their details
        """
        raise NotImplementedError("Subclasses must implement get_completion_items")

    def set_breakpoint(self, file_path: Union[str, Path], line: int, condition: Optional[str] = None) -> bool:
        """Set a breakpoint in file.

        Args:
            file_path: Path to the file
            line: Line number for breakpoint
            condition: Optional breakpoint condition

        Returns:
            bool: True if breakpoint was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_breakpoint")

    def get_breakpoints(self) -> List[Dict[str, Any]]:
        """Get all configured breakpoints.

        Returns:
            List of breakpoint information
        """
        raise NotImplementedError("Subclasses must implement get_breakpoints")

    def get_call_hierarchy(self, file_path: Union[str, Path], position: Tuple[int, int]) -> Dict[str, Any]:
        """Get call hierarchy for symbol at position.

        Args:
            file_path: Path to the file
            position: (line, column) tuple

        Returns:
            Dictionary containing incoming and outgoing calls
        """
        raise NotImplementedError("Subclasses must implement get_call_hierarchy")

    def get_type_hierarchy(self, file_path: Union[str, Path], position: Tuple[int, int]) -> Dict[str, Any]:
        """Get type hierarchy for symbol at position.

        Args:
            file_path: Path to the file
            position: (line, column) tuple

        Returns:
            Dictionary containing supertypes and subtypes
        """
        raise NotImplementedError("Subclasses must implement get_type_hierarchy")

    def sync_settings(self, settings_path: Optional[Union[str, Path]] = None) -> bool:
        """Sync VSCode settings.

        Args:
            settings_path: Optional path to settings file to sync from

        Returns:
            bool: True if settings were synced successfully
        """
        raise NotImplementedError("Subclasses must implement sync_settings")

    def get_extension_api(self, extension_id: str) -> Optional[Any]:
        """Get API object for installed extension.

        Args:
            extension_id: ID of the extension

        Returns:
            Optional[Any]: Extension API object or None if not available
        """
        raise NotImplementedError("Subclasses must implement get_extension_api")

    def create_workspace(self, folders: List[Union[str, Path]], save_path: Optional[Union[str, Path]] = None) -> bool:
        """Create a multi-root workspace.

        Args:
            folders: List of folder paths to include
            save_path: Optional path to save workspace file

        Returns:
            bool: True if workspace was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_workspace")

    def get_git_changes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get Git changes in workspace.

        Returns:
            Dictionary of changed files grouped by change type
        """
        raise NotImplementedError("Subclasses must implement get_git_changes")

    def run_git_command(self, command: str, args: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """Run Git command in workspace.

        Args:
            command: Git command to run
            args: Optional list of arguments

        Returns:
            Tuple of (success, output)
        """
        raise NotImplementedError("Subclasses must implement run_git_command")

    def get_active_color_theme(self) -> str:
        """Get name of active color theme.

        Returns:
            str: Name of active theme
        """
        raise NotImplementedError("Subclasses must implement get_active_color_theme")

    def set_color_theme(self, theme_name: str) -> bool:
        """Set active color theme.

        Args:
            theme_name: Name of theme to activate

        Returns:
            bool: True if theme was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_color_theme") 