import os
import tempfile
import base64
from typing import Optional
from vncdotool import api

from commandagi_j2.computers.base_computer import Computer
from commandagi_j2.envs.computer_types import (
    KeyboardKey,
    MouseButton,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)

class VNCComputer(Computer):
    """Computer implementation using VNC for remote system control"""

    def __init__(self, host: str, port: int, password: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self.vnc = None
        self._connect_vnc()

    def _connect_vnc(self):
        """Connect to VNC server"""
        self.vnc = api.connect(f"{self.host}::{self.port}", password=self.password)

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        """Capture screenshot using VNC and return as base64 string"""
        temp_path = os.path.join(tempfile.mkdtemp(), "temp_screenshot.png")
        self.vnc.captureScreen(temp_path)
        with open(temp_path, "rb") as f:
            b64_screenshot = base64.b64encode(f.read()).decode('utf-8')
        os.remove(temp_path)
        return ScreenshotObservation(screenshot=b64_screenshot)

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        """VNC doesn't support mouse state observation"""
        return None

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        """VNC doesn't support keyboard state observation"""
        return None

    def execute_command(self, action: CommandAction) -> bool:
        """VNC doesn't support direct command execution"""
        return False

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Press down a keyboard key using VNC"""
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyDown(vnc_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Release a keyboard key using VNC"""
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyUp(vnc_key)
        return True

    def execute_type(self, action: TypeAction) -> bool:
        """Type text using VNC"""
        self.vnc.write(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse cursor using VNC"""
        self.vnc.mouseMove(action.x, action.y)
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """VNC doesn't support mouse scrolling"""
        return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button using VNC"""
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using VNC"""
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True

    def close(self):
        """Clean up VNC connection"""
        try:
            self.vnc.disconnect()
        except:
            pass 