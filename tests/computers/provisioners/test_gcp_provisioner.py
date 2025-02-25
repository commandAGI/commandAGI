import unittest
from unittest.mock import patch, MagicMock, call
import time

from commandLAB.computers.provisioners.gcp_provisioner import GCPProvisioner


class TestGCPProvisioner(unittest.TestCase):
    @patch('google.cloud.compute_v1.InstancesClient')
    def setUp(self, mock_instances_client_cls):
        # Create a mock instances client
        self.mock_instances_client = mock_instances_client_cls.return_value
        
        # Create a GCPProvisioner
        self.provisioner = GCPProvisioner(
            port=8000,
            project="test-project",
            zone="us-central1-a",
            machine_type="n1-standard-1",
            source_image="projects/test-project/global/images/test-image",
            max_retries=2,
            timeout=10
        )
        
        # Store the mock for later use
        self.mock_instances_client_cls = mock_instances_client_cls
    
    def test_init(self):
        # Test that the provisioner initializes with the correct attributes
        self.assertEqual(self.provisioner.port, 8000)
        self.assertEqual(self.provisioner.project, "test-project")
        self.assertEqual(self.provisioner.zone, "us-central1-a")
        self.assertEqual(self.provisioner.machine_type, "n1-standard-1")
        self.assertEqual(self.provisioner.instance_name, "commandlab-daemon")
        self.assertEqual(self.provisioner.source_image, "projects/test-project/global/images/test-image")
        self.assertEqual(self.provisioner.max_retries, 2)
        self.assertEqual(self.provisioner.timeout, 10)
        self.assertEqual(self.provisioner._status, "not_started")
        
        # Check that InstancesClient was called
        self.mock_instances_client_cls.assert_called_once()
    
    def test_init_missing_project(self):
        # Test that initialization fails if project is not provided
        with self.assertRaises(ValueError):
            GCPProvisioner(zone="us-central1-a")
    
    @patch('time.sleep')
    def test_setup_success(self, mock_sleep):
        # Create a mock operation
        mock_operation = MagicMock()
        mock_operation.done.side_effect = [False, True]  # Not done, then done
        mock_operation.result.return_value = MagicMock()  # Instance creation result
        
        # Mock the instances client
        self.mock_instances_client.insert.return_value = mock_operation
        
        # Mock is_running to return True after a delay
        self.provisioner.is_running = MagicMock(side_effect=[False, True])
        
        # Call setup
        self.provisioner.setup()
        
        # Check that insert was called with the right arguments
        self.mock_instances_client.insert.assert_called_once()
        insert_args = self.mock_instances_client.insert.call_args
        self.assertEqual(insert_args[1]['project'], "test-project")
        self.assertEqual(insert_args[1]['zone'], "us-central1-a")
        
        # Check instance configuration
        instance = insert_args[1]['instance_resource']
        self.assertEqual(instance.name, "commandlab-daemon")
        self.assertEqual(instance.machine_type, "zones/us-central1-a/machineTypes/n1-standard-1")
        self.assertTrue(instance.disks[0].boot)
        self.assertTrue(instance.disks[0].auto_delete)
        self.assertEqual(instance.disks[0].initialize_params.source_image, 
                         "projects/test-project/global/images/test-image")
        self.assertEqual(instance.network_interfaces[0].name, "global/networks/default")
        self.assertIn("startup-script", [item.key for item in instance.metadata.items])
        
        # Check that operation.done and result were called
        self.assertEqual(mock_operation.done.call_count, 2)
        mock_operation.result.assert_called_once()
        
        # Check that is_running was called
        self.assertEqual(self.provisioner.is_running.call_count, 2)
        
        # Check that sleep was called
        mock_sleep.assert_has_calls([call(10), call(10)])  # Once for operation, once for is_running
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    @patch('time.sleep')
    def test_setup_operation_timeout(self, mock_sleep):
        # Create a mock operation that never completes
        mock_operation = MagicMock()
        mock_operation.done.return_value = False  # Never done
        
        # Mock the instances client
        self.mock_instances_client.insert.return_value = mock_operation
        
        # Mock time.time to simulate timeout
        with patch('time.time', side_effect=[0, 5, 15]):
            # Call setup and check that it raises TimeoutError
            with self.assertRaises(TimeoutError):
                self.provisioner.setup()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('time.sleep')
    def test_setup_is_running_timeout(self, mock_sleep):
        # Create a mock operation that completes
        mock_operation = MagicMock()
        mock_operation.done.return_value = True
        mock_operation.result.return_value = MagicMock()  # Instance creation result
        
        # Mock the instances client
        self.mock_instances_client.insert.return_value = mock_operation
        
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
        # Create a mock operation
        mock_operation = MagicMock()
        mock_operation.done.return_value = True
        mock_operation.result.return_value = MagicMock()  # Instance creation result
        
        # Mock the instances client to fail once then succeed
        self.mock_instances_client.insert.side_effect = [
            Exception("GCP error"),
            mock_operation
        ]
        
        # Mock is_running to return True
        self.provisioner.is_running = MagicMock(return_value=True)
        
        # Call setup
        self.provisioner.setup()
        
        # Check that insert was called twice
        self.assertEqual(self.mock_instances_client.insert.call_count, 2)
        
        # Check that sleep was called for retry backoff
        mock_sleep.assert_has_calls([call(2)])  # 2^1
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    @patch('time.sleep')
    def test_setup_max_retries_exceeded(self, mock_sleep):
        # Mock the instances client to always fail
        self.mock_instances_client.insert.side_effect = Exception("GCP error")
        
        # Call setup and check that it raises the Exception
        with self.assertRaises(Exception):
            self.provisioner.setup()
        
        # Check that insert was called max_retries times
        self.assertEqual(self.mock_instances_client.insert.call_count, 2)  # max_retries=2
        
        # Check that sleep was called for retry backoff
        mock_sleep.assert_has_calls([call(2), call(4)])  # 2^1, 2^2
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('time.sleep')
    def test_teardown_success(self, mock_sleep):
        # Create a mock operation
        mock_operation = MagicMock()
        mock_operation.done.side_effect = [False, True]  # Not done, then done
        mock_operation.result.return_value = MagicMock()  # Instance deletion result
        
        # Mock the instances client
        self.mock_instances_client.delete.return_value = mock_operation
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that delete was called with the right arguments
        self.mock_instances_client.delete.assert_called_once_with(
            project="test-project",
            zone="us-central1-a",
            instance="commandlab-daemon"
        )
        
        # Check that operation.done and result were called
        self.assertEqual(mock_operation.done.call_count, 2)
        mock_operation.result.assert_called_once()
        
        # Check that sleep was called
        mock_sleep.assert_called_once_with(10)
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "stopped")
    
    @patch('time.sleep')
    def test_teardown_operation_timeout(self, mock_sleep):
        # Create a mock operation that never completes
        mock_operation = MagicMock()
        mock_operation.done.return_value = False  # Never done
        
        # Mock the instances client
        self.mock_instances_client.delete.return_value = mock_operation
        
        # Mock time.time to simulate timeout
        with patch('time.time', side_effect=[0, 5, 15]):
            # Call teardown and check that it raises TimeoutError
            with self.assertRaises(TimeoutError):
                self.provisioner.teardown()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    @patch('time.sleep')
    def test_teardown_error(self, mock_sleep):
        # Mock the instances client to raise an error
        self.mock_instances_client.delete.side_effect = Exception("GCP error")
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that delete was called
        self.mock_instances_client.delete.assert_called_once()
        
        # Check that status was updated to error
        self.assertEqual(self.provisioner._status, "error")
    
    def test_is_running_true(self):
        # Create a mock instance
        mock_instance = MagicMock()
        mock_instance.status = "RUNNING"
        
        # Mock the instances client
        self.mock_instances_client.get.return_value = mock_instance
        
        # Check that is_running returns True
        self.assertTrue(self.provisioner.is_running())
        
        # Check that get was called with the right arguments
        self.mock_instances_client.get.assert_called_once_with(
            project="test-project",
            zone="us-central1-a",
            instance="commandlab-daemon"
        )
    
    def test_is_running_false(self):
        # Create a mock instance
        mock_instance = MagicMock()
        mock_instance.status = "TERMINATED"
        
        # Mock the instances client
        self.mock_instances_client.get.return_value = mock_instance
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
    
    def test_is_running_error(self):
        # Mock the instances client to raise an error
        self.mock_instances_client.get.side_effect = Exception("GCP error")
        
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