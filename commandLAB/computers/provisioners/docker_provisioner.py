from enum import Enum
from pathlib import Path
import subprocess
import time
from typing import Optional, List, Tuple
import boto3
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.identity import DefaultAzureCredential
from google.cloud import container_v1
from google.cloud import run_v2
import threading
import logging
import requests
import re
from requests.exceptions import RequestException, ConnectionError, Timeout

from commandLAB._utils.command import run_command
from commandLAB._utils.config import PROJ_DIR
from commandLAB._utils.network import find_free_port
from .base_provisioner import BaseComputerProvisioner
from commandLAB.version import get_container_version, get_package_version


class DockerPlatform(str, Enum):
    LOCAL = "local"
    AWS_ECS = "aws_ecs"
    AZURE_CONTAINER_INSTANCES = "azure_container_instances"
    GCP_CLOUD_RUN = "gcp_cloud_run"


class DockerProvisioner(BaseComputerProvisioner):
    """Docker-based computer provisioner.

    This provisioner creates and manages Docker containers for running the commandLAB daemon.
    It supports both local Docker and cloud-based container services.

    Args:
        daemon_base_url: Base URL for the daemon service
        daemon_port: Port for the daemon service
        port_range: Optional range of ports to try if daemon_port is not available
        daemon_token: Optional authentication token for the daemon
        container_name: Optional name for the container. If not provided, a name will be generated
                       based on name_prefix
        name_prefix: Prefix to use when generating container names (default: "commandlab-daemon")
        platform: Container platform to use (LOCAL, AWS_ECS, AZURE_CONTAINER_INSTANCES, GCP_CLOUD_RUN)
        version: Container image version to use
        region: Cloud region for cloud platforms
        resource_group: Resource group for Azure
        project_id: Project ID for GCP
        subnets: List of subnet IDs for AWS
        security_groups: List of security group IDs for AWS
        subscription_id: Subscription ID for Azure
        max_retries: Maximum number of retries for setup operations
        timeout: Timeout in seconds for operations
        max_health_retries: Maximum number of retries for health checks
        health_check_timeout: Timeout in seconds for the daemon responsiveness check
        dockerfile_path: Path to the Dockerfile
    """

    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = None,
        port_range: Optional[Tuple[int, int]] = None,
        daemon_token: Optional[str] = None,
        container_name: Optional[str] = None,
        name_prefix: str = "commandlab-daemon",
        platform: DockerPlatform = DockerPlatform.LOCAL,
        version: Optional[str] = None,
        # Cloud-specific parameters
        region: str = None,
        resource_group: str = None,
        project_id: str = None,
        # Add these parameters
        subnets: List[str] = None,
        security_groups: List[str] = None,
        subscription_id: str = None,
        max_retries: int = 3,
        timeout: int = 900,  # 15 minutes
        max_health_retries: int = 3,
        health_check_timeout: int = 60,  # 1 minute
        dockerfile_path: Optional[str] = Path(__file__).parent.parent.parent.parent
        / "resources"
        / "docker"
        / "Dockerfile",
    ):
        # Initialize the base class with daemon URL and port
        super().__init__(
            daemon_base_url=daemon_base_url,
            daemon_port=daemon_port,
            port_range=port_range,
            daemon_token=daemon_token,
        )

        self.name_prefix = name_prefix
        self.container_name = container_name
        self.platform = platform
        self.version = version or get_container_version()
        self.region = region
        self.resource_group = resource_group
        self.project_id = project_id
        self.subnets = subnets or ["subnet-xxxxx"]
        self.security_groups = security_groups or ["sg-xxxxx"]
        self.subscription_id = subscription_id
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"
        self.container_id = None
        self._task_arn = None
        self.dockerfile_path = dockerfile_path
        self.max_health_retries = max_health_retries
        self.health_check_timeout = health_check_timeout

        # Initialize cloud clients if needed
        match platform:
            case DockerPlatform.AWS_ECS:
                if not self.region:
                    raise ValueError("Region must be specified for AWS ECS")
                self.ecs_client = boto3.client("ecs", region_name=region)
            case DockerPlatform.AZURE_CONTAINER_INSTANCES:
                if not self.subscription_id:
                    raise ValueError(
                        "Subscription ID must be specified for Azure Container Instances"
                    )
                self.aci_client = ContainerInstanceManagementClient(
                    credential=DefaultAzureCredential(),
                    subscription_id=self.subscription_id,
                )
            case DockerPlatform.GCP_CLOUD_RUN:
                if not self.project_id:
                    raise ValueError("Project ID must be specified for GCP Cloud Run")
                self.cloud_run_client = run_v2.ServicesClient()
            case _:
                pass

    def _find_next_available_container_name(self) -> str:
        """Find the next available container name with the given prefix.

        This method checks for existing containers with the prefix and finds the next
        available name by incrementing a numeric suffix. For example, if containers
        'commandlab-daemon' and 'commandlab-daemon-1' exist, it will return 'commandlab-daemon-2'.

        For non-local platforms (AWS, Azure, GCP), it simply returns the name_prefix as is.

        In case of errors when listing containers, it generates a name with a timestamp
        to avoid conflicts.

        Examples:
            >>> # Mock a provisioner with LOCAL platform
            >>> provisioner = DockerProvisioner(platform=DockerPlatform.LOCAL)
            >>> provisioner.name_prefix = "test-daemon"
            >>>
            >>> # Case 1: No containers exist with the prefix
            >>> # Mock the subprocess.run to return empty list
            >>> def mock_run_empty(*args, **kwargs):
            ...     class Result:
            ...         stdout = ""
            ...         stderr = ""
            ...     return Result()
            >>>
            >>> # Patch subprocess.run temporarily
            >>> import subprocess
            >>> original_run = subprocess.run
            >>> subprocess.run = mock_run_empty
            >>>
            >>> # Should return the base name
            >>> provisioner._find_next_available_container_name()
            'test-daemon'
            >>>
            >>> # Case 2: Base name is taken, but no numbered suffixes
            >>> def mock_run_base_taken(*args, **kwargs):
            ...     class Result:
            ...         stdout = "test-daemon\\n"
            ...         stderr = ""
            ...     return Result()
            >>>
            >>> subprocess.run = mock_run_base_taken
            >>> provisioner._find_next_available_container_name()
            'test-daemon-1'
            >>>
            >>> # Case 3: Base name and -1 are taken
            >>> def mock_run_1_taken(*args, **kwargs):
            ...     class Result:
            ...         stdout = "test-daemon\\ntest-daemon-1\\n"
            ...         stderr = ""
            ...     return Result()
            >>>
            >>> subprocess.run = mock_run_1_taken
            >>> provisioner._find_next_available_container_name()
            'test-daemon-2'
            >>>
            >>> # Case 4: Base name, -1, and -3 are taken (should return -2)
            >>> def mock_run_gap(*args, **kwargs):
            ...     class Result:
            ...         stdout = "test-daemon\\ntest-daemon-1\\ntest-daemon-3\\n"
            ...         stderr = ""
            ...     return Result()
            >>>
            >>> subprocess.run = mock_run_gap
            >>> provisioner._find_next_available_container_name()
            'test-daemon-2'
            >>>
            >>> # Case 5: Base name, -1, -2, -3 are taken
            >>> def mock_run_sequential(*args, **kwargs):
            ...     class Result:
            ...         stdout = "test-daemon\\ntest-daemon-1\\ntest-daemon-2\\ntest-daemon-3\\n"
            ...         stderr = ""
            ...     return Result()
            >>>
            >>> subprocess.run = mock_run_sequential
            >>> provisioner._find_next_available_container_name()
            'test-daemon-4'
            >>>
            >>> # Case 6: Non-local platform
            >>> provisioner.platform = DockerPlatform.AWS_ECS
            >>> provisioner._find_next_available_container_name()
            'test-daemon'
            >>>
            >>> # Restore original subprocess.run
            >>> subprocess.run = original_run

        Returns:
            str: The next available container name
        """
        if self.platform != DockerPlatform.LOCAL:
            # For non-local platforms, just use the prefix as the name
            return self.name_prefix

        try:
            # List all containers (including stopped ones)
            list_cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
            result = subprocess.run(
                list_cmd, capture_output=True, text=True, check=True
            )

            # Get all container names
            container_names = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )

            # Filter names that match our prefix pattern
            prefix_pattern = f"^{re.escape(self.name_prefix)}(-\\d+)?$"
            matching_names = [
                name for name in container_names if re.match(prefix_pattern, name)
            ]

            if not matching_names:
                # No matching containers found, use the prefix as is
                return self.name_prefix

            # Check if the base name is available
            if self.name_prefix not in matching_names:
                return self.name_prefix

            # Find all used suffix numbers
            used_suffixes = set()
            for name in matching_names:
                # Extract the suffix number if it exists
                suffix_match = re.search(
                    f"^{re.escape(self.name_prefix)}-(\\d+)$", name
                )
                if suffix_match:
                    suffix_num = int(suffix_match.group(1))
                    used_suffixes.add(suffix_num)

            # Find the first available suffix number
            suffix = 1
            while suffix in used_suffixes:
                suffix += 1

            return f"{self.name_prefix}-{suffix}"

        except subprocess.CalledProcessError as e:
            print(f"Error listing Docker containers: {e}")
            # In case of error, generate a name with a timestamp to avoid conflicts
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            return f"{self.name_prefix}-{timestamp}"

    def setup(self) -> None:
        print(f"Setting up container with platform {self.platform}")
        self._status = "starting"
        print(f"Status set to: {self._status}")
        retry_count = 0

        # Find an available port if needed
        if self.daemon_port is None:
            # No port specified, find one in the given range or any available port
            original_port_range = self.port_range
            try:
                self.daemon_port = find_free_port(port_range=self.port_range)
                print(
                    f"Selected port {self.daemon_port} for daemon service"
                    + (
                        f" from range {original_port_range}"
                        if original_port_range
                        else ""
                    )
                )
            except RuntimeError as e:
                # Handle the case where no ports are available in the specified range
                print(f"Warning: {str(e)}. Trying to find any available port.")
                self.daemon_port = find_free_port()
                print(f"Selected port {self.daemon_port} outside of requested range")
        elif not find_free_port(preferred_port=self.daemon_port):
            # Specified port is not available, find an alternative
            print(f"Requested port {self.daemon_port} is not available")
            original_port = self.daemon_port
            try:
                self.daemon_port = find_free_port(port_range=self.port_range)
                print(
                    f"Using alternative port {self.daemon_port} instead of {original_port}"
                )
            except RuntimeError as e:
                # Handle the case where no ports are available in the specified range
                print(f"Warning: {str(e)}. Trying to find any available port.")
                self.daemon_port = find_free_port()
                print(f"Selected port {self.daemon_port} outside of requested range")
        else:
            # Specified port is available, use it
            print(f"Using requested port {self.daemon_port} for daemon service")

        # If container_name is not provided, find the next available name
        if self.container_name is None:
            self.container_name = self._find_next_available_container_name()
            print(f"Using container name: {self.container_name}")

        while retry_count < self.max_retries:
            print(f"Attempt {retry_count + 1}/{self.max_retries} to setup container")
            try:
                match self.platform:
                    case DockerPlatform.LOCAL:
                        print("Using LOCAL platform setup")
                        self._setup_local()
                    case DockerPlatform.AWS_ECS:
                        print("Using AWS ECS platform setup")
                        self._setup_aws_ecs()
                    case DockerPlatform.AZURE_CONTAINER_INSTANCES:
                        print("Using Azure Container Instances platform setup")
                        self._setup_azure_container_instances()
                    case DockerPlatform.GCP_CLOUD_RUN:
                        print("Using GCP Cloud Run platform setup")
                        self._setup_gcp_cloud_run()
                    case _:
                        raise ValueError(f"Unsupported platform: {self.platform}")

                # Wait for the container to be running and the daemon to be responsive
                print(
                    f"Waiting for container and daemon to be running (container timeout: {self.timeout}s, daemon timeout: {self.health_check_timeout}s)"
                )
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    # Use the combined check which has its own internal timeouts
                    if self.is_running_and_responsive():
                        self._status = "running"
                        print(
                            f"Container and daemon are now running after {int(time.time() - start_time)}s"
                        )
                        return
                    print(
                        "Waiting for container to be running and daemon to be responsive, checking again in 5s"
                    )
                    time.sleep(5)

                # If we get here, the container didn't start in time or the daemon isn't responsive
                self._status = "error"
                elapsed = int(time.time() - start_time)
                print(
                    f"Timeout waiting for container and daemon to start after {elapsed}s"
                )
                raise TimeoutError(
                    f"Timeout waiting for container and daemon to start after {elapsed}s"
                )

            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    print(
                        f"Failed to setup container after {self.max_retries} attempts: {str(e)}"
                    )
                    raise
                backoff = 2**retry_count
                print(
                    f"Error setting up container, retrying in {backoff}s ({retry_count}/{self.max_retries}): {str(e)}"
                )
                time.sleep(backoff)  # Exponential backoff

    def _setup_local(self):
        """Setup local Docker container"""
        print(f"Starting local Docker container {self.container_name}")

        # Run the container using Docker CLI with output streaming in a separate thread
        run_cmd = [
            "docker",
            "run",
            "-it",
            "-d",  # detached mode
            "--name",
            self.container_name,  # Add container name
            "-p",
            f"{self.daemon_port}:{self.daemon_port}",
            "-e",
            f"DAEMON_PORT={self.daemon_port}",
        ]

        # Add token if it exists
        if hasattr(self, "daemon_token") and self.daemon_token:
            run_cmd.extend(["-e", f"DAEMON_TOKEN={self.daemon_token}"])

        # Add the image name
        run_cmd.append(f"commandlab-daemon:{self.version}")

        print(f"Running command: {' '.join(run_cmd)}")

        # Create a function to run in a separate thread
        def run_docker_container():
            process = subprocess.Popen(
                run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True,
            )

            # Store the process so it can be accessed during teardown
            self._docker_process = process

            # Stream the output
            for line in iter(process.stdout.readline, ""):
                line = line.strip()
                if line:
                    print(f"Docker run: {line}")

            # Wait for process to complete and check return code
            return_code = process.wait()
            if return_code != 0:
                print(f"Docker process exited with code {return_code}")

        # Start the docker container in a separate thread
        self._docker_thread = threading.Thread(target=run_docker_container, daemon=True)
        self._docker_thread.start()

        print("Docker container started in background")

        time.sleep(10)

    def _setup_aws_ecs(self):
        """Setup AWS ECS container"""
        print(f"Starting AWS ECS task in region {self.region}")

        response = self.ecs_client.run_task(
            cluster="commandlab-cluster",
            taskDefinition="commandlab-daemon",
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": self.subnets,
                    "securityGroups": self.security_groups,
                    "assignPublicIp": "ENABLED",
                }
            },
            overrides={
                "containerOverrides": [
                    {
                        "name": "commandlab-daemon",
                        "image": f"commandlab-daemon:{self.version}",
                    }
                ]
            },
        )
        self._task_arn = response["tasks"][0]["taskArn"]
        print(f"Started ECS task with ARN: {self._task_arn}")

    def _setup_azure_container_instances(self):
        """Setup Azure Container Instances"""
        print(
            f"Starting Azure Container Instance {self.container_name} in resource group {self.resource_group}"
        )

        container_group = {
            "location": self.region,
            "containers": [
                {
                    "name": self.container_name,
                    "image": f"commandlab-daemon:{self.version}",
                    "ports": [{"port": self.daemon_port}],
                    "resources": {"requests": {"memoryInGB": 1.5, "cpu": 1.0}},
                }
            ],
            "osType": "Linux",
            "ipAddress": {
                "type": "Public",
                "ports": [{"protocol": "TCP", "port": self.daemon_port}],
            },
        }

        poller = self.aci_client.container_groups.begin_create_or_update(
            self.resource_group, self.container_name, container_group
        )

        # Wait for the operation to complete with timeout
        start_time = time.time()
        while not poller.done() and time.time() - start_time < self.timeout:
            time.sleep(5)

        if not poller.done():
            raise TimeoutError(f"Timeout waiting for Azure Container Instance creation")

        result = poller.result()
        print(f"Started Azure Container Instance: {result.name}")

    def _setup_gcp_cloud_run(self):
        """Setup GCP Cloud Run container"""
        print(
            f"Starting GCP Cloud Run service {self.container_name} in project {self.project_id}"
        )

        service = {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {"name": self.container_name},
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "image": f"commandlab-daemon:{self.version}",
                                "ports": [{"containerPort": self.daemon_port}],
                            }
                        ]
                    }
                }
            },
        }

        parent = f"projects/{self.project_id}/locations/{self.region}"
        operation = self.cloud_run_client.create_service(parent=parent, service=service)

        # Wait for the operation to complete
        print(f"Waiting for Cloud Run service creation to complete")
        start_time = time.time()
        while not operation.done() and time.time() - start_time < self.timeout:
            time.sleep(5)

        if not operation.done():
            raise TimeoutError(f"Timeout waiting for Cloud Run service creation")

        result = operation.result()
        print(f"Started Cloud Run service: {result.name}")

    def teardown(self) -> None:
        self._status = "stopping"

        try:
            match self.platform:
                case DockerPlatform.LOCAL:
                    self._teardown_local()
                case DockerPlatform.AWS_ECS:
                    self._teardown_aws_ecs()
                case DockerPlatform.AZURE_CONTAINER_INSTANCES:
                    self._teardown_azure_container_instances()
                case DockerPlatform.GCP_CLOUD_RUN:
                    self._teardown_gcp_cloud_run()
                case _:
                    raise ValueError(f"Unsupported platform: {self.platform}")

            self._status = "stopped"
        except Exception as e:
            self._status = "error"
            print(f"Error during teardown: {e}")

    def _teardown_local(self):
        """Teardown local Docker container"""
        print(f"Stopping Docker container {self.container_name}")

        try:
            # Stop the container
            stop_cmd = ["docker", "stop", self.container_name]
            print(f"Running command: {' '.join(stop_cmd)}")
            subprocess.run(stop_cmd, check=True, capture_output=True, text=True)

            # Remove the container
            rm_cmd = ["docker", "rm", self.container_name]
            print(f"Running command: {' '.join(rm_cmd)}")
            subprocess.run(rm_cmd, check=True, capture_output=True, text=True)

            print(
                f"Docker container {self.container_name} stopped and removed successfully"
            )
        except subprocess.CalledProcessError as e:
            print(f"Error stopping/removing Docker container: {e}")
            print(f"Error output: {e.stderr}")
            # Don't raise here to allow cleanup to continue even if there are errors

    def _teardown_aws_ecs(self):
        """Teardown AWS ECS task"""
        if self._task_arn:
            print(f"Stopping ECS task {self._task_arn}")
            try:
                self.ecs_client.stop_task(
                    cluster="commandlab-cluster", task=self._task_arn
                )

                # Wait for the task to stop
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    try:
                        response = self.ecs_client.describe_tasks(
                            cluster="commandlab-cluster", tasks=[self._task_arn]
                        )
                        if not response["tasks"]:
                            break
                        status = response["tasks"][0]["lastStatus"]
                        if status == "STOPPED":
                            print(f"ECS task {self._task_arn} stopped successfully")
                            break
                        print(f"ECS task status: {status}")
                        time.sleep(5)
                    except Exception as e:
                        print(f"Task {self._task_arn} no longer exists: {e}")
                        break
            except Exception as e:
                print(f"Error stopping ECS task: {e}")

    def _teardown_azure_container_instances(self):
        """Teardown Azure Container Instance"""
        print(f"Deleting Azure Container Instance {self.container_name}")
        try:
            poller = self.aci_client.container_groups.begin_delete(
                self.resource_group, self.container_name
            )

            # Wait for the operation to complete with timeout
            start_time = time.time()
            while not poller.done() and time.time() - start_time < self.timeout:
                time.sleep(5)

            if poller.done():
                print(
                    f"Azure Container Instance {self.container_name} deleted successfully"
                )
            else:
                print(f"Timeout waiting for Azure Container Instance deletion")
        except Exception as e:
            print(f"Error deleting Azure Container Instance: {e}")

    def _teardown_gcp_cloud_run(self):
        """Teardown GCP Cloud Run service"""
        print(f"Deleting Cloud Run service {self.container_name}")
        try:
            name = f"projects/{self.project_id}/locations/{self.region}/services/{self.container_name}"
            operation = self.cloud_run_client.delete_service(name=name)

            # Wait for the operation to complete
            start_time = time.time()
            while not operation.done() and time.time() - start_time < self.timeout:
                time.sleep(5)

            if operation.done():
                print(f"Cloud Run service {self.container_name} deleted successfully")
            else:
                print(f"Timeout waiting for Cloud Run service deletion")
        except Exception as e:
            print(f"Error deleting Cloud Run service: {e}")

    def is_running(self) -> bool:
        """
        Check if the container is running at the platform level.

        This method only checks if the container/service is running on the selected platform
        (Docker, AWS ECS, Azure Container Instances, or GCP Cloud Run) without checking
        if the daemon inside the container is responsive.

        Returns:
            bool: True if the container is running, False otherwise
        """
        try:
            # Check if the container/service is running at the platform level
            match self.platform:
                case DockerPlatform.LOCAL:
                    return self._is_local_running()
                case DockerPlatform.AWS_ECS:
                    return self._is_aws_ecs_running()
                case DockerPlatform.AZURE_CONTAINER_INSTANCES:
                    return self._is_azure_container_instances_running()
                case DockerPlatform.GCP_CLOUD_RUN:
                    return self._is_gcp_cloud_run_running()
                case _:
                    return False

        except Exception as e:
            print(f"Error checking if container is running: {e}")
            return False

    def is_daemon_responsive(self) -> bool:
        """
        Check if the daemon API inside the container is responsive.

        This method performs a health check to the daemon API to verify that
        the service inside the container is up and running.

        Returns:
            bool: True if the daemon is responsive, False otherwise
        """
        try:
            # Make a health check request to the daemon API
            health_url = f"{self.daemon_base_url}:{self.daemon_port}/health"
            print(f"Performing health check to {health_url}")

            # Add retry logic for health check to handle temporary failures
            health_retry_delay = 2  # seconds
            start_time = time.time()

            for retry in range(self.max_health_retries):
                # Check if we've exceeded the health check timeout
                if time.time() - start_time > self.health_check_timeout:
                    print(
                        f"Health check timed out after {int(time.time() - start_time)}s"
                    )
                    return False

                try:
                    response = requests.get(health_url, timeout=5)
                    if response.status_code == 200 and response.json().get(
                        "healthy", False
                    ):
                        print(f"Health check successful: daemon is responsive")
                        return True
                    else:
                        print(
                            f"Health check attempt {retry+1}/{self.max_health_retries} failed: daemon returned status {response.status_code}"
                        )
                        if retry < self.max_health_retries - 1:
                            print(f"Retrying in {health_retry_delay} seconds...")
                            time.sleep(health_retry_delay)
                            # Increase delay for next retry (exponential backoff)
                            health_retry_delay *= 2
                except (ConnectionError, Timeout) as e:
                    print(
                        f"Health check attempt {retry+1}/{self.max_health_retries} failed: could not connect to daemon: {e}"
                    )
                    if retry < self.max_health_retries - 1:
                        print(f"Retrying in {health_retry_delay} seconds...")
                        time.sleep(health_retry_delay)
                        # Increase delay for next retry (exponential backoff)
                        health_retry_delay *= 2
                except RequestException as e:
                    print(
                        f"Health check attempt {retry+1}/{self.max_health_retries} failed: request error: {e}"
                    )
                    if retry < self.max_health_retries - 1:
                        print(f"Retrying in {health_retry_delay} seconds...")
                        time.sleep(health_retry_delay)
                        # Increase delay for next retry (exponential backoff)
                        health_retry_delay *= 2
                except Exception as e:
                    print(
                        f"Health check attempt {retry+1}/{self.max_health_retries} failed: unexpected error: {e}"
                    )
                    if retry < self.max_health_retries - 1:
                        print(f"Retrying in {health_retry_delay} seconds...")
                        time.sleep(health_retry_delay)
                        # Increase delay for next retry (exponential backoff)
                        health_retry_delay *= 2

            # If we get here, all retries failed
            print(f"All health check attempts failed. Daemon is not responsive.")
            return False

        except Exception as e:
            print(f"Error checking if daemon is responsive: {e}")
            return False

    def is_running_and_responsive(self) -> bool:
        """
        Check if the container is running and the daemon is responsive.

        This method combines the checks from is_running() and is_daemon_responsive()
        to verify that both the container is running at the platform level and
        the daemon inside the container is responsive.

        The two checks are independent and have their own timeout and retry mechanisms:
        - Container running check: Uses the main timeout and max_retries parameters
        - Daemon responsiveness check: Uses health_check_timeout and max_health_retries parameters

        Returns:
            bool: True if the container is running and the daemon is responsive, False otherwise
        """
        # First check if the container is running at the platform level
        print("Checking if container is running at the platform level...")
        container_running = self.is_running()
        if not container_running:
            print("Container is not running at the platform level")
            return False

        # Then check if the daemon is responsive
        print("Container is running. Now checking if daemon is responsive...")
        daemon_responsive = self.is_daemon_responsive()
        if not daemon_responsive:
            print("Container is running but daemon is not responsive")
            return False

        print("Container is running and daemon is responsive")
        return True

    def _is_local_running(self) -> bool:
        """Check if local Docker container is running"""
        try:
            # Use Docker CLI to check container status
            inspect_cmd = [
                "docker",
                "inspect",
                "-f",
                '"{{.State.Running}}"',
                self.container_name,
            ]

            result = subprocess.run(
                inspect_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,  # Add a timeout to prevent hanging
            )

            is_running = result.stdout.strip().strip("\"'").lower() == "true"
            print(
                f"Docker container {self.container_name} running status: {is_running}"
            )
            return is_running
        except subprocess.CalledProcessError as e:
            # This likely means the container doesn't exist
            print(f"Error checking Docker container status: {e}")
            if "No such object" in e.stderr:
                print(f"Docker container {self.container_name} not found")
            return False
        except subprocess.TimeoutExpired:
            print(f"Timeout while checking Docker container status")
            return False

    def _is_aws_ecs_running(self) -> bool:
        """Check if AWS ECS task is running"""
        try:
            if not self._task_arn:
                return False

            response = self.ecs_client.describe_tasks(
                cluster="commandlab-cluster", tasks=[self._task_arn]
            )

            if not response["tasks"]:
                return False

            status = response["tasks"][0]["lastStatus"]
            is_running = status == "RUNNING"
            print(f"ECS task {self._task_arn} status: {status}")
            return is_running
        except Exception as e:
            print(f"Error checking ECS task status: {e}")
            return False

    def _is_azure_container_instances_running(self) -> bool:
        """Check if Azure Container Instance is running"""
        try:
            container_group = self.aci_client.container_groups.get(
                self.resource_group, self.container_name
            )
            is_running = (
                container_group.containers[0].instance_view.current_state.state
                == "Running"
            )
            print(
                f"Azure Container Instance {self.container_name} running status: {is_running}"
            )
            return is_running
        except Exception as e:
            print(f"Error checking Azure Container Instance status: {e}")
            return False

    def _is_gcp_cloud_run_running(self) -> bool:
        """Check if GCP Cloud Run service is running"""
        try:
            name = f"projects/{self.project_id}/locations/{self.region}/services/{self.container_name}"
            service = self.cloud_run_client.get_service(name=name)
            is_running = service.status.conditions[0].status == True
            print(
                f"Cloud Run service {self.container_name} running status: {is_running}"
            )
            return is_running
        except Exception as e:
            print(f"Error checking Cloud Run service status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status
