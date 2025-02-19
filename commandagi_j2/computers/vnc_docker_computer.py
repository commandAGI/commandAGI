import os
import time
import tempfile
import base64
import uuid
from typing import Optional

import docker
from docker.errors import DockerException, ImageNotFound
from vncdotool import api

from commandagi_j2.computers.base_computer import Computer
from commandagi_j2.envs.computer_types import (
    ScreenshotObservation,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    KeyboardKey,
    MouseButton,
)
from commandagi_j2.computers.docker_computer import DockerComputer

class VNCDockerComputer(DockerComputer):
    """
    Computer implementation using a Docker container with a VNC interface.
    """
    def __init__(
        self,
        dockerfile_path: str,
        container_name: Optional[str] = None,
        user: str = "root",
        password: str = "secret",
        vnc_port: int = 5900,
        image_tag: str = "vnc_image",
        ports: dict = None,
        env_vars: dict = None,
    ):
        # Set up VNC-specific environment variables
        env_vars = env_vars if env_vars is not None else {}
        env_vars.update({"PASSWORD": password, "USER": user})
        
        # Set up VNC port mapping
        ports = ports if ports is not None else {}
        ports[vnc_port] = vnc_port

        # Initialize base Docker computer
        super().__init__(
            dockerfile_path=dockerfile_path,
            container_name=container_name,
            image_tag=image_tag,
            ports=ports,
            env_vars=env_vars,
        )

        self.vnc_port = vnc_port
        self.vnc_host = "localhost"
        self.password = password

        self._connect_vnc()

    def _connect_vnc(self):
        self.vnc = api.connect(f"{self.vnc_host}::{self.vnc_port}", password=self.password)

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        temp_path = os.path.join(tempfile.mkdtemp(), "temp_screenshot.png")
        self.vnc.captureScreen(temp_path)
        with open(temp_path, "rb") as f:
            b64_scr = base64.b64encode(f.read()).decode("utf-8")
        os.remove(temp_path)
        return ScreenshotObservation(screenshot=b64_scr)

    def get_mouse_state(self):
        # Not implemented (can be extended if needed)
        return None

    def get_keyboard_state(self):
        # Not implemented (can be extended if needed)
        return None

    def execute_command(self, action: CommandAction) -> bool:
        try:
            exec_result = self.container.exec_run(action.command, tty=True, stdin=True)
            return exec_result.exit_code == 0
        except Exception as e:
            print(f"Error executing command in container: {e}")
            return False

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
        # vncdotool does not support scroll in our implementation.
        return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True

    def close(self):
        try:
            self.vnc.disconnect()
        except Exception as e:
            print(f"Error disconnecting VNC: {e}")
        try:
            self.container.stop(timeout=10)
        except Exception as e:
            print(f"Error stopping container: {e}")
        try:
            self.docker_client.close()
        except Exception as e:
            print(f"Error closing docker client: {e}") 