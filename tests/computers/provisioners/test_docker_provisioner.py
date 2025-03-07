import unittest
from unittest.mock import patch, MagicMock, call
import time
import docker
from docker.errors import DockerException, NotFound

from commandAGI.computers.provisioners.docker_provisioner import (
    DockerProvisioner,
    DockerPlatform,
)


class TestDockerProvisioner(unittest.TestCase):
    @patch("docker.from_env")
    def setUp(self, mock_docker_from_env):
        # Mock Docker client
        self.mock_docker_client = MagicMock()
        self.mock_containers = MagicMock()
        self.mock_images = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = self.mock_docker_client
        self.mock_docker_client.containers = self.mock_containers
        self.mock_docker_client.images = self.mock_images

        # Store the mock for later assertions
        self.mock_docker_from_env = mock_docker_from_env

        # Create a provisioner for testing
        self.provisioner = DockerProvisioner(
            port=8000,
            container_name="test-container",
            version="test-version",
            max_retries=2,
        )

    def test_init(self):
        # Test that the provisioner initializes with the correct attributes
        self.assertEqual(self.provisioner.port, 8000)
        self.assertEqual(self.provisioner.container_name, "test-container")
        self.assertEqual(self.provisioner.platform, DockerPlatform.LOCAL)
        self.assertEqual(self.provisioner.version, "test-version")
        self.assertEqual(self.provisioner.max_provisioning_retries, 2)
        self.assertEqual(self.provisioner.timeout, 300)
        self.assertEqual(self.provisioner._status, "not_started")

    def test_init_with_cloud_params(self):
        # Test initialization with cloud-specific parameters
        provisioner = DockerProvisioner(
            platform=DockerPlatform.AWS_ECS,
            region="us-west-2",
            subnets=["subnet-1", "subnet-2"],
            security_groups=["sg-1", "sg-2"],
        )

        self.assertEqual(provisioner.platform, DockerPlatform.AWS_ECS)
        self.assertEqual(provisioner.region, "us-west-2")
        self.assertEqual(provisioner.subnets, ["subnet-1", "subnet-2"])
        self.assertEqual(provisioner.security_groups, ["sg-1", "sg-2"])

    @patch("docker.from_env")
    @patch("time.sleep")
    def test_setup_local_success(self, mock_sleep, mock_docker_from_env):
        # Create a new provisioner to avoid interference from setUp
        provisioner = DockerProvisioner(
            port=8000,
            container_name="test-container",
            version="test-version",
            max_retries=2,
        )

        # Mock Docker client
        mock_docker_client = MagicMock()
        mock_containers = MagicMock()
        mock_images = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers = mock_containers
        mock_docker_client.images = mock_images

        # Mock container
        mock_container = MagicMock()
        mock_containers.run.return_value = mock_container

        # Mock is_running to return True
        provisioner.is_running = MagicMock(return_value=True)

        # Call setup
        provisioner.setup()

        # Check that containers.run was called with the right arguments
        mock_containers.run.assert_called_once()
        run_args = mock_containers.run.call_args[1]
        self.assertEqual(run_args["name"], "test-container")

        # Check that status was updated
        self.assertEqual(provisioner._status, "running")

    @patch("docker.from_env")
    @patch("time.sleep")
    def test_setup_local_image_pull(self, mock_sleep, mock_docker_from_env):
        # Create a new provisioner to avoid interference from setUp
        provisioner = DockerProvisioner(
            port=8000,
            container_name="test-container",
            version="test-version",
            max_retries=2,
        )

        # Mock Docker client
        mock_docker_client = MagicMock()
        mock_containers = MagicMock()
        mock_images = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers = mock_containers
        mock_docker_client.images = mock_images

        # Mock containers.run to fail once with ImageNotFound, then succeed
        mock_container = MagicMock()
        mock_containers.run.side_effect = [
            docker.errors.ImageNotFound("Image not found"),
            mock_container,
        ]

        # Mock is_running to return True
        provisioner.is_running = MagicMock(return_value=True)

        # Call setup
        provisioner.setup()

        # Check that containers.run was called twice
        self.assertEqual(mock_containers.run.call_count, 2)

        # Check that status was updated
        self.assertEqual(provisioner._status, "running")

    @patch("docker.from_env")
    @patch("time.sleep")
    def test_setup_local_retry_success(self, mock_sleep, mock_docker_from_env):
        # Create a new provisioner to avoid interference from setUp
        provisioner = DockerProvisioner(
            port=8000,
            container_name="test-container",
            version="test-version",
            max_retries=2,
        )

        # Mock Docker client
        mock_docker_client = MagicMock()
        mock_containers = MagicMock()
        mock_images = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers = mock_containers
        mock_docker_client.images = mock_images

        # Mock containers.run to fail once with a general error, then succeed
        mock_container = MagicMock()
        mock_containers.run.side_effect = [
            DockerException("Docker error"),
            mock_container,
        ]

        # Mock is_running to return True
        provisioner.is_running = MagicMock(return_value=True)

        # Call setup
        provisioner.setup()

        # Check that containers.run was called twice
        self.assertEqual(mock_containers.run.call_count, 2)

        # Check that sleep was called for retry backoff
        mock_sleep.assert_called_once_with(2)  # 2^1

        # Check that status was updated
        self.assertEqual(provisioner._status, "running")

    @patch("docker.from_env")
    @patch("time.sleep")
    def test_setup_local_max_retries_exceeded(self, mock_sleep, mock_docker_from_env):
        # Create a new provisioner to avoid interference from setUp
        provisioner = DockerProvisioner(
            port=8000,
            container_name="test-container",
            version="test-version",
            max_retries=1,  # Set to 1 to simplify the test
        )

        # Mock Docker client
        mock_docker_client = MagicMock()
        mock_containers = MagicMock()
        mock_images = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers = mock_containers
        mock_docker_client.images = mock_images

        # Mock containers.run to always fail
        mock_containers.run.side_effect = DockerException("Docker error")

        # Call setup and check that it raises DockerException
        with self.assertRaises(DockerException):
            provisioner.setup()

        # Check that containers.run was called at least once
        self.assertTrue(mock_containers.run.called)

        # Check that status was updated to error
        self.assertEqual(provisioner._status, "error")

    # @patch('boto3.client')
    # @patch('time.sleep')
    # def test_setup_aws_ecs(self, mock_sleep, mock_boto3_client):
    #     # Create a provisioner with AWS_ECS platform
    #     provisioner = DockerProvisioner(
    #         port=8000,
    #         platform=DockerPlatform.AWS_ECS,
    #         region="us-west-2",
    #         subnets=["subnet-1"],
    #         security_groups=["sg-1"]
    #     )

    #     # Mock ECS client
    #     mock_ecs = MagicMock()
    #     mock_boto3_client.return_value = mock_ecs

    #     # Mock run_task response
    #     mock_ecs.run_task.return_value = {
    #         'tasks': [{'taskArn': 'task-arn'}]
    #     }

    #     # Mock describe_tasks response
    #     mock_ecs.describe_tasks.return_value = {
    #         'tasks': [{'lastStatus': 'RUNNING'}]
    #     }

    #     # Call setup
    #     provisioner.setup()

    #     # Check that boto3.client was called with the right arguments
    #     mock_boto3_client.assert_called_with('ecs', region_name="us-west-2")

    #     # Check that run_task was called with the right arguments
    #     mock_ecs.run_task.assert_called_once()
    #     run_task_args = mock_ecs.run_task.call_args[1]
    #     self.assertEqual(run_task_args['launchType'], 'FARGATE')
    #     self.assertEqual(run_task_args['networkConfiguration']['awsvpcConfiguration']['subnets'], ["subnet-1"])
    #     self.assertEqual(run_task_args['networkConfiguration']['awsvpcConfiguration']['securityGroups'], ["sg-1"])

    #     # Check that describe_tasks was called
    #     mock_ecs.describe_tasks.assert_called_once()

    #     # Check that status was updated
    #     self.assertEqual(provisioner._status, "running")

    @patch("docker.from_env")
    def test_teardown_local_success(self, mock_docker_from_env):
        # Mock Docker client and container
        mock_docker_client = MagicMock()
        mock_container = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.return_value = mock_container

        # Call teardown
        self.provisioner.teardown()

        # Check that docker.from_env was called
        mock_docker_from_env.assert_called_once()

        # Check that containers.get was called with the right arguments
        mock_docker_client.containers.get.assert_called_once_with("test-container")

        # Check that container.stop and container.remove were called
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()

        # Check that status was updated
        self.assertEqual(self.provisioner._status, "stopped")

    @patch("docker.from_env")
    def test_teardown_local_container_not_found(self, mock_docker_from_env):
        # Mock Docker client
        mock_docker_client = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        # Call teardown
        self.provisioner.teardown()

        # Check that docker.from_env was called
        mock_docker_from_env.assert_called_once()

        # Check that containers.get was called
        mock_docker_client.containers.get.assert_called_once()

        # Check that status was updated
        self.assertEqual(self.provisioner._status, "stopped")

    @patch("docker.from_env")
    def test_teardown_local_error(self, mock_docker_from_env):
        # Mock Docker client
        mock_docker_client = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = DockerException("Docker error")

        # Call teardown
        self.provisioner.teardown()

        # Check that docker.from_env was called
        mock_docker_from_env.assert_called_once()

        # Check that containers.get was called
        mock_docker_client.containers.get.assert_called_once()

        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")

    # @patch('boto3.client')
    # def test_teardown_aws_ecs(self, mock_boto3_client):
    #     # Create a provisioner with AWS_ECS platform
    #     provisioner = DockerProvisioner(
    #         port=8000,
    #         platform=DockerPlatform.AWS_ECS,
    #         region="us-west-2"
    #     )
    #     provisioner._task_arn = "task-arn"  # Set task ARN

    #     # Mock ECS client
    #     mock_ecs = MagicMock()
    #     mock_boto3_client.return_value = mock_ecs

    #     # Call teardown
    #     provisioner.teardown()

    #     # Check that stop_task was called with the right arguments
    #     mock_ecs.stop_task.assert_called_once_with(
    #         cluster="default",
    #         task="task-arn",
    #         reason="Stopped by commandAGI"
    #     )

    #     # Check that status was updated
    #     self.assertEqual(provisioner._status, "stopped")

    @patch("docker.from_env")
    def test_is_running_local_true(self, mock_docker_from_env):
        # Mock Docker client and container
        mock_docker_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = "running"

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.return_value = mock_container

        # Check that is_running returns True
        self.assertTrue(self.provisioner.is_running())

        # Check that docker.from_env was called
        mock_docker_from_env.assert_called_once()

        # Check that containers.get was called with the right arguments
        mock_docker_client.containers.get.assert_called_once_with("test-container")

    @patch("docker.from_env")
    def test_is_running_local_false(self, mock_docker_from_env):
        # Mock Docker client and container
        mock_docker_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = "exited"

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.return_value = mock_container

        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())

        # Check that docker.from_env was called
        mock_docker_from_env.assert_called_once()

        # Check that containers.get was called with the right arguments
        mock_docker_client.containers.get.assert_called_once_with("test-container")

    @patch("docker.from_env")
    def test_is_running_local_not_found(self, mock_docker_from_env):
        # Mock Docker client
        mock_docker_client = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())

        # Check that docker.from_env was called
        mock_docker_from_env.assert_called_once()

        # Check that containers.get was called with the right arguments
        mock_docker_client.containers.get.assert_called_once_with("test-container")

    @patch("docker.from_env")
    def test_is_running_local_error(self, mock_docker_from_env):
        # Mock Docker client
        mock_docker_client = MagicMock()

        # Set up the mock chain
        mock_docker_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = DockerException("Docker error")

        # Check that is_running returns False on error
        self.assertFalse(self.provisioner.is_running())

        # Check that docker.from_env was called
        mock_docker_from_env.assert_called_once()

        # Check that containers.get was called with the right arguments
        mock_docker_client.containers.get.assert_called_once_with("test-container")

    @patch("boto3.client")
    def test_is_running_aws_ecs_true(self, mock_boto3_client):
        # Create a provisioner with AWS_ECS platform
        provisioner = DockerProvisioner(
            platform=DockerPlatform.AWS_ECS, region="us-west-2"
        )
        provisioner._task_arn = "task-arn"  # Set task ARN

        # Mock ECS client
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        # Set the ecs_client attribute on the provisioner
        provisioner.ecs_client = mock_ecs

        # Mock describe_tasks response
        mock_ecs.describe_tasks.return_value = {"tasks": [{"lastStatus": "RUNNING"}]}

        # Check that is_running returns True
        self.assertTrue(provisioner.is_running())

        # Check that describe_tasks was called with the right arguments
        mock_ecs.describe_tasks.assert_called_once_with(
            cluster="commandagi-cluster", tasks=["task-arn"]
        )

    @patch("azure.mgmt.containerinstance.ContainerInstanceManagementClient")
    @patch("azure.identity.DefaultAzureCredential")
    def test_is_running_azure_container_instances_true(
        self, mock_credential, mock_aci_client_cls
    ):
        # Create a provisioner with AZURE_CONTAINER_INSTANCES platform
        provisioner = DockerProvisioner(
            platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
            resource_group="test-rg",
            subscription_id="test-subscription",
        )

        # Mock ACI client
        mock_aci_client = mock_aci_client_cls.return_value
        mock_container_groups = MagicMock()
        mock_aci_client.container_groups = mock_container_groups

        # Set the aci_client attribute on the provisioner
        provisioner.aci_client = mock_aci_client

        # Mock get response
        mock_container_group = MagicMock()
        mock_container = MagicMock()
        mock_instance_view = MagicMock()
        mock_current_state = MagicMock()

        mock_current_state.state = "Running"
        mock_instance_view.current_state = mock_current_state
        mock_container.instance_view = mock_instance_view
        mock_container_group.containers = [mock_container]

        mock_container_groups.get.return_value = mock_container_group

        # Check that is_running returns True
        self.assertTrue(provisioner.is_running())

        # Check that get was called with the right arguments
        mock_container_groups.get.assert_called_once_with(
            "test-rg", "commandagi-daemon"
        )

    @patch("google.cloud.run_v2.ServicesClient")
    @patch(
        "commandAGI.computers.provisioners.docker_provisioner.DockerProvisioner.__init__"
    )
    def test_is_running_gcp_cloud_run_true(self, mock_init, mock_services_client_cls):
        # Mock the __init__ method to avoid the CloudRunClient initialization
        mock_init.return_value = None

        # Create a provisioner with GCP_CLOUD_RUN platform
        provisioner = DockerProvisioner()

        # Set the necessary attributes manually
        provisioner.platform = DockerPlatform.GCP_CLOUD_RUN
        provisioner.project_id = "test-project"
        provisioner.region = "us-central1"
        provisioner.container_name = "commandagi-daemon"

        # Mock Cloud Run client
        mock_services_client = mock_services_client_cls.return_value
        provisioner.cloud_run_client = mock_services_client

        # Mock get_service response
        mock_service = MagicMock()
        mock_service.status.conditions = [MagicMock(status=True)]
        mock_services_client.get_service.return_value = mock_service

        # Add the is_running method to check if it's properly mocked
        provisioner.is_running = lambda: provisioner._is_gcp_cloud_run_running()

        # Check that is_running returns True
        self.assertTrue(provisioner.is_running())

        # Check that get_service was called with the right arguments
        name = f"projects/test-project/locations/us-central1/services/commandagi-daemon"
        mock_services_client.get_service.assert_called_once_with(name=name)

    def test_get_status(self):
        # Test that get_status returns the current status
        self.assertEqual(self.provisioner.get_status(), "not_started")

        # Change status and check again
        self.provisioner._status = "running"
        self.assertEqual(self.provisioner.get_status(), "running")


if __name__ == "__main__":
    unittest.main()
