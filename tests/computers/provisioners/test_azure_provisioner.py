# import unittest
# from unittest.mock import patch, MagicMock, call
# import time
# import os
# import sys

# # Add the mocks directory to the path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mocks')))

# from commandAGI.computers.provisioners.azure_provisioner import AzureProvisioner


# class TestAzureProvisioner(unittest.TestCase):
#     @patch('azure.mgmt.compute.ComputeManagementClient')
#     @patch('azure.identity.DefaultAzureCredential')
#     def setUp(self, mock_credential, mock_compute_client_cls):
#         # Create mock objects
#         self.mock_credential = mock_credential.return_value
#         self.mock_compute_client = mock_compute_client_cls.return_value
#         self.mock_vm_client = MagicMock()
#         self.mock_compute_client.virtual_machines = self.mock_vm_client

#         # Create an AzureProvisioner
#         self.provisioner = AzureProvisioner(
#             port=8000,
#             resource_group="test-rg",
#             location="eastus",
#             vm_size="Standard_DS1_v2",
#             subscription_id="test-subscription",
#             image_id="/test/image/id",
#             max_retries=2,
#             timeout=10
#         )

#         # Store the mocks for later use
#         self.mock_compute_client_cls = mock_compute_client_cls

#     def test_init(self):
#         # Test that the provisioner initializes with the correct attributes
#         self.assertEqual(self.provisioner.port, 8000)
#         self.assertEqual(self.provisioner.resource_group, "test-rg")
#         self.assertEqual(self.provisioner.location, "eastus")
#         self.assertEqual(self.provisioner.vm_size, "Standard_DS1_v2")
#         self.assertEqual(self.provisioner.vm_name, "commandagi-daemon")
#         self.assertEqual(self.provisioner.subscription_id, "test-subscription")
#         self.assertEqual(self.provisioner.image_id, "/test/image/id")
#         self.assertEqual(self.provisioner.max_retries, 2)
#         self.assertEqual(self.provisioner.timeout, 10)
#         self.assertEqual(self.provisioner._status, "not_started")

#     def test_init_with_env_var(self):
#         # Test initialization with subscription_id from environment variable
#         with patch.dict('os.environ', {'AZURE_SUBSCRIPTION_ID': 'env-subscription'}):
#             provisioner = AzureProvisioner(
#                 port=8000,
#                 resource_group="test-rg"
#             )
#             self.assertEqual(provisioner.subscription_id, "env-subscription")

#     def test_init_missing_subscription_id(self):
#         # Test that initialization fails if subscription_id is not provided
#         with patch.dict('os.environ', {}, clear=True):
#             with self.assertRaises(ValueError):
#                 AzureProvisioner(port=8000, resource_group="test-rg")

#     @patch('time.sleep')
#     def test_setup_success(self, mock_sleep):
#         # Create a mock poller
#         mock_poller = MagicMock()
#         mock_poller.done.return_value = True
#         self.mock_vm_client.begin_create_or_update.return_value = mock_poller

#         # Mock is_running to return True after one check
#         self.provisioner.is_running = MagicMock(side_effect=[False, True])

#         # Call setup
#         self.provisioner.setup()

#         # Check that begin_create_or_update was called with the right arguments
#         self.mock_vm_client.begin_create_or_update.assert_called_once()
#         args, kwargs = self.mock_vm_client.begin_create_or_update.call_args
#         self.assertEqual(args[0], "test-rg")
#         self.assertEqual(args[1], "commandagi-daemon")

#         # Check that the VM configuration is correct
#         vm_config = args[2]
#         self.assertEqual(vm_config['location'], "eastus")
#         self.assertEqual(vm_config['hardware_profile']['vm_size'], "Standard_DS1_v2")
#         self.assertEqual(vm_config['storage_profile']['image_reference']['id'], "/test/image/id")

#         # Check that is_running was called
#         self.assertEqual(self.provisioner.is_running.call_count, 2)

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch('time.sleep')
#     def test_setup_poller_timeout(self, mock_sleep):
#         # Create a mock poller that never completes
#         mock_poller = MagicMock()
#         mock_poller.done.return_value = False
#         self.mock_vm_client.begin_create_or_update.return_value = mock_poller

