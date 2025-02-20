import base64
import os
import tempfile

from commandAGI_LAB.computers.base_computer import BaseComputer
from commandAGI_LAB.computers.computer_types import (KeyboardKey,
                                                    KeyboardKeyDownAction,
                                                    KeyboardKeyReleaseAction,
                                                    KeyboardStateObservation,
                                                    MouseButtonDownAction,
                                                    MouseButtonUpAction,
                                                    MouseMoveAction,
                                                    MouseScrollAction,
                                                    MouseStateObservation,
                                                    ScreenshotObservation,
                                                    TypeAction)
from vncdotool import api


class VNCComputer(BaseComputer):
    """Environment for VNC connections to arbitrary hardware."""

    def __init__(self, host: str, port: int, password: str = ""):
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.vnc = None
        self._connect_vnc()

    def _connect_vnc(self):
        self.vnc = api.connect(f"{self.host}::{self.port}", password=self.password)

    def get_screenshot(self) -> ScreenshotObservation:
        temp_path = os.path.join(tempfile.mkdtemp(), "temp_screenshot.png")
        self.vnc.captureScreen(temp_path)
        with open(temp_path, "rb") as f:
            b64_screenshot = base64.b64encode(f.read()).decode("utf-8")
        os.remove(temp_path)
        return ScreenshotObservation(screenshot=b64_screenshot)

    def get_mouse_state(self) -> MouseStateObservation:
        raise NotImplementedError(
            "VNCComputerEnv does not support mouse state observation."
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        raise NotImplementedError(
            "VNCComputerEnv does not support keyboard state observation."
        )

    def execute_command(self, action):
        raise NotImplementedError("VNCComputerEnv does not support command execution.")

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyDown(vnc_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyUp(vnc_key)
        return True

    def execute_type(self, action: TypeAction) -> bool:
        self.vnc.write(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        self.vnc.mouseMove(action.x, action.y)
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        # Not implemented as vncdotool does not support mouse scroll
        return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        from commandAGI_LAB.computers.computer_types import MouseButton

        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        from commandAGI_LAB.computers.computer_types import MouseButton

        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True

    def close(self):
        """Clean up VNC connection and resources.

        Disconnects from the VNC server and cleans up any resources.
        """
        try:
            self.vnc.disconnect()
            print("Disconnected from VNC server")
        except Exception as e:
            print(f"Error disconnecting from VNC server: {e}")

        super().close()
