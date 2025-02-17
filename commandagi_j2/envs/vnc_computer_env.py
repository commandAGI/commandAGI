import os
import tempfile
from vncdotool import api
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
from commandagi_j2.envs.computer_types import (
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    KeyboardKey,
)


class VNCComputerEnv(BaseComputerEnv):
    """Environment for VNC connections to arbitrary hardware."""

    def __init__(self, host: str, port: int, password: str = ""):
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self._connect_vnc()

    def _connect_vnc(self):
        self.vnc = api.connect(f"{self.host}::{self.port}", password=self.password)

    def get_screenshot(self) -> ScreenshotObservation:
        screenshot_path = os.path.join(tempfile.mkdtemp(), "vnc_screenshot.png")
        self.vnc.captureScreen(screenshot_path)
        return ScreenshotObservation(screenshot=screenshot_path)

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
        from commandagi_j2.envs.computer_types import MouseButton

        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        from commandagi_j2.envs.computer_types import MouseButton

        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True
