import os
import tempfile
from vncdotool import api
from commandagi_j2.envs.kubernetes_computer_env import KubernetesComputerEnv
from commandagi_j2.envs.computer_types import (
    ScreenshotObservation,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    MouseMoveAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)


class VNCKubernetesComputerEnv(KubernetesComputerEnv):
    """
    Kubernetes environment with VNC capabilities.
    This class extends KubernetesComputerEnv and adds support for VNC-based screenshot capture and input actions.
    """

    def __init__(
        self,
        pod_name: str,
        image: str,
        namespace: str = "default",
        vnc_port: int = 5900,
        user: str = "root",
        password: str = "secret",
        env_vars: dict = None,
        ports: dict = None,
    ):
        super().__init__(pod_name, image, namespace, env_vars, ports)
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"  # Assumes port-forwarding is set up to map the pod's VNC port to localhost
        self.password = password
        self._connect_vnc()

    def _connect_vnc(self):
        self.vnc = api.connect(
            f"{self.vnc_host}::{self.vnc_port}", password=self.password
        )

    def get_screenshot(self) -> ScreenshotObservation:
        screenshot_path = os.path.join(tempfile.mkdtemp(), "vnc_screenshot.png")
        self.vnc.captureScreen(screenshot_path)
        return ScreenshotObservation(screenshot=screenshot_path)

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyDown(vnc_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyUp(vnc_key)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        self.vnc.mouseMove(action.x, action.y)
        return True

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
