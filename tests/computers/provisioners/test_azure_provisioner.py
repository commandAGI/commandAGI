import unittest
from unittest.mock import patch, MagicMock, call
import time
import os

from commandLAB.computers.provisioners.azure_provisioner import AzureProvisioner


class TestAzureProvisioner(unittest.TestCase):
    @patch('azure.mgmt.compute.ComputeManagementClient')
    @patch('azure.identity.DefaultAzureCredential')
    def setUp(self, mock_credential, mock_compute_client_cls):
        # Create mock objects
        self.mock_credential = mock_credential.return_value
        self.mock_compute_client = mock_compute_client_cls.return_value
        self.mock_vm_client = MagicMock()
        self.mock_compute_client.virtual_machines = self.mock_vm_client
        
        # Create an AzureProvisioner
        self.provisioner = AzureProvisioner(
            port=8000,
            resource_group="test-rg",
            location="eastus",
            vm_size="Standard_DS1_v2",
            subscription_id="test-subscription",
            image_id="/test/image/id",
            max_retries=2,
            timeout=10
        )
        
        # Store the mocks for later use
        self.mock_compute_client_cls = mock_compute_client_cls
    
    def test_init(self):
        # Test that the provisioner initializes with the correct attributes
        self.assertEqual(self.provisioner.port, 8000)
        self.assertEqual(self.provisioner.resource_group, "test-rg")
        self.assertEqual(self.provisioner.location, "eastus")
        self.assertEqual(self.provisioner.vm_size, "Standard_DS1_v2")
        self.assertEqual(self.provisioner.vm_name, "commandlab-daemon")
        self.assertEqual(self.provisioner.subscription_id, "test-subscription")
        self.assertEqual(self.provisioner.image_id, "/test/image/id")
        self.assertEqual(self.provisioner.max_retries, 2)
        self.assertEqual(self.provisioner.timeout, 10)
        self.assertEqual(self.provisioner._status, "not_started")
    
    def test_init_with_env_var(self):
        # Test initialization with subscription_id from environment variable
        with patch.dict(os.environ, {"AZURE_SUBSCRIPTION_ID": "env-subscription"}):
            # Create a provisioner without explicitly setting subscription_id
            provisioner = AzureProvisioner(
                resource_group="test-rg",
                location="eastus"
            )
            
            # Check that subscription_id was set from the environment variable
            self.assertEqual(provisioner.subscription_id, "env-subscription")
    
    def test_init_missing_subscription_id(self):
        # Test that initialization fails if subscription_id is not provided
        with patch.dict(os.environ, {}, clear=True):  # Clear environment variables
            # Check that creating a provisioner without subscription_id raises ValueError
            with self.assertRaises(ValueError):
                AzureProvisioner(resource_group="test-rg", location="eastus")
    
    @patch('time.sleep')
    def test_setup_success(self, mock_sleep):
        # Create a mock poller
        mock_poller = MagicMock()
        mock_poller.done.side_effect = [False, True]  # Not done, then done
        mock_poller.result.return_value = MagicMock()  # VM creation result
        
        # Mock the VM client
        self.mock_vm_client.begin_create_or_update.return_value = mock_poller
        
        # Mock is_running to return True after a delay
        self.provisioner.is_running = MagicMock(side_effect=[False, True])
        
        # Call setup
        self.provisioner.setup()
        
        # Check that begin_create_or_update was called with the right arguments
        self.mock_vm_client.begin_create_or_update.assert_called_once()
        create_args = self.mock_vm_client.begin_create_or_update.call_args
        self.assertEqual(create_args[0][0], "test-rg")  # resource_group
        self.assertEqual(create_args[0][1], "commandlab-daemon")  # vm_name
        
        # Check VM configuration
        vm_config = create_args[0][2]
        self.assertEqual(vm_config['location'], "eastus")
        self.assertEqual(vm_config['hardware_profile']['vm_size'], "Standard_DS1_v2")
        self.assertEqual(vm_config['storage_profile']['image_reference']['id'], "/test/image/id")
        self.assertEqual(vm_config['os_profile']['computer_name'], "commandlab-daemon")
        self.assertEqual(vm_config['os_profile']['admin_username'], "commandlab")
        self.assertIn("custom_data", vm_config['os_profile'])
        
        # Check that poller.done and result were called
        self.assertEqual(mock_poller.done.call_count, 2)
        mock_poller.result.assert_called_once()
        
        # Check that is_running was called
        self.assertEqual(self.provisioner.is_running.call_count, 2)
        
        # Check that sleep was called
        mock_sleep.assert_has_calls([call(10), call(10)])  # Once for poller, once for is_running
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    @patch('time.sleep')
    def test_setup_poller_timeout(self, mock_sleep):
        # Create a mock poller that never completes
        mock_poller = MagicMock()
        mock_poller.done.return_value = False  # Never done
        
        # Mock the VM client
        self.mock_vm_client.begin_create_or_update.return_value = mock_poller
        
        # Mock time.time to simulate timeout
        with patch('time.time', side_effect=[0, 5, 15]):
            # Call setup and check that it raises TimeoutError
            with self.assertRaises(TimeoutError):
                self.provisioner.setup()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('time.sleep')
    def test_setup_is_running_timeout(self, mock_sleep):
        # Create a mock poller that completes
        mock_poller = MagicMock()
        mock_poller.done.return_value = True
        mock_poller.result.return_value = MagicMock()  # VM creation result
        
        # Mock the VM client
        self.mock_vm_client.begin_create_or_update.return_value = mock_poller
        
        # Mock is_running to always return False (timeout)
        self.provisioner.is_running = MagicMock(return_value=False)
        
        # Mock time.time to simulate timeout
        with patch('time.time', side_effect=[0, 5, 15]):
            # Call setup and check that it raises TimeoutError
            with self.assertRaises(TimeoutError):
                self.provisioner.setup()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('time.sleep')
    def test_setup_retry_success(self, mock_sleep):
        # Create a mock poller
        mock_poller = MagicMock()
        mock_poller.done.return_value = True
        mock_poller.result.return_value = MagicMock()  # VM creation result
        
        # Mock the VM client to fail once then succeed
        self.mock_vm_client.begin_create_or_update.side_effect = [
            Exception("Azure error"),
            mock_poller
        ]
        
        # Mock is_running to return True
        self.provisioner.is_running = MagicMock(return_value=True)
        
        # Call setup
        self.provisioner.setup()
        
        # Check that begin_create_or_update was called twice
        self.assertEqual(self.mock_vm_client.begin_create_or_update.call_count, 2)
        
        # Check that sleep was called for retry backoff
        mock_sleep.assert_has_calls([call(2)])  # 2^1
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    @patch('time.sleep')
    def test_setup_max_retries_exceeded(self, mock_sleep):
        # Mock the VM client to always fail
        self.mock_vm_client.begin_create_or_update.side_effect = Exception("Azure error")
        
        # Call setup and check that it raises the Exception
        with self.assertRaises(Exception):
            self.provisioner.setup()
        
        # Check that begin_create_or_update was called max_retries times
        self.assertEqual(self.mock_vm_client.begin_create_or_update.call_count, 2)  # max_retries=2
        
        # Check that sleep was called for retry backoff
        mock_sleep.assert_has_calls([call(2), call(4)])  # 2^1, 2^2
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('time.sleep')
    def test_teardown_success(self, mock_sleep):
        # Create a mock poller
        mock_poller = MagicMock()
        mock_poller.done.side_effect = [False, True]  # Not done, then done
        mock_poller.result.return_value = MagicMock()  # VM deletion result
        
        # Mock the VM client
        self.mock_vm_client.begin_delete.return_value = mock_poller
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that begin_delete was called with the right arguments
        self.mock_vm_client.begin_delete.assert_called_once_with(
            "test-rg",  # resource_group
            "commandlab-daemon"  # vm_name
        )
        
        # Check that poller.done and result were called
        self.assertEqual(mock_poller.done.call_count, 2)
        mock_poller.result.assert_called_once()
        
        # Check that sleep was called
        mock_sleep.assert_called_once_with(10)
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "stopped")
    
    @patch('time.sleep')
    def test_teardown_poller_timeout(self, mock_sleep):
        # Create a mock poller that never completes
        mock_poller = MagicMock()
        mock_poller.done.return_value = False  # Never done
        
        # Mock the VM client
        self.mock_vm_client.begin_delete.return_value = mock_poller
        
        # Mock time.time to simulate timeout
        with patch('time.time', side_effect=[0, 5, 15]):
            # Call teardown and check that it raises TimeoutError
            with self.assertRaises(TimeoutError):
                self.provisioner.teardown()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('time.sleep')
    def test_teardown_error(self, mock_sleep):
        # Mock the VM client to raise an error
        self.mock_vm_client.begin_delete.side_effect = Exception("Azure error")
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that begin_delete was called
        self.mock_vm_client.begin_delete.assert_called_once()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    def test_is_running_true(self):
        # Create a mock VM
        mock_vm = MagicMock()
        mock_vm.instance_view.statuses = [
            MagicMock(code="PowerState/running")
        ]
        
        # Mock the VM client
        self.mock_vm_client.get.return_value = mock_vm
        
        # Check that is_running returns True
        self.assertTrue(self.provisioner.is_running())
        
        # Check that get was called with the right arguments
        self.mock_vm_client.get.assert_called_once_with(
            "test-rg",  # resource_group
            "commandlab-daemon",  # vm_name
            expand='instanceView'
        )
    
    def test_is_running_false(self):
        # Create a mock VM
        mock_vm = MagicMock()
        mock_vm.instance_view.statuses = [
            MagicMock(code="PowerState/deallocated")
        ]
        
        # Mock the VM client
        self.mock_vm_client.get.return_value = mock_vm
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
    
    def test_is_running_error(self):
        # Mock the VM client to raise an error
        self.mock_vm_client.get.side_effect = Exception("Azure error")
        
        # Check that is_running returns False on error
        self.assertFalse(self.provisioner.is_running())
    
    def test_get_status(self):
        # Test that get_status returns the current status
        self.assertEqual(self.provisioner.get_status(), "not_started")
        
        # Change status and check again
        self.provisioner._status = "running"
        self.assertEqual(self.provisioner.get_status(), "running")


if __name__ == '__main__':
    unittest.main() 