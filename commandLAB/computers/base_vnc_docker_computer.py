import base64
import os
import tempfile
import uuid

from commandLAB.computers.base_docker_computer import BaseDockerComputer
from commandLAB.computers.computer_types import (KeyboardKey,
                                                    KeyboardKeyDownAction,
                                                    KeyboardKeyReleaseAction,
                                                    KeyboardStateObservation,
                                                    MouseButton,
                                                    MouseButtonDownAction,
                                                    MouseButtonUpAction,
                                                    MouseMoveAction,
                                                    MouseScrollAction,
                                                    ScreenshotObservation,
                                                    TypeAction)
from vncdotool import api


class VNCDockerComputer(BaseDockerComputer):
    def __init__(
        self,
        dockerfile_path,
        user="root",
        password="secret",
        vnc_port=5900,
        container_name=None,
    ):
        # Auto-generate the container name if not provided.
        if container_name is None:
            # Use the Dockerfile name (without extension) as a prefix, then append a short uuid.
            prefix = dockerfile_path.split("/")[-1].split(".")[0]
            container_name = f"{prefix}-{uuid.uuid4().hex[:6]}"
        # Specify ports mapping (host_port:container_port) and necessary environment variables.
        ports = {vnc_port: vnc_port}
        env_vars = {"PASSWORD": password, "USER": user}
        # "lxde_image" is used as the image tag when building the Docker image.
        super().__init__(
            container_name=container_name,
            dockerfile_path=dockerfile_path,
            image_tag="lxde_image",
            ports=ports,
            env_vars=env_vars,
        )
        self.password = password
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"
        self.vnc = None
        self._connect_vnc()

    def _connect_vnc(self):
        """
        Connect to the container's VNC server using vncdotool.
        """
        self.vnc = api.connect(
            f"{self.vnc_host}::{self.vnc_port}", password=self.password
        )

    def get_screenshot(self) -> ScreenshotObservation:
        """Capture a screenshot using the VNC connection and return as base64 string."""
        temp_path = os.path.join(tempfile.mkdtemp(), "temp_screenshot.png")
        self.vnc.captureScreen(temp_path)
        with open(temp_path, "rb") as f:
            b64_screenshot = base64.b64encode(f.read()).decode("utf-8")
        os.remove(temp_path)
        return ScreenshotObservation(screenshot=b64_screenshot)

    def close(self):
        """Clean up VNC and Docker resources.

        Disconnects from the VNC server and cleans up Docker container resources.
        """
        try:
            self.vnc.disconnect()
            print("Disconnected from VNC server")
        except Exception as e:
            print(f"Error disconnecting from VNC server: {e}")

        # Call parent's close to cleanup Docker resources
        super().close()

    def reset(self):
        """
        Reset the environment. For instance, pressing 'Super+d' in LXDE inside
        the Docker container might show the desktop. Adjust to your needs.
        """
        return self.get_observation()

    def get_keyboard_state(self) -> KeyboardStateObservation:
        raise NotImplementedError(
            "DockerLxdeEnv does not support keyboard state observation"
        )

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using VNC."""
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyDown(vnc_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using VNC."""
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
        print(f"Scrolling by amount {action.amount} not implemented in DockerLxdeEnv")
        return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True
