from typing import Optional

try:
    import scrapybara
except ImportError:
    raise ImportError(
        "The Scrapybara dependencies are not installed. Please install commandAGI with the scrapybara extra:\n\npip install commandAGI[scrapybara]"
    )



class BrowserScrapybaraComputer(BaseScrapybaraComputer):
    """Scrapybara computer specifically for Browser instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.client = None

    def _start(self):
        """Start a Browser Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                self.client = scrapybara.Client(api_key=self.api_key)
            else:
                self.client = scrapybara.Client()

            # Start a Browser instance
            self.client = self.client.start_browser()

    def get_cdp_url(self) -> str:
        """Get the Playwright CDP URL for the browser instance."""
        response = self.client.get_cdp_url()
        return response.cdp_url

    def save_auth(self, name: str = "default") -> str:
        """Save the current browser authentication state.

        Args:
            name: Name to identify the saved auth state

        Returns:
            The auth state ID that can be used to restore this state
        """
        response = self.client.save_auth(name=name)
        return response.auth_state_id

    def authenticate(self, auth_state_id: str):
        """Authenticate the browser using a saved auth state.

        Args:
            auth_state_id: The ID of the saved auth state to restore
        """
        self.client.authenticate(auth_state_id=auth_state_id)

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executable: Optional[str] = None,
    ):
        """Execute a command in the browser instance.

        Note: Browser instances don't support bash commands directly.
        This is a limitation of the browser-only environment.
        """
        self.logger.warning("Browser instances don't support direct command execution")
        raise NotImplementedError(
            "Browser instances don't support direct command execution"
        )
