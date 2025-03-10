from typing import Optional

from commandAGI.computers.clients.base_computer_client import BaseComputerComputerClient, ComputerClientStatus


class ManualComputerClient(BaseComputerComputerClient):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: int = 8000,
        daemon_token: Optional[str] = None,
        max_provisioning_retries: int = 1,
        timeout: int = 60,
        max_health_retries: int = 1,
        health_check_timeout: int = 30,
    ):
        super().__init__(
            daemon_base_url=daemon_base_url,
            daemon_port=daemon_port,
            daemon_token=daemon_token,
            max_provisioning_retries=max_provisioning_retries,
            timeout=timeout,
            max_health_retries=max_health_retries,
            health_check_timeout=health_check_timeout,
        )

    def _provision_resource(self) -> None:
        """Provide instructions for manual daemon setup"""
        print(f"If you haven't already, please start the daemon manually using:")
        print(f"pip install commandagi[local,daemon]")
        print(
            f"python -m commandagi.daemon.daemon --port {
                self.daemon_port} --token {
                self.daemon_token} --backend pynput"
        )

    def _deprovision_resource(self) -> None:
        """Provide instructions for manual daemon teardown"""
        print("Please stop the daemon manually if you're done")

    def is_running(self) -> bool:
        """Assume the manually started daemon is running"""
        # We'll rely on the health check in the base class to verify
        return True
