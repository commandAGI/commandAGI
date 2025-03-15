import unittest
from unittest.mock import patch, MagicMock
import secrets

from fastapi.testclient import TestClient
from commandAGI.daemon.server import ComputerDaemon
from commandAGI.types import (
    ShellCommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardKeyPressAction,
    KeyboardHotkeyAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    KeyboardKey,
    MouseButton,
)


class TestComputerDaemon(unittest.TestCase):
    @patch("secrets.token_urlsafe")
    def setUp(self, mock_token_urlsafe):
        # Mock the token generation to return a predictable token
        mock_token_urlsafe.return_value = "test_token"

        # Create a mock computer class
        self.mock_computer = MagicMock()
        self.mock_computer_cls = MagicMock(return_value=self.mock_computer)

        # Create the daemon
        self.daemon = ComputerDaemon(computer_cls=self.mock_computer_cls)

        # Create a test client
        self.client = TestClient(self.daemon._fastapi_server)

        # Store the mock token for later use
        self.token = "test_token"

    def test_init(self):
        # Test that the daemon initializes with the correct attributes
        self.assertEqual(self.daemon.API_TOKEN, "test_token")
        self.assertEqual(self.daemon._computer_cls, self.mock_computer_cls)
        self.assertEqual(self.daemon._computer_cls_kwargs, {})
        self.assertIsNone(self.daemon._computer)

        # Test with computer_cls_kwargs
        daemon = ComputerDaemon(
            computer_cls=self.mock_computer_cls,
            computer_cls_kwargs={"test_arg": "test_value"},
        )
        self.assertEqual(daemon._computer_cls_kwargs, {"test_arg": "test_value"})

    def test_get_computer(self):
        # Test that get_computer returns the computer instance
        computer = self.daemon.get_computer()
        self.assertEqual(computer, self.mock_computer)

        # Test that get_computer only creates the computer once
        self.mock_computer_cls.reset_mock()
        computer = self.daemon.get_computer()
        self.mock_computer_cls.assert_not_called()

    def test_reset_endpoint(self):
        # Test the reset endpoint
        response = self.client.post(
            "/reset", headers={"Authorization": f"Bearer {self.token}"}
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that reset was called on the computer
        self.mock_computer.reset.assert_called_once()

    def test_execute_command_endpoint(self):
        # Test the execute_command endpoint
        command = ShellCommandAction(command="ls -la")
        response = self.client.post(
            "/execute/command",
            json=command.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that execute_command was called on the computer with the right action
        self.mock_computer.execute_command.assert_called_once()
        call_args = self.mock_computer.execute_command.call_args[0][0]
        self.assertEqual(call_args.command, "ls -la")

    def test_keydown_endpoint(self):
        # Test the keydown endpoint
        action = KeyboardKeyDownAction(key=KeyboardKey.SHIFT)
        response = self.client.post(
            "/execute/keyboard/key_down",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that keydown was called on the computer with the right action
        self.mock_computer.keydown.assert_called_once()
        call_args = self.mock_computer.keydown.call_args[0][0]
        self.assertEqual(call_args.key, KeyboardKey.SHIFT)

    def test_keyup_endpoint(self):
        # Test the keyup endpoint
        action = KeyboardKeyReleaseAction(key=KeyboardKey.SHIFT)
        response = self.client.post(
            "/execute/keyboard/key_release",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that keyup was called on the computer with the right action
        self.mock_computer.keyup.assert_called_once()
        call_args = self.mock_computer.keyup.call_args[0][0]
        self.assertEqual(call_args.key, KeyboardKey.SHIFT)

    def test_keypress_endpoint(self):
        # Test the keypress endpoint
        action = KeyboardKeyPressAction(key=KeyboardKey.ENTER, duration=0.5)
        response = self.client.post(
            "/execute/keyboard/key_press",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that keypress was called on the computer with the right action
        self.mock_computer.keypress.assert_called_once()
        call_args = self.mock_computer.keypress.call_args[0][0]
        self.assertEqual(call_args.key, KeyboardKey.ENTER)
        self.assertEqual(call_args.duration, 0.5)

    def test_hotkey_endpoint(self):
        # Test the hotkey endpoint
        action = KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S])
        response = self.client.post(
            "/execute/keyboard/hotkey",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that hotkey was called on the computer with the right action
        self.mock_computer.hotkey.assert_called_once()
        call_args = self.mock_computer.hotkey.call_args[0][0]
        self.assertEqual(call_args.keys, [KeyboardKey.CTRL, KeyboardKey.S])

    def test_type_endpoint(self):
        # Test the type endpoint
        action = TypeAction(text="Hello, commandAGI!")
        response = self.client.post(
            "/execute/type",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that type was called on the computer with the right action
        self.mock_computer.type.assert_called_once()
        call_args = self.mock_computer.type.call_args[0][0]
        self.assertEqual(call_args.text, "Hello, commandAGI!")

    def test_move_endpoint(self):
        # Test the move endpoint
        action = MouseMoveAction(x=100, y=200, move_duration=0.5)
        response = self.client.post(
            "/execute/mouse/move",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that move was called on the computer with the right action
        self.mock_computer.move.assert_called_once()
        call_args = self.mock_computer.move.call_args[0][0]
        self.assertEqual(call_args.x, 100)
        self.assertEqual(call_args.y, 200)
        self.assertEqual(call_args.move_duration, 0.5)

    def test_scroll_endpoint(self):
        # Test the scroll endpoint
        action = MouseScrollAction(amount=10)
        response = self.client.post(
            "/execute/mouse/scroll",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that scroll was called on the computer with the right action
        self.mock_computer.scroll.assert_called_once()
        call_args = self.mock_computer.scroll.call_args[0][0]
        self.assertEqual(call_args.amount, 10)

    def test_mouse_down_endpoint(self):
        # Test the mouse_down endpoint
        action = MouseButtonDownAction(button=MouseButton.LEFT)
        response = self.client.post(
            "/execute/mouse/button_down",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that mouse_down was called on the computer with the right action
        self.mock_computer.mouse_down.assert_called_once()
        call_args = self.mock_computer.mouse_down.call_args[0][0]
        self.assertEqual(call_args.button, MouseButton.LEFT)

    def test_mouse_up_endpoint(self):
        # Test the mouse_up endpoint
        action = MouseButtonUpAction(button=MouseButton.LEFT)
        response = self.client.post(
            "/execute/mouse/button_up",
            json=action.model_dump(),
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that mouse_up was called on the computer with the right action
        self.mock_computer.mouse_up.assert_called_once()
        call_args = self.mock_computer.mouse_up.call_args[0][0]
        self.assertEqual(call_args.button, MouseButton.LEFT)

    def test_get_observation_endpoint(self):
        # Test the get_observation endpoint
        response = self.client.get(
            "/observation", headers={"Authorization": f"Bearer {self.token}"}
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that get_observation was called on the computer
        self.mock_computer.get_observation.assert_called_once()

    def test_authentication(self):
        # Test that endpoints require authentication
        response = self.client.post("/reset")
        self.assertEqual(response.status_code, 403)

        # Test with an invalid token
        response = self.client.post(
            "/reset", headers={"Authorization": "Bearer invalid_token"}
        )
        self.assertEqual(response.status_code, 403)

        # Test with the correct token
        response = self.client.post(
            "/reset", headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
