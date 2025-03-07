# import unittest
# from unittest.mock import patch, MagicMock, call
# import time
# import sys
# import os

# # Add the mocks directory to the path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mocks')))

# from commandAGI.computers.provisioners.gcp_provisioner import GCPProvisioner


# class TestGCPProvisioner(unittest.TestCase):
#     @patch('google.cloud.compute_v1.InstancesClient')
#     def setUp(self, mock_instances_client_cls):
#         # Create a mock instances client
#         self.mock_instances_client = mock_instances_client_cls.return_value

#         # Create a GCPProvisioner
#         self.provisioner = GCPProvisioner(
#             port=8000,
#             project="test-project",
#             zone="us-central1-a",
#             machine_type="n1-standard-1",
#             source_image="projects/test-project/global/images/test-image",
#             max_retries=2,
#             timeout=10
#         )

#     def test_init(self):
#         # Test that the provisioner initializes with the correct attributes
#         self.assertEqual(self.provisioner.port, 8000)
#         self.assertEqual(self.provisioner.project, "test-project")
#         self.assertEqual(self.provisioner.zone, "us-central1-a")
#         self.assertEqual(self.provisioner.machine_type, "n1-standard-1")
#         self.assertEqual(self.provisioner.instance_name, "commandagi-daemon")
#         self.assertEqual(self.provisioner.source_image, "projects/test-project/global/images/test-image")
#         self.assertEqual(self.provisioner.max_retries, 2)
#         self.assertEqual(self.provisioner.timeout, 10)
#         self.assertEqual(self.provisioner._status, "not_started")

#     def test_init_missing_project(self):
#         # Test that initialization fails if project is not provided
#         with self.assertRaises(ValueError):
#             GCPProvisioner(port=8000)

#     @patch('time.sleep')
#     def test_setup_success(self, mock_sleep):
#         # Create a mock operation
#         mock_operation = MagicMock()
#         mock_operation.done.return_value = True
#         self.mock_instances_client.insert.return_value = mock_operation

#         # Mock is_running to return True after one check
#         self.provisioner.is_running = MagicMock(side_effect=[False, True])

#         # Call setup
#         self.provisioner.setup()

#         # Check that insert was called with the right arguments
#         self.mock_instances_client.insert.assert_called_once()
#         args, kwargs = self.mock_instances_client.insert.call_args
#         self.assertEqual(kwargs['project'], "test-project")
#         self.assertEqual(kwargs['zone'], "us-central1-a")

#         # Check that the instance configuration is correct
#         instance = kwargs['instance_resource']
#         self.assertEqual(instance.name, "commandagi-daemon")
#         self.assertEqual(instance.machine_type, f"zones/us-central1-a/machineTypes/n1-standard-1")

#         # Check that is_running was called
#         self.assertEqual(self.provisioner.is_running.call_count, 2)

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch('time.sleep')
#     def test_setup_operation_timeout(self, mock_sleep):
#         # Create a mock operation that never completes
#         mock_operation = MagicMock()
#         mock_operation.done.return_value = False
#         self.mock_instances_client.insert.return_value = mock_operation

#         # Call setup and expect a timeout
#         with self.assertRaises(TimeoutError):
#             self.provisioner.setup()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_setup_is_running_timeout(self, mock_sleep):
#         # Create a mock operation that completes
#         mock_operation = MagicMock()
#         mock_operation.done.return_value = True
#         self.mock_instances_client.insert.return_value = mock_operation

#         # Mock is_running to always return False
#         self.provisioner.is_running = MagicMock(return_value=False)

#         # Call setup and expect a timeout
#         with self.assertRaises(TimeoutError):
#             self.provisioner.setup()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_setup_retry_success(self, mock_sleep):
#         # Create a mock operation
#         mock_operation = MagicMock()
#         mock_operation.done.return_value = True

#         # Mock insert to fail once, then succeed
#         self.mock_instances_client.insert.side_effect = [
#             Exception("Insert error"),
#             mock_operation
#         ]

