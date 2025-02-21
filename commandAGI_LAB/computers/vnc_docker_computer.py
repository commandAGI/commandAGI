import base64
import os
import tempfile
import uuid

try:
    from vncdotool import api
except ImportError:
    raise ImportError("vncdotool is not installed. Please install commandAGI_LAB with the vnc extra:\n\npip install commandAGI_LAB[vnc]")

from commandAGI_LAB.computers.base_docker_computer import BaseDockerComputer
from commandAGI_LAB.types import (KeyboardKey, KeyboardKeyDownAction,
                                KeyboardKeyReleaseAction, KeyboardStateObservation,
                                MouseButton, MouseButtonDownAction,
                                MouseButtonUpAction, MouseMoveAction,
                                MouseScrollAction, MouseStateObservation,
                                ScreenshotObservation, TypeAction)


class VNCDockerComputer(BaseDockerComputer):
    """Base class for Docker-based VNC environments."""

    def __init__(
        self,
        dockerfile_path: str,
        user: str = "root",
        password: str = "secret",
        vnc_port: int = 5900,
        container_name: str = None,
        image_tag: str = None,
    ):
        # Auto-generate container name if not provided
        if container_name is None:
            prefix = os.path.basename(dockerfile_path).split(".")[0]
            container_name = f"{prefix}-{uuid.uuid4().hex[:6]}"

        # Set up ports and environment variables for VNC
        ports = {vnc_port: vnc_port}
        env_vars = {"PASSWORD": password, "USER": user}

        # Use provided image tag or default to vnc_image
        image_tag = image_tag or "vnc_image"

        super().__init__(
            container_name=container_name,
            dockerfile_path=dockerfile_path,
            image_tag=image_tag,
            ports=ports,
            env_vars=env_vars,
        )

        self.password = password
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"
        self.vnc = None
        self._connect_vnc()

    def _connect_vnc(self):
        """Connect to the container's VNC server using vncdotool."""
        self.vnc = api.connect(f"{self.vnc_host}::{self.vnc_port}", password=self.password)

    def get_screenshot(self) -> ScreenshotObservation:
        """Capture a screenshot using VNC and return as base64 string."""
        temp_path = os.path.join(tempfile.mkdtemp(), "temp_screenshot.png")
        self.vnc.captureScreen(temp_path)
        with open(temp_path, "rb") as f:
            b64_screenshot = base64.b64encode(f.read()).decode("utf-8")
        os.remove(temp_path)
        return ScreenshotObservation(screenshot=b64_screenshot)

    def get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state. Override in subclasses if needed."""
        raise NotImplementedError("Mouse state observation not implemented")

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state. Override in subclasses if needed."""
        raise NotImplementedError("Keyboard state observation not implemented")

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
        """Type text using VNC."""
        self.vnc.write(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse using VNC."""
        self.vnc.mouseMove(action.x, action.y)
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse (not supported by vncdotool)."""
        return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button using VNC."""
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using VNC."""
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True

    def close(self):
        """Clean up VNC and Docker resources."""
        try:
            self.vnc.disconnect()
            print("Disconnected from VNC server")
        except Exception as e:
            print(f"Error disconnecting from VNC server: {e}")

        # Call parent's close to cleanup Docker resources
        super().close() 