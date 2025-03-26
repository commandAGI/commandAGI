from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from commandAGI.computers.base_computer.applications.base_chrome_browser import (
    BaseChromeBrowser,
)
from commandAGI.computers.local_computer.local_subprocess import LocalApplication


class LocalChromeBrowser(BaseChromeBrowser, LocalApplication):
    """Local class for Chrome browser operations.

    This class defines the interface for controlling Chrome browser.
    Implementations should provide methods to navigate, manipulate tabs,
    and interact with web content.
    """

    model_config = {"arbitrary_types_allowed": True}

    def navigate(self, url: str, new_tab: bool = False) -> bool:
        """Navigate to a URL.

        Args:
            url: URL to navigate to
            new_tab: If True, opens in new tab

        Returns:
            bool: True if navigation was successful
        """
        raise NotImplementedError("Subclasses must implement navigate")

    def get_current_url(self) -> Optional[str]:
        """Get URL of current tab.

        Returns:
            Optional[str]: Current URL or None if not available
        """
        raise NotImplementedError("Subclasses must implement get_current_url")

    def get_page_title(self) -> Optional[str]:
        """Get title of current page.

        Returns:
            Optional[str]: Page title or None if not available
        """
        raise NotImplementedError("Subclasses must implement get_page_title")

    def refresh_page(self) -> bool:
        """Refresh current page.

        Returns:
            bool: True if refresh was successful
        """
        raise NotImplementedError("Subclasses must implement refresh_page")

    def go_back(self) -> bool:
        """Navigate back in history.

        Returns:
            bool: True if navigation was successful
        """
        raise NotImplementedError("Subclasses must implement go_back")

    def go_forward(self) -> bool:
        """Navigate forward in history.

        Returns:
            bool: True if navigation was successful
        """
        raise NotImplementedError("Subclasses must implement go_forward")

    def create_tab(self, url: Optional[str] = None) -> bool:
        """Create a new tab.

        Args:
            url: Optional URL to navigate to

        Returns:
            bool: True if tab was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_tab")

    def close_tab(self, tab_id: Optional[str] = None) -> bool:
        """Close a tab.

        Args:
            tab_id: Optional ID of tab to close, closes current if None

        Returns:
            bool: True if tab was closed successfully
        """
        raise NotImplementedError("Subclasses must implement close_tab")

    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get information about all open tabs.

        Returns:
            List of tab information dictionaries
        """
        raise NotImplementedError("Subclasses must implement get_tabs")

    def switch_tab(self, tab_id: str) -> bool:
        """Switch to specified tab.

        Args:
            tab_id: ID of tab to switch to

        Returns:
            bool: True if switch was successful
        """
        raise NotImplementedError("Subclasses must implement switch_tab")

    def execute_script(self, script: str) -> Any:
        """Execute JavaScript in current tab.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of script execution
        """
        raise NotImplementedError("Subclasses must implement execute_script")

    def get_cookies(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get browser cookies.

        Args:
            domain: Optional domain to filter cookies

        Returns:
            List of cookie dictionaries
        """
        raise NotImplementedError("Subclasses must implement get_cookies")

    def set_cookie(self, cookie_data: Dict[str, Any]) -> bool:
        """Set a browser cookie.

        Args:
            cookie_data: Cookie data dictionary

        Returns:
            bool: True if cookie was set successfully
        """
        raise NotImplementedError("Subclasses must implement set_cookie")

    def clear_cookies(self, domain: Optional[str] = None) -> bool:
        """Clear browser cookies.

        Args:
            domain: Optional domain to clear cookies for

        Returns:
            bool: True if cookies were cleared successfully
        """
        raise NotImplementedError("Subclasses must implement clear_cookies")

    def download_file(self, url: str, destination: Union[str, Path]) -> bool:
        """Download a file.

        Args:
            url: URL to download from
            destination: Path to save the file

        Returns:
            bool: True if download was successful
        """
        raise NotImplementedError("Subclasses must implement download_file")

    def take_screenshot(self, path: Union[str, Path], full_page: bool = False) -> bool:
        """Take a screenshot of current page.

        Args:
            path: Path to save the screenshot
            full_page: If True, captures entire page

        Returns:
            bool: True if screenshot was taken successfully
        """
        raise NotImplementedError("Subclasses must implement take_screenshot")

    def get_page_source(self) -> Optional[str]:
        """Get HTML source of current page.

        Returns:
            Optional[str]: Page source or None if not available
        """
        raise NotImplementedError("Subclasses must implement get_page_source")

    def is_running(self) -> bool:
        """Check if Chrome browser is running.

        Returns:
            bool: True if browser is running
        """
        raise NotImplementedError("Subclasses must implement is_running")