#         # Mock is_running to return True after one check
#         self.provisioner.is_running = MagicMock(side_effect=[False, True])

#         # Call setup
#         self.provisioner.setup()

#         # Check that insert was called twice
#         self.assertEqual(self.mock_instances_client.insert.call_count, 2)

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch('time.sleep')
#     def test_setup_max_retries_exceeded(self, mock_sleep):
#         # Mock the instances client to always fail
#         self.mock_instances_client.insert.side_effect = Exception("Insert error")

#         # Call setup and expect an exception
#         with self.assertRaises(Exception):
#             self.provisioner.setup()

#         # Check that insert was called the right number of times
#         self.assertEqual(self.mock_instances_client.insert.call_count, 2)

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_teardown_success(self, mock_sleep):
#         # Create a mock operation
#         mock_operation = MagicMock()
#         mock_operation.done.return_value = True
#         self.mock_instances_client.delete.return_value = mock_operation

#         # Set instance_id
#         self.provisioner.instance_name = "test-instance"
#         self.provisioner._status = "running"

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that delete was called with the right arguments
#         self.mock_instances_client.delete.assert_called_once_with(
#             project="test-project",
#             zone="us-central1-a",
#             instance="test-instance"
#         )

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "stopped")

#     @patch('time.sleep')
#     def test_teardown_operation_timeout(self, mock_sleep):
#         # Create a mock operation that never completes
#         mock_operation = MagicMock()
#         mock_operation.done.return_value = False
#         self.mock_instances_client.delete.return_value = mock_operation

#         # Set instance_id
#         self.provisioner.instance_name = "test-instance"
#         self.provisioner._status = "running"

#         # Call teardown and expect a timeout
#         with self.assertRaises(TimeoutError):
#             self.provisioner.teardown()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_teardown_error(self, mock_sleep):
#         # Mock the instances client to raise an error
#         self.mock_instances_client.delete.side_effect = Exception("Delete error")

#         # Set instance_id
#         self.provisioner.instance_name = "test-instance"
#         self.provisioner._status = "running"

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     def test_is_running_true(self):
#         # Create a mock instance
#         mock_instance = MagicMock()
#         mock_instance.status = "RUNNING"
#         self.mock_instances_client.get.return_value = mock_instance

#         # Set instance_id
#         self.provisioner.instance_name = "test-instance"

#         # Call is_running
#         result = self.provisioner.is_running()

#         # Check that get was called with the right arguments
#         self.mock_instances_client.get.assert_called_once_with(
#             project="test-project",
#             zone="us-central1-a",
#             instance="test-instance"
#         )

#         # Check that the result is True
#         self.assertTrue(result)

#     def test_is_running_false(self):
#         # Create a mock instance
#         mock_instance = MagicMock()
#         mock_instance.status = "STOPPED"
#         self.mock_instances_client.get.return_value = mock_instance

#         # Set instance_id
#         self.provisioner.instance_name = "test-instance"

#         # Call is_running
#         result = self.provisioner.is_running()

#         # Check that the result is False
#         self.assertFalse(result)

#     def test_is_running_error(self):
#         # Mock the instances client to raise an error
#         self.mock_instances_client.get.side_effect = Exception("Get error")

#         # Call is_running
#         result = self.provisioner.is_running()

#         # Check that the result is False
#         self.assertFalse(result)

#     def test_get_status(self):
#         # Test that get_status returns the current status
#         self.assertEqual(self.provisioner.get_status(), "not_started")

#         # Change status and check again
#         self.provisioner._status = "running"
#         self.assertEqual(self.provisioner.get_status(), "running")

#         # Change status and check again
#         self.provisioner._status = "stopped"
#         self.assertEqual(self.provisioner.get_status(), "stopped")

#         # Change status and check again
#         self.provisioner._status = "error"
#         self.assertEqual(self.provisioner.get_status(), "error")


# if __name__ == '__main__':
#     unittest.main()
