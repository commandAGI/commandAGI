from abc import ABC, abstractmethod
from typing import Optional


class BaseComputerProvisioner(ABC):
    def __init__(self, port: int = 8000):
        self.port = port

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