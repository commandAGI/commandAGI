import os
import platform
import subprocess
import logging
import base64
import io
import datetime
from enum import Enum
from typing import Optional, Dict, Any, Union, Literal

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseStateObservation,
    KeyboardStateObservation,
    ScreenshotObservation,
    KeyboardKey,
    MouseButton,
)
from commandLAB.computers.provisioners.base_provisioner import BaseComputerProvisioner
from commandLAB._utils.config import APPDIR
from commandLAB._utils.screenshot import process_screenshot, base64_to_image

# Import the proper client classes
try:
    from commandLAB.daemon.client import AuthenticatedClient
    from commandLAB.daemon.client.api.default.execute_command_execute_command_post import sync as execute_command_sync
    from commandLAB.daemon.client.api.default.execute_keyboard_key_down_execute_keyboard_key_down_post import sync as execute_keyboard_key_down_sync
    from commandLAB.daemon.client.api.default.execute_keyboard_key_release_execute_keyboard_key_release_post import sync as execute_keyboard_key_release_sync
    from commandLAB.daemon.client.api.default.execute_keyboard_key_press_execute_keyboard_key_press_post import sync as execute_keyboard_key_press_sync
    from commandLAB.daemon.client.api.default.execute_keyboard_hotkey_execute_keyboard_hotkey_post import sync as execute_keyboard_hotkey_sync
    from commandLAB.daemon.client.api.default.execute_type_execute_type_post import sync as execute_type_sync
    from commandLAB.daemon.client.api.default.execute_mouse_move_execute_mouse_move_post import sync as execute_mouse_move_sync
    from commandLAB.daemon.client.api.default.execute_mouse_scroll_execute_mouse_scroll_post import sync as execute_mouse_scroll_sync
    from commandLAB.daemon.client.api.default.execute_mouse_button_down_execute_mouse_button_down_post import sync as execute_mouse_button_down_sync
    from commandLAB.daemon.client.api.default.execute_mouse_button_up_execute_mouse_button_up_post import sync as execute_mouse_button_up_sync
    from commandLAB.daemon.client.api.default.get_observation_observation_get import sync as get_observation_sync
    from commandLAB.daemon.client.api.default.get_screenshot_observation_screenshot_get import sync as get_screenshot_sync
    from commandLAB.daemon.client.api.default.get_mouse_state_observation_mouse_state_get import sync as get_mouse_state_sync
    from commandLAB.daemon.client.api.default.get_keyboard_state_observation_keyboard_state_get import sync as get_keyboard_state_sync
    from commandLAB.daemon.client.api.default.reset_reset_post import sync as reset_sync
    from commandLAB.daemon.client.models import (
        CommandAction as ClientCommandAction,
        KeyboardKeyDownAction as ClientKeyboardKeyDownAction,
        KeyboardKeyReleaseAction as ClientKeyboardKeyReleaseAction,
        KeyboardKeyPressAction as ClientKeyboardKeyPressAction,
        KeyboardHotkeyAction as ClientKeyboardHotkeyAction,
        TypeAction as ClientTypeAction,
        MouseMoveAction as ClientMouseMoveAction,
        MouseScrollAction as ClientMouseScrollAction,
        MouseButtonDownAction as ClientMouseButtonDownAction,
        MouseButtonUpAction as ClientMouseButtonUpAction,
        KeyboardKey as ClientKeyboardKey,
        MouseButton as ClientMouseButton,
    )
except ImportError:
    raise ImportError(
        "commandLAB daemon client is not installed. Please install commandLAB with the daemon extra:\n\npip install commandLAB[daemon-client-all] (or one of the other `daemon-client-*` extras)"
    )

try:
    from PIL import Image
except ImportError:
    pass  # PIL is optional for DaemonClientComputer