#         # Call setup and expect a timeout
#         with self.assertRaises(TimeoutError):
#             self.provisioner.setup()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_setup_is_running_timeout(self, mock_sleep):
#         # Create a mock poller that completes
#         mock_poller = MagicMock()
#         mock_poller.done.return_value = True
#         self.mock_vm_client.begin_create_or_update.return_value = mock_poller

#         # Mock is_running to always return False
#         self.provisioner.is_running = MagicMock(return_value=False)

#         # Call setup and expect a timeout
#         with self.assertRaises(TimeoutError):
#             self.provisioner.setup()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_setup_retry_success(self, mock_sleep):
#         # Create a mock poller
#         mock_poller = MagicMock()
#         mock_poller.done.return_value = True

#         # Mock begin_create_or_update to fail once, then succeed
#         self.mock_vm_client.begin_create_or_update.side_effect = [
#             Exception("Create error"),
#             mock_poller
#         ]

#         # Mock is_running to return True after one check
#         self.provisioner.is_running = MagicMock(side_effect=[False, True])

#         # Call setup
#         self.provisioner.setup()

#         # Check that begin_create_or_update was called twice
#         self.assertEqual(self.mock_vm_client.begin_create_or_update.call_count, 2)

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch('time.sleep')
#     def test_setup_max_retries_exceeded(self, mock_sleep):
#         # Mock the VM client to always fail
#         self.mock_vm_client.begin_create_or_update.side_effect = Exception("Create error")

#         # Call setup and expect an exception
#         with self.assertRaises(Exception):
#             self.provisioner.setup()

#         # Check that begin_create_or_update was called the right number of times
#         self.assertEqual(self.mock_vm_client.begin_create_or_update.call_count, 2)

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_teardown_success(self, mock_sleep):
#         # Create a mock poller
#         mock_poller = MagicMock()
#         mock_poller.done.return_value = True
#         self.mock_vm_client.begin_delete.return_value = mock_poller

#         # Set status to running
#         self.provisioner._status = "running"

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that begin_delete was called with the right arguments
#         self.mock_vm_client.begin_delete.assert_called_once_with(
#             "test-rg",
#             "commandagi-daemon"
#         )

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "stopped")

#     @patch('time.sleep')
#     def test_teardown_poller_timeout(self, mock_sleep):
#         # Create a mock poller that never completes
#         mock_poller = MagicMock()
#         mock_poller.done.return_value = False
#         self.mock_vm_client.begin_delete.return_value = mock_poller

#         # Set status to running
#         self.provisioner._status = "running"

#         # Call teardown and expect a timeout
#         with self.assertRaises(TimeoutError):
#             self.provisioner.teardown()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     @patch('time.sleep')
#     def test_teardown_error(self, mock_sleep):
#         # Mock the VM client to raise an error
#         self.mock_vm_client.begin_delete.side_effect = Exception("Delete error")

#         # Set status to running
#         self.provisioner._status = "running"

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that the status was updated
#         self.assertEqual(self.provisioner._status, "error")

#     def test_is_running_true(self):
#         # Create a mock VM
#         mock_vm = MagicMock()
#         mock_vm.instance_view.statuses = [
#             MagicMock(code="PowerState/running")
#         ]
#         self.mock_vm_client.get.return_value = mock_vm

#         # Call is_running
#         result = self.provisioner.is_running()

#         # Check that get was called with the right arguments
#         self.mock_vm_client.get.assert_called_once_with(
#             "test-rg",
#             "commandagi-daemon",
#             expand='instanceView'
#         )

#         # Check that the result is True
#         self.assertTrue(result)

#     def test_is_running_false(self):
#         # Create a mock VM
#         mock_vm = MagicMock()
#         mock_vm.instance_view.statuses = [
#             MagicMock(code="PowerState/stopped")
#         ]
#         self.mock_vm_client.get.return_value = mock_vm

#         # Call is_running
#         result = self.provisioner.is_running()

#         # Check that the result is False
#         self.assertFalse(result)

#     def test_is_running_error(self):
#         # Mock the VM client to raise an error
#         self.mock_vm_client.get.side_effect = Exception("Get error")

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
