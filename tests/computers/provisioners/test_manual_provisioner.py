import unittest
from unittest.mock import patch, MagicMock

from commandLAB.computers.provisioners.manual_provisioner import ManualProvisioner


class TestManualProvisioner(unittest.TestCase):
    def setUp(self):
        # Create a ManualProvisioner with default parameters
        self.provisioner = ManualProvisioner(
            port=8000,
            host="localhost"
        )
    
    def test_init(self):
        # Test that the provisioner initializes with the correct attributes
        self.assertEqual(self.provisioner.port, 8000)
        self.assertEqual(self.provisioner.host, "localhost")
        self.assertEqual(self.provisioner._status, "not_started")
    
    def test_init_with_custom_params(self):
        # Test initialization with custom parameters
        provisioner = ManualProvisioner(
            port=9000,
            host="192.168.1.100"
        )
        
        self.assertEqual(provisioner.port, 9000)
        self.assertEqual(provisioner.host, "192.168.1.100")
        self.assertEqual(provisioner._status, "not_started")
    
    def test_setup(self):
        # Call setup
        self.provisioner.setup()
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "running")
    
    def test_teardown(self):
        # Set status to running
        self.provisioner._status = "running"
        
        # Call teardown
        self.provisioner.teardown()
        
        # Check that status was updated
        self.assertEqual(self.provisioner._status, "stopped")
    
    def test_is_running_true(self):
        # Set status to running
        self.provisioner._status = "running"
        
        # Check that is_running returns True
        self.assertTrue(self.provisioner.is_running())
    
    def test_is_running_false(self):
        # Set status to not_started
        self.provisioner._status = "not_started"
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
        
        # Set status to stopped
        self.provisioner._status = "stopped"
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
        
        # Set status to error
        self.provisioner._status = "error"
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
    
    def test_get_status(self):
        # Test that get_status returns the current status
        self.assertEqual(self.provisioner.get_status(), "not_started")
        
        # Change status and check again
        self.provisioner._status = "running"
        self.assertEqual(self.provisioner.get_status(), "running")
        
        # Change status and check again
        self.provisioner._status = "stopped"
        self.assertEqual(self.provisioner.get_status(), "stopped")
        
        # Change status and check again
        self.provisioner._status = "error"
        self.assertEqual(self.provisioner.get_status(), "error")
    
    @patch('socket.socket')
    def test_check_connection_success(self, mock_socket):
        # Mock socket.socket to return a successful connection
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        # Call check_connection
        result = self.provisioner.check_connection()
        
        # Check that socket.socket was called
        mock_socket.assert_called_once()
        
        # Check that connect was called with the right arguments
        mock_socket_instance.connect.assert_called_once_with(("localhost", 8000))
        
        # Check that close was called
        mock_socket_instance.close.assert_called_once()
        
        # Check that the result is True
        self.assertTrue(result)
    
    @patch('socket.socket')
    def test_check_connection_error(self, mock_socket):
        # Mock socket.socket to raise an error on connect
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect.side_effect = Exception("Connection error")
        mock_socket.return_value = mock_socket_instance
        
        # Call check_connection
        result = self.provisioner.check_connection()
        
        # Check that socket.socket was called
        mock_socket.assert_called_once()
        
        # Check that connect was called with the right arguments
        mock_socket_instance.connect.assert_called_once_with(("localhost", 8000))
        
        # Check that close was called
        mock_socket_instance.close.assert_called_once()
        
        # Check that the result is False
        self.assertFalse(result)
    
    @patch.object(ManualProvisioner, 'check_connection')
    def test_is_running_with_check_connection_true(self, mock_check_connection):
        # Mock check_connection to return True
        mock_check_connection.return_value = True
        
        # Set status to running
        self.provisioner._status = "running"
        
        # Check that is_running returns True
        self.assertTrue(self.provisioner.is_running())
        
        # Check that check_connection was called
        mock_check_connection.assert_called_once()
    
    @patch.object(ManualProvisioner, 'check_connection')
    def test_is_running_with_check_connection_false(self, mock_check_connection):
        # Mock check_connection to return False
        mock_check_connection.return_value = False
        
        # Set status to running
        self.provisioner._status = "running"
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
        
        # Check that check_connection was called
        mock_check_connection.assert_called_once()
    
    @patch.object(ManualProvisioner, 'check_connection')
    def test_is_running_not_running_status(self, mock_check_connection):
        # Set status to not_started
        self.provisioner._status = "not_started"
        
        # Check that is_running returns False
        self.assertFalse(self.provisioner.is_running())
        
        # Check that check_connection was not called
        mock_check_connection.assert_not_called()


if __name__ == '__main__':
    unittest.main() 