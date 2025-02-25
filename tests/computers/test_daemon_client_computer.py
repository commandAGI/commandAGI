import unittest
from unittest.mock import patch, MagicMock

from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandLAB.types import (
    ClickAction,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    KeyboardKey,
    MouseButton
)


class TestDaemonClientComputer(unittest.TestCase):
    @patch('commandLAB.computers.daemon_client_computer.requests')
    @patch('commandLAB.computers.provisioners.manual_provisioner.ManualProvisioner')
    def setUp(self, mock_provisioner_cls, mock_requests):
        # Create a mock provisioner
        self.mock_provisioner = mock_provisioner_cls.return_value
        
        # Create a mock response
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"success": True}
        mock_requests.post.return_value = self.mock_response
        mock_requests.get.return_value = self.mock_response
        
        # Create a DaemonClientComputer
        self.computer = DaemonClientComputer(
            daemon_base_url="http://localhost",
            daemon_port=8000,
            provisioning_method=ProvisioningMethod.MANUAL
        )
        
        # Store the mock objects for later use
        self.mock_requests = mock_requests
        self.mock_provisioner_cls = mock_provisioner_cls
    
    def test_init(self):
        # Test that the computer initializes with the correct attributes
        self.assertEqual(self.computer.daemon_base_url, "http://localhost")
        self.assertEqual(self.computer.daemon_port, 8000)
        self.assertEqual(self.computer.provisioner, self.mock_provisioner)
        
        # Check that the provisioner was set up
        self.mock_provisioner.setup.assert_called_once()
    
    def test_close(self):
        # Test that close calls teardown on the provisioner
        self.computer.close()
        self.mock_provisioner.teardown.assert_called_once()
    
    def test_get_endpoint_url(self):
        # Test that _get_endpoint_url returns the correct URL
        url = self.computer._get_endpoint_url("test")
        self.assertEqual(url, "http://localhost:8000/test")
        
        # Test with a different base URL and port
        self.computer.daemon_base_url = "https://example.com"
        self.computer.daemon_port = 9000
        url = self.computer._get_endpoint_url("another/test")
        self.assertEqual(url, "https://example.com:9000/another/test")
    
    def test_get_screenshot(self):
        # Set up the mock response for get_screenshot
        self.mock_response.json.return_value = {"screenshot": "base64_data"}
        
        # Call get_screenshot
        screenshot = self.computer.get_screenshot()
        
        # Check that requests.get was called with the correct URL
        self.mock_requests.get.assert_called_with("http://localhost:8000/screenshot")
        
        # Check that the response was parsed correctly
        self.assertIsInstance(screenshot, ScreenshotObservation)
        self.assertEqual(screenshot.screenshot, "base64_data")
    
    def test_get_mouse_state(self):
        # Set up the mock response for get_mouse_state
        self.mock_response.json.return_value = {
            "buttons": {
                MouseButton.LEFT: False,
                MouseButton.RIGHT: False,
                MouseButton.MIDDLE: False
            },
            "position": [100, 200]
        }
        
        # Call get_mouse_state
        mouse_state = self.computer.get_mouse_state()
        
        # Check that requests.get was called with the correct URL
        self.mock_requests.get.assert_called_with("http://localhost:8000/mouse/state")
        
        # Check that the response was parsed correctly
        self.assertIsInstance(mouse_state, MouseStateObservation)
        self.assertEqual(mouse_state.position, [100, 200])
        self.assertEqual(mouse_state.buttons[MouseButton.LEFT], False)
    
    def test_get_keyboard_state(self):
        # Set up the mock response for get_keyboard_state
        self.mock_response.json.return_value = {
            "keys": {
                KeyboardKey.SHIFT: False,
                KeyboardKey.CTRL: False,
                KeyboardKey.ALT: False
            }
        }
        
        # Call get_keyboard_state
        keyboard_state = self.computer.get_keyboard_state()
        
        # Check that requests.get was called with the correct URL
        self.mock_requests.get.assert_called_with("http://localhost:8000/keyboard/state")
        
        # Check that the response was parsed correctly
        self.assertIsInstance(keyboard_state, KeyboardStateObservation)
        self.assertEqual(keyboard_state.keys[KeyboardKey.SHIFT], False)
    
    def test_execute_command(self):
        # Create a command action
        command = CommandAction(command="ls -la", timeout=5)
        
        # Call execute_command
        result = self.computer.execute_command(command)
        
        # Check that requests.post was called with the correct URL and data
        self.mock_requests.post.assert_called_with(
            "http://localhost:8000/command",
            json=command.model_dump()
        )
        
        # Check that the result is True (status_code == 200)
        self.assertTrue(result)
        
        # Test with a failed response
        self.mock_response.status_code = 500
        result = self.computer.execute_command(command)
        self.assertFalse(result)
    
    def test_execute_keyboard_key_down(self):
        # Create a keyboard key down action
        action = KeyboardKeyDownAction(key=KeyboardKey.SHIFT)
        
        # Call execute_keyboard_key_down
        result = self.computer.execute_keyboard_key_down(action)
        
        # Check that requests.post was called with the correct URL and data
        self.mock_requests.post.assert_called_with(
            "http://localhost:8000/keyboard/key/down",
            json=action.model_dump()
        )
        
        # Check that the result is True (status_code == 200)
        self.assertTrue(result)
    
    def test_execute_keyboard_key_release(self):
        # Create a keyboard key release action
        action = KeyboardKeyReleaseAction(key=KeyboardKey.SHIFT)
        
        # Call execute_keyboard_key_release
        result = self.computer.execute_keyboard_key_release(action)
        
        # Check that requests.post was called with the correct URL and data
        self.mock_requests.post.assert_called_with(
            "http://localhost:8000/keyboard/key/release",
            json=action.model_dump()
        )
        
        # Check that the result is True (status_code == 200)
        self.assertTrue(result)
    
    def test_execute_mouse_move(self):
        # Create a mouse move action
        action = MouseMoveAction(x=100, y=200, move_duration=0.5)
        
        # Call execute_mouse_move
        result = self.computer.execute_mouse_move(action)
        
        # Check that requests.post was called with the correct URL and data
        self.mock_requests.post.assert_called_with(
            "http://localhost:8000/mouse/move",
            json=action.model_dump()
        )
        
        # Check that the result is True (status_code == 200)
        self.assertTrue(result)
    
    def test_execute_mouse_scroll(self):
        # Create a mouse scroll action
        action = MouseScrollAction(amount=10)
        
        # Call execute_mouse_scroll
        result = self.computer.execute_mouse_scroll(action)
        
        # Check that requests.post was called with the correct URL and data
        self.mock_requests.post.assert_called_with(
            "http://localhost:8000/mouse/scroll",
            json=action.model_dump()
        )
        
        # Check that the result is True (status_code == 200)
        self.assertTrue(result)
    
    def test_execute_mouse_button_down(self):
        # Create a mouse button down action
        action = MouseButtonDownAction(button=MouseButton.LEFT)
        
        # Call execute_mouse_button_down
        result = self.computer.execute_mouse_button_down(action)
        
        # Check that requests.post was called with the correct URL and data
        self.mock_requests.post.assert_called_with(
            "http://localhost:8000/mouse/button/down",
            json=action.model_dump()
        )
        
        # Check that the result is True (status_code == 200)
        self.assertTrue(result)
    
    def test_execute_mouse_button_up(self):
        # Create a mouse button up action
        action = MouseButtonUpAction(button=MouseButton.LEFT)
        
        # Call execute_mouse_button_up
        result = self.computer.execute_mouse_button_up(action)
        
        # Check that requests.post was called with the correct URL and data
        self.mock_requests.post.assert_called_with(
            "http://localhost:8000/mouse/button/up",
            json=action.model_dump()
        )
        
        # Check that the result is True (status_code == 200)
        self.assertTrue(result)
    
    @patch('commandLAB.computers.daemon_client_computer.ProvisioningMethod.get_provisioner_cls')
    def test_provisioning_method(self, mock_get_provisioner_cls):
        # Create a mock provisioner class
        mock_provisioner_cls = MagicMock()
        mock_provisioner = MagicMock()
        mock_provisioner_cls.return_value = mock_provisioner
        mock_get_provisioner_cls.return_value = mock_provisioner_cls
        
        # Create a DaemonClientComputer with a different provisioning method
        computer = DaemonClientComputer(
            provisioning_method=ProvisioningMethod.DOCKER,
            platform="local"
        )
        
        # Check that get_provisioner_cls was called with the right method
        mock_get_provisioner_cls.assert_called_once()
        
        # Check that the provisioner was created with the right arguments
        mock_provisioner_cls.assert_called_once_with(port=8000)
        
        # Check that the provisioner was set up
        mock_provisioner.setup.assert_called_once()


if __name__ == '__main__':
    unittest.main() 