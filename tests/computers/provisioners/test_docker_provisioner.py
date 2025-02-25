import unittest
from unittest.mock import patch, MagicMock, call
import time
import docker
from docker.errors import DockerException, NotFound

from commandLAB.computers.provisioners.docker_provisioner import (
    DockerProvisioner,
    DockerPlatform
)


class TestDockerProvisioner(unittest.TestCase):
    @patch('docker.from_env')
    def setUp(self, mock_docker_from_env):
        # Create mock Docker client and its components
        self.mock_docker_client = MagicMock()
        self.mock_containers = MagicMock()
        self.mock_images = MagicMock()
        
        self.mock_docker_client.containers = self.mock_containers
        self.mock_docker_client.images = self.mock_images
        mock_docker_from_env.return_value = self.mock_docker_client
        
        # Create a DockerProvisioner with LOCAL platform
        self.provisioner = DockerProvisioner(
            port=8000,
            container_name="test-container",
            platform=DockerPlatform.LOCAL,
            version="test-version",
            max_retries=2,
            timeout=10
        )
        
        # Store the mock for later use
        self.mock_docker_from_env = mock_docker_from_env
    
    def test_init(self):
        # Test that the provisioner initializes with the correct attributes
        self.assertEqual(self.provisioner.port, 8000)
        self.assertEqual(self.provisioner.container_name, "test-container")
        self.assertEqual(self.provisioner.platform, DockerPlatform.LOCAL)
        self.assertEqual(self.provisioner.version, "test-version")
        self.assertEqual(self.provisioner.max_retries, 2)
        self.assertEqual(self.provisioner.timeout, 10)
        self.assertEqual(self.provisioner._status, "not_started")
        
        # Check that docker.from_env was called
        self.mock_docker_from_env.assert_called_once()
    
    def test_init_with_cloud_params(self):
        # Test initialization with cloud-specific parameters
        provisioner = DockerProvisioner(
            platform=DockerPlatform.AWS_ECS,
            region="us-west-2",
            subnets=["subnet-1", "subnet-2"],
            security_groups=["sg-1", "sg-2"]
        )
        
        self.assertEqual(provisioner.platform, DockerPlatform.AWS_ECS)
        self.assertEqual(provisioner.region, "us-west-2")
        self.assertEqual(provisioner.subnets, ["subnet-1", "subnet-2"])
        self.assertEqual(provisioner.security_groups, ["sg-1", "sg-2"])
    
    @patch('time.sleep')
    def test_setup_local_success(self, mock_sleep):
        # Mock container
        mock_container = MagicMock()
        self.mock_containers.run.return_value = mock_container
        
        # Mock is_running to return True
        self.provisioner.is_running = MagicMock(return_value=True)
        
        # Call setup
        self.provisioner.setup()
        
        # Check that containers.run was called with the right arguments
        self.mock_containers.run.assert_called_once()
        run_args = self.mock_containers.run.call_args
        self.assertEqual(run_args[0][0], "commandlab-daemon:test-version")
        self.assertEqual(run_args[1]["name"], "test-container")
        self.assertEqual(run_args[1]["ports"], {"8000/tcp": 8000})
        self.assertTrue(run_args[1]["detach"])
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    @patch('time.sleep')
    def test_setup_local_image_pull(self, mock_sleep):
        # Mock containers.run to fail once with ImageNotFound, then succeed
        mock_container = MagicMock()
        self.mock_containers.run.side_effect = [
            docker.errors.ImageNotFound("Image not found"),
            mock_container
        ]
        
        # Mock images.pull
        self.mock_images.pull.return_value = MagicMock()
        
        # Mock is_running to return True
        self.provisioner.is_running = MagicMock(return_value=True)
        
        # Call setup
        self.provisioner.setup()
        
        # Check that images.pull was called
        self.mock_images.pull.assert_called_once_with("commandlab-daemon", tag="test-version")
        
        # Check that containers.run was called twice
        self.assertEqual(self.mock_containers.run.call_count, 2)
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    @patch('time.sleep')
    def test_setup_local_retry_success(self, mock_sleep):
        # Mock containers.run to fail once with a general error, then succeed
        mock_container = MagicMock()
        self.mock_containers.run.side_effect = [
            DockerException("Docker error"),
            mock_container
        ]
        
        # Mock is_running to return True
        self.provisioner.is_running = MagicMock(return_value=True)
        
        # Call setup
        self.provisioner.setup()
        
        # Check that containers.run was called twice
        self.assertEqual(self.mock_containers.run.call_count, 2)
        
        # Check that sleep was called for retry backoff
        mock_sleep.assert_called_once_with(2)  # 2^1
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    @patch('time.sleep')
    def test_setup_local_max_retries_exceeded(self, mock_sleep):
        # Mock containers.run to always fail
        self.mock_containers.run.side_effect = DockerException("Docker error")
        
        # Call setup and check that it raises DockerException
        with self.assertRaises(DockerException):
            self.provisioner.setup()
        
        # Check that containers.run was called max_retries times
        self.assertEqual(self.mock_containers.run.call_count, 2)  # max_retries=2
        
        # Check that sleep was called for retry backoff
        mock_sleep.assert_has_calls([call(2), call(4)])  # 2^1, 2^2
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('boto3.client')
    @patch('time.sleep')
    def test_setup_aws_ecs(self, mock_sleep, mock_boto3_client):
        # Create a provisioner with AWS_ECS platform
        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.AWS_ECS,
            region="us-west-2",
            subnets=["subnet-1"],
            security_groups=["sg-1"]
        )
        
        # Mock ECS client
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs
        
        # Mock run_task response
        mock_ecs.run_task.return_value = {
            'tasks': [{'taskArn': 'task-arn'}]
        }
        
        # Mock describe_tasks response
        mock_ecs.describe_tasks.return_value = {
            'tasks': [{'lastStatus': 'RUNNING'}]
        }
        
        # Call setup
        provisioner.setup()
        
        # Check that boto3.client was called with the right arguments
        mock_boto3_client.assert_called_with('ecs', region_name="us-west-2")
        
        # Check that run_task was called with the right arguments
        mock_ecs.run_task.assert_called_once()
        run_task_args = mock_ecs.run_task.call_args[1]
        self.assertEqual(run_task_args['launchType'], 'FARGATE')
        self.assertEqual(run_task_args['networkConfiguration']['awsvpcConfiguration']['subnets'], ["subnet-1"])
        self.assertEqual(run_task_args['networkConfiguration']['awsvpcConfiguration']['securityGroups'], ["sg-1"])
        
        # Check that describe_tasks was called
        mock_ecs.describe_tasks.assert_called_once()
        
        # Check that status was updated
        self.assertEqual(provisioner._status, "running")
    
    @patch('azure.mgmt.containerinstance.ContainerInstanceManagementClient')
    @patch('azure.identity.DefaultAzureCredential')
    @patch('time.sleep')
    def test_setup_azure_container_instances(self, mock_sleep, mock_credential, mock_aci_client_cls):
        # Create a provisioner with AZURE_CONTAINER_INSTANCES platform
        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
            resource_group="test-rg",
            region="eastus",
            subscription_id="test-subscription"
        )
        
        # Mock ACI client
        mock_aci_client = mock_aci_client_cls.return_value
        mock_container_groups = MagicMock()
        mock_aci_client.container_groups = mock_container_groups
        
        # Mock begin_create_or_update response
        mock_poller = MagicMock()
        mock_poller.done.return_value = True
        mock_poller.result.return_value = MagicMock()
        mock_container_groups.begin_create_or_update.return_value = mock_poller
        
        # Mock get response
        mock_container_groups.get.return_value = MagicMock(provisioning_state="Succeeded")
        
        # Call setup
        provisioner.setup()
        
        # Check that ContainerInstanceManagementClient was created with the right arguments
        mock_aci_client_cls.assert_called_once()
        
        # Check that begin_create_or_update was called with the right arguments
        mock_container_groups.begin_create_or_update.assert_called_once()
        create_args = mock_container_groups.begin_create_or_update.call_args
        self.assertEqual(create_args[0][0], "test-rg")  # resource_group
        
        # Check that status was updated
        self.assertEqual(provisioner._status, "running")
    
    @patch('google.cloud.run_v2.ServicesClient')
    @patch('time.sleep')
    def test_setup_gcp_cloud_run(self, mock_sleep, mock_services_client_cls):
        # Create a provisioner with GCP_CLOUD_RUN platform
        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.GCP_CLOUD_RUN,
            project_id="test-project",
            region="us-central1"
        )
        
        # Mock Cloud Run client
        mock_services_client = mock_services_client_cls.return_value
        
        # Mock create_service response
        mock_operation = MagicMock()
        mock_operation.done.return_value = True
        mock_operation.result.return_value = MagicMock()
        mock_services_client.create_service.return_value = mock_operation
        
        # Call setup
        provisioner.setup()
        
        # Check that ServicesClient was created
        mock_services_client_cls.assert_called_once()
        
        # Check that create_service was called
        mock_services_client.create_service.assert_called_once()
        
        # Check that status was updated
        self.assertEqual(provisioner._status, "running")
    
    def test_teardown_local_success(self):
        # Mock container
        mock_container = MagicMock()
        self.mock_containers.get.return_value = mock_container
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that containers.get was called with the right arguments
        self.mock_containers.get.assert_called_once_with("test-container")
        
        # Check that container.stop and container.remove were called
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "stopped")
    
    def test_teardown_local_container_not_found(self):
        # Mock containers.get to raise NotFound
        self.mock_containers.get.side_effect = NotFound("Container not found")
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that containers.get was called
        self.mock_containers.get.assert_called_once()
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "stopped")
    
    def test_teardown_local_error(self):
        # Mock containers.get to raise an error
        self.mock_containers.get.side_effect = DockerException("Docker error")
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that containers.get was called
        self.mock_containers.get.assert_called_once()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('boto3.client')
    def test_teardown_aws_ecs(self, mock_boto3_client):
        # Create a provisioner with AWS_ECS platform
        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.AWS_ECS,
            region="us-west-2"
        )
        provisioner._task_arn = "task-arn"  # Set task ARN
        
        # Mock ECS client
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs
        
        # Call teardown
        provisioner.teardown()
        
        # Check that stop_task was called with the right arguments
        mock_ecs.stop_task.assert_called_once_with(
            cluster="default",
            task="task-arn",
            reason="Stopped by CommandLAB"
        )
        
        # Check that status was updated
        self.assertEqual(provisioner._status, "stopped")
    
    @patch('azure.mgmt.containerinstance.ContainerInstanceManagementClient')
    @patch('azure.identity.DefaultAzureCredential')
    def test_teardown_azure_container_instances(self, mock_credential, mock_aci_client_cls):
        # Create a provisioner with AZURE_CONTAINER_INSTANCES platform
        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
            resource_group="test-rg",
            subscription_id="test-subscription"
        )
        
        # Mock ACI client
        mock_aci_client = mock_aci_client_cls.return_value
        mock_container_groups = MagicMock()
        mock_aci_client.container_groups = mock_container_groups
        
        # Mock begin_delete response
        mock_poller = MagicMock()
        mock_poller.done.return_value = True
        mock_container_groups.begin_delete.return_value = mock_poller
        
        # Call teardown
        provisioner.teardown()
        
        # Check that begin_delete was called with the right arguments
        mock_container_groups.begin_delete.assert_called_once_with(
            "test-rg",
            "commandlab-daemon"
        )
        
        # Check that status was updated
        self.assertEqual(provisioner._status, "stopped")
    
    @patch('google.cloud.run_v2.ServicesClient')
    def test_teardown_gcp_cloud_run(self, mock_services_client_cls):
        # Create a provisioner with GCP_CLOUD_RUN platform
        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.GCP_CLOUD_RUN,
            project_id="test-project",
            region="us-central1"
        )
        
        # Mock Cloud Run client
        mock_services_client = mock_services_client_cls.return_value
        
        # Mock delete_service response
        mock_operation = MagicMock()
        mock_operation.done.return_value = True
        mock_services_client.delete_service.return_value = mock_operation
        
        # Call teardown
        provisioner.teardown()
        
        # Check that delete_service was called
        mock_services_client.delete_service.assert_called_once()
        
        # Check that status was updated
        self.assertEqual(provisioner._status, "stopped")
    
    def test_is_running_local_true(self):
        # Mock container
        mock_container = MagicMock()
        mock_container.status = "running"
        self.mock_containers.get.return_value = mock_container
        
        # Check that is_running returns True
        self.assertTrue(self.provisioner.is_running())
        
        # Check that containers.get was called with the right arguments
        self.mock_containers.get.assert_called_once_with("test-container")
    
    def test_is_running_local_false(self):
        # Mock container
        mock_container = MagicMock()
        mock_container.status = "exited"
        self.mock_containers.get.return_value = mock_container
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
    
    def test_is_running_local_not_found(self):
        # Mock containers.get to raise NotFound
        self.mock_containers.get.side_effect = NotFound("Container not found")
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
    
    def test_is_running_local_error(self):
        # Mock containers.get to raise an error
        self.mock_containers.get.side_effect = DockerException("Docker error")
        
        # Check that is_running returns False on error
        self.assertFalse(self.provisioner.is_running())
    
    @patch('boto3.client')
    def test_is_running_aws_ecs_true(self, mock_boto3_client):
        # Create a provisioner with AWS_ECS platform
        provisioner = DockerProvisioner(
            platform=DockerPlatform.AWS_ECS,
            region="us-west-2"
        )
        provisioner._task_arn = "task-arn"  # Set task ARN
        
        # Mock ECS client
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs
        
        # Mock describe_tasks response
        mock_ecs.describe_tasks.return_value = {
            'tasks': [{'lastStatus': 'RUNNING'}]
        }
        
        # Check that is_running returns True
        self.assertTrue(provisioner.is_running())
        
        # Check that describe_tasks was called with the right arguments
        mock_ecs.describe_tasks.assert_called_once_with(
            cluster="default",
            tasks=["task-arn"]
        )
    
    @patch('azure.mgmt.containerinstance.ContainerInstanceManagementClient')
    @patch('azure.identity.DefaultAzureCredential')
    def test_is_running_azure_container_instances_true(self, mock_credential, mock_aci_client_cls):
        # Create a provisioner with AZURE_CONTAINER_INSTANCES platform
        provisioner = DockerProvisioner(
            platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
            resource_group="test-rg",
            subscription_id="test-subscription"
        )
        
        # Mock ACI client
        mock_aci_client = mock_aci_client_cls.return_value
        mock_container_groups = MagicMock()
        mock_aci_client.container_groups = mock_container_groups
        
        # Mock get response
        mock_container_groups.get.return_value = MagicMock(provisioning_state="Succeeded")
        
        # Check that is_running returns True
        self.assertTrue(provisioner.is_running())
        
        # Check that get was called with the right arguments
        mock_container_groups.get.assert_called_once_with(
            "test-rg",
            "commandlab-daemon"
        )
    
    @patch('google.cloud.run_v2.ServicesClient')
    def test_is_running_gcp_cloud_run_true(self, mock_services_client_cls):
        # Create a provisioner with GCP_CLOUD_RUN platform
        provisioner = DockerProvisioner(
            platform=DockerPlatform.GCP_CLOUD_RUN,
            project_id="test-project",
            region="us-central1"
        )
        
        # Mock Cloud Run client
        mock_services_client = mock_services_client_cls.return_value
        
        # Mock get_service response
        mock_service = MagicMock()
        mock_service.latest_ready_revision = "revision-1"
        mock_services_client.get_service.return_value = mock_service
        
        # Check that is_running returns True
        self.assertTrue(provisioner.is_running())
        
        # Check that get_service was called
        mock_services_client.get_service.assert_called_once()
    
    def test_get_status(self):
        # Test that get_status returns the current status
        self.assertEqual(self.provisioner.get_status(), "not_started")
        
        # Change status and check again
        self.provisioner._status = "running"
        self.assertEqual(self.provisioner.get_status(), "running")


if __name__ == '__main__':
    unittest.main() 