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
import re

from commandLAB._utils.command import run_command
from commandLAB._utils.config import PROJ_DIR
from commandLAB._utils.network import find_free_port
from .base_provisioner import BaseComputerProvisioner, ProvisionerStatus
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
        port_range: Optional range of ports to try if daemon_port is not available.
                   NOTE: This parameter is only used for LOCAL Docker containers.
                   When running locally, port collisions can occur with existing containers
                   or other processes. The port_range allows the provisioner to find the
                   next available port within the specified range if the requested port
                   is unavailable. This is not needed for cloud provisioners where exact
                   ports can be specified during VM/container creation.
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
        port_range: Optional[Tuple[int, int]] = None,  # Only used for LOCAL platform to handle port collisions
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
            daemon_token=daemon_token,
            max_provisioning_retries=max_retries,
            timeout=timeout,
            max_health_retries=max_health_retries,
            health_check_timeout=health_check_timeout,
        )

        self.port_range = port_range
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
        self.container_id = None
        self._task_arn = None
        self.dockerfile_path = dockerfile_path

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

        Returns:
            str: The next available container name
        """
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

    def _provision_resource(self) -> None:
        """Provision the Docker container or cloud service based on the selected platform."""
        print(f"Provisioning container with platform {self.platform}")
        
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

    def _deprovision_resource(self) -> None:
        """Deprovision the Docker container or cloud service based on the selected platform."""
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

    def _setup_local(self):
        """Setup local Docker container"""
        print(f"Starting local Docker container")

        # Find an available port if needed for local setup
        # NOTE: This port handling logic is specific to LOCAL Docker containers.
        # When running locally, we need to handle port collisions that can occur with:
        # 1. Other running Docker containers
        # 2. System processes using the same ports
        # 3. Other commandLAB daemon instances
        # This is why we implement port scanning and fallback logic for local containers.
        # Cloud provisioners don't need this as they can specify exact ports during VM/container creation.
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
            # This is important for local development where ports might be used by other processes
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

        # If container_name is not provided, find the next available name for local setup
        if self.container_name is None:
            self.container_name = self._find_next_available_container_name()
            print(f"Using container name: {self.container_name}")

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

        # For cloud platforms, use fixed port 8000 if not specified
        if self.daemon_port is None:
            self.daemon_port = 8000
            print(f"Using default port {self.daemon_port} for AWS ECS")

        # Use simple naming for cloud platforms
        if self.container_name is None:
            self.container_name = f"{self.name_prefix}-ecs"
            print(f"Using container name: {self.container_name}")

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
            f"Starting Azure Container Instance in resource group {self.resource_group}"
        )

        # For cloud platforms, use fixed port 8000 if not specified
        if self.daemon_port is None:
            self.daemon_port = 8000
            print(
                f"Using default port {self.daemon_port} for Azure Container Instances"
            )

        # Use simple naming for cloud platforms
        if self.container_name is None:
            self.container_name = f"{self.name_prefix}-aci"
            print(f"Using container name: {self.container_name}")

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
        print(f"Starting GCP Cloud Run service in project {self.project_id}")

        # For cloud platforms, use fixed port 8000 if not specified
        if self.daemon_port is None:
            self.daemon_port = 8000
            print(f"Using default port {self.daemon_port} for GCP Cloud Run")

        # Use simple naming for cloud platforms
        if self.container_name is None:
            self.container_name = f"{self.name_prefix}-gcr"
            print(f"Using container name: {self.container_name}")

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
        return self._status.value
