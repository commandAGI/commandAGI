from typing import Optional

try:
    import scrapybara
except ImportError:
    raise ImportError(
        "The Scrapybara dependencies are not installed. Please install commandAGI with the scrapybara extra:\n\npip install commandAGI[scrapybara]"
    )



class UbuntuScrapybaraComputer(BaseScrapybaraComputer):
    """Scrapybara computer specifically for Ubuntu instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _start(self):
        """Start an Ubuntu Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                client = scrapybara.Client(api_key=self.api_key)
            else:
                client = scrapybara.Client()

            # Start an Ubuntu instance
            self.client = client.start_ubuntu()

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executable: Optional[str] = None,
    ):
        """Execute a bash command in the Ubuntu instance."""
        response = self.client.bash(command=command)

    def edit_file(self, path: str, command: str, **kwargs):
        """Edit a file on the Ubuntu instance.

        Args:
            path: Path to the file
            command: Content to write to the file
            **kwargs: Additional arguments to pass to the edit method
        """
        self.client.edit(path=path, command=command, **kwargs)
