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
        """
        Check if the container/service is running at the platform level.
        
        This method should only check if the container/service is running on the selected platform
        without checking if the daemon inside the container is responsive.
        
        Returns:
            bool: True if the container is running, False otherwise
        """
        pass
        
    @abstractmethod
    def is_daemon_responsive(self) -> bool:
        """
        Check if the daemon API inside the container is responsive.
        
        This method should perform a health check to the daemon API to verify that
        the service inside the container is up and running. It should have its own
        timeout and retry mechanism independent from the container running check.
        
        Returns:
            bool: True if the daemon is responsive, False otherwise
        """
        pass
        
    @abstractmethod
    def is_running_and_responsive(self) -> bool:
        """
        Check if the container is running and the daemon is responsive.
        
        This method should combine the checks from is_running() and is_daemon_responsive()
        to verify that both the container is running at the platform level and
        the daemon inside the container is responsive.
        
        The two checks should be independent and have their own timeout and retry mechanisms.
        
        Returns:
            bool: True if the container is running and the daemon is responsive, False otherwise
        """
        pass
        
    @property
    def daemon_url(self) -> str:
        """Get the full daemon URL including base URL and port."""
        return f"{self.daemon_base_url}:{self.daemon_port}"
