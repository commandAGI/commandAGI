import base64
import io
from typing import Optional

try:
    import vncdotool.api as vnc
    from PIL import Image
except ImportError:
    raise ImportError(
        "vncdotool and Pillow are not installed. Please install commandLAB with the vnc extra:\n\npip install commandLAB[vnc]"
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


class VNCComputer(BaseComputer):
    """Environment that uses VNC for remote computer interactions"""

    def __init__(self, host: str = "localhost", port: int = 5900, password: Optional[str] = None):
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.client = None
        self._start()

    def _start(self):
        """Start the VNC connection."""
        if not self.client:
            connection_string = f"{self.host}::{self.port}"
            self.client = vnc.connect(connection_string, password=self.password)
        return True

    def _stop(self):
        """Stop the VNC connection."""
        if self.client:
            self.client.disconnect()
            self.client = None
        return True

    def reset_state(self):
        """Reset the VNC connection"""
        self._stop()
        self._start()

    def _get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        if not self.client:
            self._start()
            
        # Capture the screenshot using vncdotool
        png_data = self.client.capture()
        
        # Convert the PNG data to a base64 string
        b64_screenshot = base64.b64encode(png_data).decode("utf-8")
        return ScreenshotObservation(screenshot=b64_screenshot)

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from VNC."""
        raise NotImplementedError("VNC does not support getting mouse state")

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from VNC."""
        raise NotImplementedError("VNC does not support getting keyboard state")

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command on the remote system.
        
        Note: This is limited by VNC capabilities and may not work for all commands.
        """
        try:
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
                
            return True
        except Exception as e:
            print(f"Error executing command via VNC: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using VNC."""
        try:
            vnc_key = KeyboardKey.to_vnc(action.key)
            self.client.keyDown(vnc_key)
            return True
        except Exception as e:
            print(f"Error executing key down via VNC: {e}")
            return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using VNC."""
        try:
            vnc_key = KeyboardKey.to_vnc(action.key)
            self.client.keyUp(vnc_key)
            return True
        except Exception as e:
            print(f"Error executing key release via VNC: {e}")
            return False

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using VNC."""
        try:
            self.client.type(action.text)
            return True
        except Exception as e:
            print(f"Error typing text via VNC: {e}")
            return False

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using VNC."""
        try:
            # VNC doesn't have a direct move duration parameter, so we just move
            self.client.mouseMove(action.x, action.y)
            return True
        except Exception as e:
            print(f"Error moving mouse via VNC: {e}")
            return False

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using VNC."""
        try:
            # VNC scroll is typically done by wheel events
            # Positive values scroll up, negative values scroll down
            if action.amount > 0:
                for _ in range(int(abs(action.amount))):
                    self.client.mouseWheel(1)  # Scroll up
            else:
                for _ in range(int(abs(action.amount))):
                    self.client.mouseWheel(-1)  # Scroll down
            return True
        except Exception as e:
            print(f"Error scrolling mouse via VNC: {e}")
            return False

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using VNC."""
        try:
            vnc_button = MouseButton.to_vnc(action.button)
            self.client.mouseDown(vnc_button)
            return True
        except Exception as e:
            print(f"Error pressing mouse button via VNC: {e}")
            return False

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using VNC."""
        try:
            vnc_button = MouseButton.to_vnc(action.button)
            self.client.mouseUp(vnc_button)
            return True
        except Exception as e:
            print(f"Error releasing mouse button via VNC: {e}")
            return False
