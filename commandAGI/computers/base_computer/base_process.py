
class BaseComputerSubprocess(BaseModel):
    """Base class for computer processes."""

    pid: int = Field(description="Process ID")
    executable: str = DEFAULT_SHELL_EXECUTIBLE
    _logger: Optional[logging.Logger] = None
    last_pinfo: Optional[ProcessInfo] = Field(None, description="Last process info")
    _computer: "BaseComputer" = Field(description="Computer instance")

    @property
    def cwd(self) -> Path:
        """Get the current working directory of the shell.

        Returns:
            Path: The current working directory
        """
        raise NotImplementedError("Subclasses must implement cwd getter")
    
    @property
    def env(self) -> Dict[str, str]:
        """Get all environment variables from the shell.

        Returns:
            Dict[str, str]: Dictionary mapping environment variable names to their values
        """
        raise NotImplementedError("Subclasses must implement env getter")

    def read_output(self, timeout: Optional[float] = None, *, encoding: Optional[str] = None) -> str:
        """Read any available output from the shell.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            str: The output from the shell
        """
        raise NotImplementedError("Subclasses must implement read_output")

    def send_input(self, text: str, *, encoding: Optional[str] = None) -> bool:
        """Send input to the shell.

        Args:
            text: The text to send to the shell

        Returns:
            bool: True if the input was sent successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send_input")

    def start(self) -> bool:
        """Start the shell process.

        Returns:
            bool: True if the shell was started successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement start")

    def stop(self) -> bool:
        """Stop the shell process.

        Returns:
            bool: True if the shell was stopped successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement stop")

