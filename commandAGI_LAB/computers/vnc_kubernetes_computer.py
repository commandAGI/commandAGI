import base64
import os
import tempfile

from commandAGI_LAB.computers.base_kubernetes_computer import BaseKubernetesComputer
from commandAGI_LAB.types import (KeyboardKey,
                                                    KeyboardKeyDownAction,
                                                    KeyboardKeyReleaseAction,
                                                    MouseButtonDownAction,
                                                    MouseButtonUpAction,
                                                    MouseMoveAction,
                                                    ScreenshotObservation)
from vncdotool import api


class VNCKubernetesComputer(BaseKubernetesComputer):
    """
    Kubernetes environment with VNC capabilities.
    This class extends BaseKubernetesComputer and adds support for VNC-based screenshot capture and input actions.
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
        # Ensure VNC port is included in the ports mapping
        ports = ports or {}
        ports[vnc_port] = vnc_port
        
        # Add VNC-related environment variables
        env_vars = env_vars or {}
        env_vars.update({
            "VNC_PASSWORD": password,
            "USER": user
        })

        super().__init__(pod_name, image, namespace, env_vars, ports)
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"  # Assumes port-forwarding is set up
        self.password = password
        self.vnc = None
        self._connect_vnc()

    def _connect_vnc(self):
        """Connect to the VNC server running in the pod."""
        self.vnc = api.connect(
            f"{self.vnc_host}::{self.vnc_port}", password=self.password
        )

    def get_screenshot(self) -> ScreenshotObservation:
        temp_path = os.path.join(tempfile.mkdtemp(), "temp_screenshot.png")
        self.vnc.captureScreen(temp_path)
        with open(temp_path, "rb") as f:
            b64_screenshot = base64.b64encode(f.read()).decode("utf-8")
        os.remove(temp_path)
        return ScreenshotObservation(screenshot=b64_screenshot)

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
        from commandAGI_LAB.types import MouseButton
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        from commandAGI_LAB.types import MouseButton
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True

    def close(self):
        """Clean up VNC connection and Kubernetes resources."""
        try:
            self.vnc.disconnect()
            print("Disconnected from VNC server")
        except Exception as e:
            print(f"Error disconnecting from VNC server: {e}")

        # Call parent's close to cleanup Kubernetes resources
        super().close()
