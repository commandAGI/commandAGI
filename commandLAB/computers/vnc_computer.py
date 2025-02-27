import base64
import io
import os
import datetime
from typing import Optional, Union, Literal

try:
    import vncdotool.api as vnc
    from PIL import Image
except ImportError:
    raise ImportError(
        "The VNC dependencies are not installed. Please install commandLAB with the vnc extra:\n\npip install commandLAB[vnc]"
    )

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
    TypeAction,
)
from commandLAB._utils.config import APPDIR
from commandLAB._utils.screenshot import process_screenshot


# VNC-specific mappings
def mouse_button_to_vnc(button: Union[MouseButton, str]) -> int:
    """Convert MouseButton to VNC mouse button code.
    
    VNC uses integers for mouse buttons:
    1 = left button
    2 = middle button
    3 = right button
    4 = wheel up
    5 = wheel down
    """
    if isinstance(button, str):
        button = MouseButton(button)
    
    # VNC mouse button mapping
    vnc_button_mapping = {
        MouseButton.LEFT: 1,
        MouseButton.MIDDLE: 2,
        MouseButton.RIGHT: 3
    }
    
    return vnc_button_mapping.get(button, 1)  # Default to left button if not found

def keyboard_key_to_vnc(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to VNC key name.
    
    VNC uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)
    
    # VNC-specific key mappings
    vnc_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "return",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "escape",
        KeyboardKey.HOME: "home",
        KeyboardKey.END: "end",
        KeyboardKey.PAGE_UP: "page_up",
        KeyboardKey.PAGE_DOWN: "page_down",
        
        # Arrow keys
        KeyboardKey.UP: "up",
        KeyboardKey.DOWN: "down",
        KeyboardKey.LEFT: "left",
        KeyboardKey.RIGHT: "right",
        
        # Modifier keys
        KeyboardKey.SHIFT: "shift",
        KeyboardKey.CTRL: "control",
        KeyboardKey.LCTRL: "control",
        KeyboardKey.RCTRL: "control",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "meta",
        KeyboardKey.LMETA: "meta",
        KeyboardKey.RMETA: "meta",
        
        # Function keys
        KeyboardKey.F1: "f1",
        KeyboardKey.F2: "f2",
        KeyboardKey.F3: "f3",
        KeyboardKey.F4: "f4",
        KeyboardKey.F5: "f5",
        KeyboardKey.F6: "f6",
        KeyboardKey.F7: "f7",
        KeyboardKey.F8: "f8",
        KeyboardKey.F9: "f9",
        KeyboardKey.F10: "f10",
        KeyboardKey.F11: "f11",
        KeyboardKey.F12: "f12",
    }
    
    # For letter keys and number keys, use the value directly
    return vnc_key_mapping.get(key, key.value)


class VNCComputer(BaseComputer):
    """Environment that uses VNC for remote computer interactions"""

    def __init__(self, host: str = "localhost", port: int = 5900, password: Optional[str] = None):
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.client = None

    def _start(self):
        """Start the VNC connection."""
        if not self.client:
            connection_string = f"{self.host}::{self.port}"
            self.logger.info(f"Connecting to VNC server at {connection_string}")
            self.client = vnc.connect(connection_string, password=self.password)
            self.logger.info(f"Successfully connected to VNC server")

    def _stop(self):
        """Stop the VNC connection."""
        if self.client:
            self.logger.info(f"Disconnecting from VNC server")
            self.client.disconnect()
            self.client = None
            self.logger.info(f"Successfully disconnected from VNC server")

    def reset_state(self):
        """Reset the VNC connection"""
        self.logger.info(f"Resetting VNC connection")
        self._stop()
        self._start()

    def _get_screenshot(self, display_id: int = 0, format: Literal['base64', 'PIL', 'path'] = 'PIL') -> ScreenshotObservation:
        """Return a screenshot of the current state in the specified format.
        
        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
            
        # Capture the screenshot using vncdotool
        self.logger.debug(f"Capturing VNC screenshot")
        png_data = self.client.capture()
        
        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=png_data,
            output_format=format,
            input_format='bytes',
            computer_name="vnc"
        )

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from VNC."""
        self.logger.debug("VNC does not support getting mouse state")
        raise NotImplementedError("VNC does not support getting mouse state")

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from VNC."""
        self.logger.debug("VNC does not support getting keyboard state")
        raise NotImplementedError("VNC does not support getting keyboard state")

    def _execute_command(self, action: CommandAction):
        """Execute a system command on the remote system.
        
        Note: This is limited by VNC capabilities and may not work for all commands.
        """
        self.logger.info(f"Executing command via VNC: {action.command}")
        # For VNC, we can try to execute commands by opening a terminal and typing
        # This is a simplified approach and may not work in all environments
        self.client.keyPress('windown')  # Open start menu or equivalent
        self.client.pause(0.5)
        self.client.type('terminal')  # Type 'terminal' to search for terminal
        self.client.pause(0.5)
        self.client.keyPress('enter')  # Open terminal
        self.client.pause(1.0)
        self.client.type(action.command)  # Type the command
        self.client.keyPress('enter')  # Execute the command
        
        # Wait for command to complete if timeout is specified
        if action.timeout is not None:
            self.client.pause(action.timeout)
            
        self.logger.info(f"Command executed successfully")

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        """Execute key down for a keyboard key using VNC."""
        vnc_key = keyboard_key_to_vnc(action.key)
        self.logger.debug(f"Pressing key down: {action.key} (VNC key: {vnc_key})")
        self.client.keyDown(vnc_key)

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        """Execute key release for a keyboard key using VNC."""
        vnc_key = keyboard_key_to_vnc(action.key)
        self.logger.debug(f"Releasing key: {action.key} (VNC key: {vnc_key})")
        self.client.keyUp(vnc_key)

    def _execute_type(self, action: TypeAction):
        """Type text using VNC."""
        self.logger.debug(f"Typing text: {action.text}")
        self.client.type(action.text)

    def _execute_mouse_move(self, action: MouseMoveAction):
        """Move mouse to specified coordinates using VNC."""
        self.logger.debug(f"Moving mouse to: ({action.x}, {action.y})")
        # VNC doesn't have a direct move duration parameter, so we just move
        self.client.mouseMove(action.x, action.y)

    def _execute_mouse_scroll(self, action: MouseScrollAction):
        """Scroll mouse using VNC."""
        self.logger.debug(f"Scrolling mouse by: {action.amount}")
        # VNC scroll is typically done by wheel events
        # Positive values scroll up, negative values scroll down
        if action.amount > 0:
            for _ in range(int(abs(action.amount))):
                self.client.mouseWheel(1)  # Scroll up
        else:
            for _ in range(int(abs(action.amount))):
                self.client.mouseWheel(-1)  # Scroll down

    def _execute_mouse_button_down(self, action: MouseButtonDownAction):
        """Press mouse button down using VNC."""
        vnc_button = mouse_button_to_vnc(action.button)
        self.logger.debug(f"Pressing mouse button down: {action.button} (VNC button: {vnc_button})")
        self.client.mouseDown(vnc_button)

    def _execute_mouse_button_up(self, action: MouseButtonUpAction):
        """Release mouse button using VNC."""
        vnc_button = mouse_button_to_vnc(action.button)
        self.logger.debug(f"Releasing mouse button: {action.button} (VNC button: {vnc_button})")
        self.client.mouseUp(vnc_button)