# Daemon client-specific mappings
def keyboard_key_to_daemon(key: Union[KeyboardKey, str]) -> ClientKeyboardKey:
    """Convert KeyboardKey to Daemon client KeyboardKey.
    
    The daemon client uses its own KeyboardKey enum that should match our KeyboardKey values.
    This function ensures proper conversion between the two.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)
    
    # The daemon client's KeyboardKey enum should have the same values as our KeyboardKey enum
    # We just need to convert to the client's enum type
    try:
        return ClientKeyboardKey(key.value)
    except ValueError:
        # If the key value doesn't exist in the client's enum, use a fallback
        logging.warning(f"Key {key} not found in daemon client KeyboardKey enum, using fallback")
        return ClientKeyboardKey.ENTER  # Use a safe default

def mouse_button_to_daemon(button: Union[MouseButton, str]) -> ClientMouseButton:
    """Convert MouseButton to Daemon client MouseButton.
    
    The daemon client uses its own MouseButton enum that should match our MouseButton values.
    This function ensures proper conversion between the two.
    """
    if isinstance(button, str):
        button = MouseButton(button)
    
    # The daemon client's MouseButton enum should have the same values as our MouseButton enum
    # We just need to convert to the client's enum type
    try:
        return ClientMouseButton(button.value)
    except ValueError:
        # If the button value doesn't exist in the client's enum, use a fallback
        logging.warning(f"Button {button} not found in daemon client MouseButton enum, using fallback")
        return ClientMouseButton.LEFT  # Use a safe default

class DaemonClientComputer(BaseComputer):
    provisioner: Optional[BaseComputerProvisioner] = None
    client: Optional[AuthenticatedClient] = None
    logger: logging.Logger

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        daemon_base_url: str,
        daemon_port: int,
        daemon_token: str,
        provisioner: BaseComputerProvisioner,
    ):
        super().__init__()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Store the provisioner
        self.provisioner = provisioner
        self.daemon_base_url = daemon_base_url
        self.daemon_port = daemon_port
        self.daemon_token = daemon_token

        # Setup the provisioner
        self.logger.info(f"Starting MCP and FastAPI daemon services at {daemon_base_url}:{daemon_port}")
        self.provisioner.setup()

        # Create the authenticated client
        self.client = AuthenticatedClient(
            base_url=f"{self.daemon_base_url}:{self.daemon_port}",
            token=self.daemon_token
        )
        self.logger.info(f"Successfully connected to daemon services")

    def _start(self):
        """Start the daemon services"""
        if not self.client:
            self.logger.info(f"Starting MCP and FastAPI daemon services at {self.daemon_base_url}:{self.daemon_port}")
            self.provisioner.setup()
            
            # Create the authenticated client
            self.client = AuthenticatedClient(
                base_url=f"{self.daemon_base_url}:{self.daemon_port}",
                token=self.daemon_token
            )
            self.logger.info(f"Successfully connected to daemon services")
        return True

    def _stop(self):
        """Stop the daemon services"""
        if self.client:
            self.logger.info("Shutting down MCP and FastAPI daemon services")
            self.provisioner.teardown()
            self.client = None
            self.logger.info("MCP and FastAPI daemon services successfully stopped")
        return True

    def reset_state(self) -> bool:
        """Reset the computer state"""
        return super().reset_state()

    def get_observation(self) -> Dict[str, Any]:
        """Get a complete observation of the computer state"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        response = get_observation_sync(client=self.client)
        return response if response else {}

    def _get_screenshot(self, display_id: int = 0, format: Literal['base64', 'PIL', 'path'] = 'PIL') -> ScreenshotObservation:
        """Get a screenshot of the computer in the specified format.
        
        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        # Get the screenshot from the daemon (usually returns base64)
        response = get_screenshot_sync(client=self.client)
        if not response or 'screenshot' not in response:
            return ScreenshotObservation()
        
        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=response['screenshot'],
            output_format=format,
            input_format='base64',
            computer_name="daemon"
        )

    def _get_mouse_state(self) -> MouseStateObservation:
        """Get the current mouse state"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        response = get_mouse_state_sync(client=self.client)
        if response:
            return MouseStateObservation(**response)
        return MouseStateObservation()

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Get the current keyboard state"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        response = get_keyboard_state_sync(client=self.client)
        if response:
            return KeyboardStateObservation(**response)
        return KeyboardStateObservation()

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a shell command on the computer"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer CommandAction to the client's CommandAction
        client_action = ClientCommandAction(
            command=action.command,
            timeout=action.timeout
        )
        
        response = execute_command_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Press down a keyboard key"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer KeyboardKeyDownAction to the client's KeyboardKeyDownAction
        client_action = ClientKeyboardKeyDownAction(
            key=keyboard_key_to_daemon(action.key)
        )
        
        response = execute_keyboard_key_down_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Release a keyboard key"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer KeyboardKeyReleaseAction to the client's KeyboardKeyReleaseAction
        client_action = ClientKeyboardKeyReleaseAction(
            key=keyboard_key_to_daemon(action.key)
        )
        
        response = execute_keyboard_key_release_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Press and release a keyboard key"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer KeyboardKeyPressAction to the client's KeyboardKeyPressAction
        client_action = ClientKeyboardKeyPressAction(
            key=keyboard_key_to_daemon(action.key),
            duration=action.duration
        )
        
        response = execute_keyboard_key_press_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey (multiple keys pressed simultaneously)"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer KeyboardHotkeyAction to the client's KeyboardHotkeyAction
        client_action = ClientKeyboardHotkeyAction(
            keys=[keyboard_key_to_daemon(k) for k in action.keys]
        )
        
        response = execute_keyboard_hotkey_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text on the keyboard"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer TypeAction to the client's TypeAction
        client_action = ClientTypeAction(
            text=action.text
        )
        
        response = execute_type_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move the mouse to a position"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer MouseMoveAction to the client's MouseMoveAction
        client_action = ClientMouseMoveAction(
            x=action.x,
            y=action.y,
            move_duration=action.move_duration
        )
        
        response = execute_mouse_move_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll the mouse wheel"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer MouseScrollAction to the client's MouseScrollAction
        client_action = ClientMouseScrollAction(
            amount=action.amount
        )
        
        response = execute_mouse_scroll_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press down a mouse button"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer MouseButtonDownAction to the client's MouseButtonDownAction
        client_action = ClientMouseButtonDownAction(
            button=mouse_button_to_daemon(action.button) if action.button else None
        )
        
        response = execute_mouse_button_down_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release a mouse button"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        # Convert the BaseComputer MouseButtonUpAction to the client's MouseButtonUpAction
        client_action = ClientMouseButtonUpAction(
            button=mouse_button_to_daemon(action.button) if action.button else None
        )
        
        response = execute_mouse_button_up_sync(client=self.client, body=client_action)
        return response is not None and response.get("success", False)
