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
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = 8000,
        port_range: Optional[Tuple[int, int]] = None,
        container_name: str = "commandlab-daemon",
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
        dockerfile_path: Optional[str] = Path(__file__).parent.parent.parent.parent / "resources" / "docker" / "Dockerfile",
    ):
        # Initialize the base class with daemon URL and port
        super().__init__(
            daemon_base_url=daemon_base_url,
            daemon_port=daemon_port,
            port_range=port_range
        )
            
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

    def setup(self) -> None:
        print(f"Setting up container with platform {self.platform}")
        self._status = "starting"
        print(f"Status set to: {self._status}")
        retry_count = 0
        
        # Find an available port if needed
        if self.daemon_port is None or not find_free_port(preferred_port=self.daemon_port):
            self.daemon_port = find_free_port(port_range=self.port_range)
            print(f"Using port {self.daemon_port} for daemon service")

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

                # Wait for the container to be running
                print(f"Waiting for container to be running (timeout: {self.timeout}s)")
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        print(f"Container is now running after {int(time.time() - start_time)}s")
                        return
                    print("Container not yet running, checking again in 5s")
                    time.sleep(5)

                # If we get here, the container didn't start in time
                self._status = "error"
                elapsed = int(time.time() - start_time)
                print(f"Timeout waiting for container to start after {elapsed}s")
                raise TimeoutError(f"Timeout waiting for container to start after {elapsed}s")

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
            "--name", self.container_name,  # Add container name
            "-p",
            f"{self.daemon_port}:{self.daemon_port}",
            "-e", f"DAEMON_PORT={self.daemon_port}",
        ]
        
        # Add token if it exists
        if hasattr(self, 'daemon_token') and self.daemon_token:
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
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                universal_newlines=True
            )

            # Store the process so it can be accessed during teardown
            self._docker_process = process

            # Stream the output
            for line in iter(process.stdout.readline, ''):
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
            
            print(f"Docker container {self.container_name} stopped and removed successfully")
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
                            print(
                                f"ECS task {self._task_arn} stopped successfully"
                            )
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
                print(
                    f"Cloud Run service {self.container_name} deleted successfully"
                )
            else:
                print(f"Timeout waiting for Cloud Run service deletion")
        except Exception as e:
            print(f"Error deleting Cloud Run service: {e}")

    def is_running(self) -> bool:
        try:
            if self.platform == DockerPlatform.LOCAL:
                return self._is_local_running()
            elif self.platform == DockerPlatform.AWS_ECS:
                return self._is_aws_ecs_running()
            elif self.platform == DockerPlatform.AZURE_CONTAINER_INSTANCES:
                return self._is_azure_container_instances_running()
            elif self.platform == DockerPlatform.GCP_CLOUD_RUN:
                return self._is_gcp_cloud_run_running()
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
                "{{.State.Running}}",
                self.container_name
            ]
            
            result = subprocess.run(
                inspect_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            is_running = result.stdout.strip() == "true"
            print(f"Docker container {self.container_name} running status: {is_running}")
            return is_running
        except subprocess.CalledProcessError as e:
            # This likely means the container doesn't exist
            print(f"Error checking Docker container status: {e}")
            if "No such object" in e.stderr:
                print(f"Docker container {self.container_name} not found")
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
