from enum import Enum
import subprocess
from typing import Optional
import boto3
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.identity import DefaultAzureCredential
from google.cloud import container_v1
from .base_provisioner import BaseComputerProvisioner
from commandLAB.version import get_container_version


class DockerPlatform(str, Enum):
    LOCAL = "local"
    AWS_ECS = "aws_ecs"
    AZURE_CONTAINER_INSTANCES = "azure_container_instances"
    GCP_CLOUD_RUN = "gcp_cloud_run"


class DockerProvisioner(BaseComputerProvisioner):
    def __init__(
        self, 
        port: int = 8000, 
        container_name: str = "commandlab-daemon",
        platform: DockerPlatform = DockerPlatform.LOCAL,
        version: Optional[str] = None,
        # Cloud-specific parameters
        region: str = None,
        resource_group: str = None,
        project_id: str = None
    ):
        super().__init__(port)
        self.container_name = container_name
        self.platform = platform
        self.version = version or get_container_version()
        self.region = region
        self.resource_group = resource_group
        self.project_id = project_id
        
        # Initialize cloud clients if needed
        if platform == DockerPlatform.AWS_ECS:
            self.ecs_client = boto3.client('ecs', region_name=region)
        elif platform == DockerPlatform.AZURE_CONTAINER_INSTANCES:
            self.aci_client = ContainerInstanceManagementClient(
                credential=DefaultAzureCredential(),
                subscription_id="your-subscription-id"
            )
        elif platform == DockerPlatform.GCP_CLOUD_RUN:
            self.cloud_run_client = container_v1.CloudRunClient()

    def setup(self) -> None:
        if self.platform == DockerPlatform.LOCAL:
            self._setup_local()
        elif self.platform == DockerPlatform.AWS_ECS:
            self._setup_aws_ecs()
        elif self.platform == DockerPlatform.AZURE_CONTAINER_INSTANCES:
            self._setup_azure_container_instances()
        elif self.platform == DockerPlatform.GCP_CLOUD_RUN:
            self._setup_gcp_cloud_run()

    def _setup_local(self):
        """Setup local Docker container"""
        cmd = [
            "docker", "run",
            "-d",  # detached mode
            "--name", self.container_name,
            "-p", f"{self.port}:{self.port}",
            f"commandlab-daemon:{self.version}",
            "--port", str(self.port),
            "--backend", "pynput"
        ]
        subprocess.run(cmd, check=True)

    def _setup_aws_ecs(self):
        """Setup AWS ECS container"""
        response = self.ecs_client.run_task(
            cluster="commandlab-cluster",
            taskDefinition="commandlab-daemon",
            launchType="FARGATE",
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': ['subnet-xxxxx'],
                    'securityGroups': ['sg-xxxxx'],
                    'assignPublicIp': 'ENABLED'
                }
            },
            overrides={
                'containerOverrides': [{
                    'name': 'commandlab-daemon',
                    'image': f'commandlab-daemon:{self.version}'
                }]
            }
        )
        self.task_arn = response['tasks'][0]['taskArn']

    def _setup_azure_container_instances(self):
        """Setup Azure Container Instances"""
        container_group = {
            'location': self.region,
            'containers': [{
                'name': self.container_name,
                'image': f'commandlab-daemon:{self.version}',
                'ports': [{'port': self.port}],
                'resources': {
                    'requests': {
                        'memoryInGB': 1.5,
                        'cpu': 1.0
                    }
                }
            }],
            'osType': 'Linux',
            'ipAddress': {
                'type': 'Public',
                'ports': [{'protocol': 'TCP', 'port': self.port}]
            }
        }
        
        self.aci_client.container_groups.begin_create_or_update(
            self.resource_group,
            self.container_name,
            container_group
        ).result()

    def _setup_gcp_cloud_run(self):
        """Setup GCP Cloud Run container"""
        service = {
            'apiVersion': 'serving.knative.dev/v1',
            'kind': 'Service',
            'metadata': {'name': self.container_name},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{
                            'image': f'commandlab-daemon:{self.version}',
                            'ports': [{'containerPort': self.port}],
                        }]
                    }
                }
            }
        }
        
        parent = f"projects/{self.project_id}/locations/{self.region}"
        self.cloud_run_client.create_service(parent=parent, service=service)

    def teardown(self) -> None:
        if self.platform == DockerPlatform.LOCAL:
            subprocess.run(["docker", "stop", self.container_name], check=True)
            subprocess.run(["docker", "rm", self.container_name], check=True)
        elif self.platform == DockerPlatform.AWS_ECS:
            self.ecs_client.stop_task(
                cluster="commandlab-cluster",
                task=self.task_arn
            )
        elif self.platform == DockerPlatform.AZURE_CONTAINER_INSTANCES:
            self.aci_client.container_groups.begin_delete(
                self.resource_group,
                self.container_name
            ).result()
        elif self.platform == DockerPlatform.GCP_CLOUD_RUN:
            name = f"projects/{self.project_id}/locations/{self.region}/services/{self.container_name}"
            self.cloud_run_client.delete_service(name=name)

    def is_running(self) -> bool:
        try:
            if self.platform == DockerPlatform.LOCAL:
                result = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Running}}", self.container_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip() == "true"
            elif self.platform == DockerPlatform.AWS_ECS:
                response = self.ecs_client.describe_tasks(
                    cluster="commandlab-cluster",
                    tasks=[self.task_arn]
                )
                return response['tasks'][0]['lastStatus'] == 'RUNNING'
            elif self.platform == DockerPlatform.AZURE_CONTAINER_INSTANCES:
                container_group = self.aci_client.container_groups.get(
                    self.resource_group,
                    self.container_name
                )
                return container_group.containers[0].instance_view.current_state.state == 'Running'
            elif self.platform == DockerPlatform.GCP_CLOUD_RUN:
                name = f"projects/{self.project_id}/locations/{self.region}/services/{self.container_name}"
                service = self.cloud_run_client.get_service(name=name)
                return service.status.conditions[0].status == True
        except Exception:
            return False 