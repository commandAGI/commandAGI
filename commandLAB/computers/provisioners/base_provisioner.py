from abc import ABC, abstractmethod
from typing import Optional, Tuple
import secrets


class BaseComputerProvisioner(ABC):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = 8000,
        port_range: Optional[Tuple[int, int]] = None,
        daemon_token: Optional[str] = None,
    ):
        """Initialize the base provisioner.
        
        Args:
            daemon_base_url: Base URL for the daemon service
            daemon_port: Preferred port for the daemon service
            port_range: Optional range of ports to try if preferred port is unavailable
            daemon_token: Authentication token for the daemon service. If None, a random token will be generated.
        """
        self.daemon_base_url = daemon_base_url
        self.daemon_port = daemon_port
        self.port_range = port_range
        self.daemon_token = daemon_token or secrets.token_urlsafe(32)

    @abstractmethod
    def setup(self) -> None:
        """Setup the daemon with the specific provisioning method"""
        pass

    @abstractmethod
    def teardown(self) -> None:
        """Cleanup any resources created during setup"""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if the daemon is running"""
        pass
        
    @property
    def daemon_url(self) -> str:
        """Get the full daemon URL including base URL and port."""
        return f"{self.daemon_base_url}:{self.daemon_port}"
