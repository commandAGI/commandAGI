from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
import secrets
import time
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout


class ProvisionerStatus(str, Enum):
    """Status states for provisioners."""

    NOT_STARTED = "not_started"
    PROVISIONING = "provisioning"
    STARTING = "starting"
    HEALTH_CHECKING = "health_checking"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SETUP_ERROR = "setup_error"
    HEALTH_CHECK_ERROR = "health_check_error"
    TEARDOWN_ERROR = "teardown_error"


class BaseComputerProvisioner(ABC):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = None,
        daemon_token: Optional[str] = None,
        max_provisioning_retries: int = 3,
        timeout: int = 900,  # 15 minutes
        max_health_retries: int = 10,
        health_check_timeout: int = 60,  # 1 minute
    ):
        """Initialize the base provisioner.

        Args:
            daemon_base_url: Base URL for the daemon service
            daemon_port: Port for the daemon service (default: 8000 if None)
            daemon_token: Authentication token for the daemon service. If None, a random token will be generated.
            max_provisioning_retries: Maximum number of retries for setup operations
            timeout: Timeout in seconds for operations
            max_health_retries: Maximum number of retries for health checks
            health_check_timeout: Timeout in seconds for the daemon responsiveness check
        """
        self.daemon_base_url = daemon_base_url
        self.daemon_port = daemon_port if daemon_port is not None else 8000
        self.daemon_token = daemon_token or secrets.token_urlsafe(32)
        self.max_provisioning_retries = max_provisioning_retries
        self.timeout = timeout
        self.max_health_retries = max_health_retries
        self.health_check_timeout = health_check_timeout
        self._status = ProvisionerStatus.NOT_STARTED

    def _set_status(self, status: ProvisionerStatus) -> None:
        """Set the provisioner status with logging.

        Args:
            status: The new status to set
        """
        old_status = self._status
        self._status = status
        print(f"Status changed: {old_status} -> {status}")

    def setup(self) -> None:
        """Setup the daemon with the specific provisioning method.

        This method implements the common setup flow with retries and health checks,
        while delegating the platform-specific provisioning to _provision_resource.
        """
        print(f"Setting up resource")
        self._set_status(ProvisionerStatus.STARTING)
        provision_attempt = 0

        # First loop: Provisioning with retries
        while provision_attempt < self.max_provisioning_retries:
            print(
                f"Attempt {provision_attempt + 1}/{self.max_provisioning_retries} to setup resource"
            )
            try:
                self._set_status(ProvisionerStatus.PROVISIONING)
                self._provision_resource()

                # If we get here, provisioning was successful
                break

            except Exception as e:
                provision_attempt += 1
                if provision_attempt >= self.max_provisioning_retries:
                    self._set_status(ProvisionerStatus.SETUP_ERROR)
                    print(
                        f"Failed to setup resource after {
                            self.max_provisioning_retries} attempts: {
                            str(e)}"
                    )
                    raise
                backoff_seconds = 2**provision_attempt
                print(
                    f"Error setting up resource, retrying in {backoff_seconds}s ({provision_attempt}/{
                        self.max_provisioning_retries}): {
                        str(e)}"
                )
                time.sleep(backoff_seconds)  # Exponential backoff

        # Second loop: Health checking with its own timeout and retry count
        self._set_status(ProvisionerStatus.HEALTH_CHECKING)
        print(
            f"Waiting for resource and daemon to be running (timeout: {
                self.health_check_timeout}s)"
        )

        health_check_attempt = 0
        health_check_start_time = time.time()

        while health_check_attempt < self.max_health_retries:
            try:
                # First check if the resource is running
                print("Checking if resource is running at the platform level...")
                resource_running = self.is_running()
                if not resource_running:
                    raise RuntimeError("Resource is not running at the platform level")

                # Then check if the daemon is responsive
                print("Resource is running. Now checking if daemon is responsive...")
                daemon_responsive = self.is_daemon_responsive()
                if not daemon_responsive:
                    raise RuntimeError(
                        "Resource is running but daemon is not responsive"
                    )

                # Both checks passed
                print("Resource is running and daemon is responsive")
                self._set_status(ProvisionerStatus.RUNNING)
                print(
                    f"Resource and daemon are now running after {
                        int(
                            time.time() -
                            health_check_start_time)}s"
                )
                return

            except Exception as e:
                health_check_attempt += 1
                elapsed_seconds = int(time.time() - health_check_start_time)

                # Check if we've exceeded the timeout
                if elapsed_seconds > self.health_check_timeout:
                    self._set_status(ProvisionerStatus.HEALTH_CHECK_ERROR)
                    print(
                        f"Timeout waiting for resource and daemon to start after {elapsed_seconds}s"
                    )
                    raise TimeoutError(
                        f"Timeout waiting for resource and daemon to start after {elapsed_seconds}s"
                    )

                # Check if we've exceeded max retries
                if health_check_attempt >= self.max_health_retries:
                    self._set_status(ProvisionerStatus.HEALTH_CHECK_ERROR)
                    print(
                        f"Failed health check after {
                            self.max_health_retries} attempts: {
                            str(e)}"
                    )
                    raise RuntimeError(
                        f"Failed health check after {
                            self.max_health_retries} attempts: {
                            str(e)}"
                    )

                # Wait before retrying
                retry_wait_seconds = min(
                    5, self.health_check_timeout - elapsed_seconds
                )  # Don't wait longer than remaining timeout
                if retry_wait_seconds > 0:
                    print(
                        f"Health check failed ({health_check_attempt}/{
                            self.max_health_retries}): {
                            str(e)}. Retrying in {retry_wait_seconds}s"
                    )
                    time.sleep(retry_wait_seconds)

    @abstractmethod
    def _provision_resource(self) -> None:
        """Provision the specific resource (container, VM, etc.)

        This method should be implemented by subclasses to handle the platform-specific
        provisioning logic.
        """
        pass

    def teardown(self) -> None:
        """Cleanup any resources created during setup.

        This method implements the common teardown flow, while delegating
        the platform-specific cleanup to _deprovision_resource.
        """
        self._set_status(ProvisionerStatus.STOPPING)

        try:
            self._deprovision_resource()
            self._set_status(ProvisionerStatus.STOPPED)
        except Exception as e:
            self._set_status(ProvisionerStatus.TEARDOWN_ERROR)
            print(f"Error during teardown: {e}")

    @abstractmethod
    def _deprovision_resource(self) -> None:
        """Deprovision the specific resource (container, VM, etc.)

        This method should be implemented by subclasses to handle the platform-specific
        deprovisioning logic.
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if the resource is running at the platform level.

        This method should only check if the resource is running on the selected platform
        without checking if the daemon inside the resource is responsive.

        Returns:
            bool: True if the resource is running, False otherwise
        """
        pass

    def is_daemon_responsive(self) -> bool:
        """
        Check if the daemon API inside the resource is responsive.

        This method performs a health check to the daemon API to verify that
        the service inside the resource is up and running.

        Returns:
            bool: True if the daemon is responsive, False otherwise
        """
        try:
            # Make a health check request to the daemon API
            health_url = f"{self.daemon_base_url}:{self.daemon_port}/health"
            print(f"Performing health check to {health_url}")

            # Single attempt health check
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200 and response.json().get(
                    "healthy", False
                ):
                    print(f"Health check successful: daemon is responsive")
                    return True
                else:
                    print(
                        f"Health check failed: daemon returned status {
                            response.status_code}"
                    )
                    return False
            except (ConnectionError, Timeout) as e:
                print(f"Health check failed: could not connect to daemon: {e}")
                return False
            except RequestException as e:
                print(f"Health check failed: request error: {e}")
                return False
            except Exception as e:
                print(f"Health check failed: unexpected error: {e}")
                return False

        except Exception as e:
            print(f"Error checking if daemon is responsive: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status.value

    @property
    def daemon_url(self) -> str:
        """Get the full daemon URL including base URL and port."""
        return f"{self.daemon_base_url}:{self.daemon_port}"
