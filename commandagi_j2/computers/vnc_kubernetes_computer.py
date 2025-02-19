import os
import tempfile
import base64
import time
import subprocess
from typing import Optional

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
    MouseStateObservation,
    KeyboardStateObservation,
)

class VNCKubernetesComputer(Computer):
    """
    Computer implementation using a Kubernetes pod with VNC capabilities.
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
        self.pod_name = pod_name
        self.image = image
        self.namespace = namespace
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"  # Assumes port-forwarding is set up externally
        self.user = user
        self.password = password
        self.env_vars = env_vars if env_vars is not None else {}
        self.ports = ports if ports is not None else {}
        self._create_pod()
        self._wait_for_pod_ready()
        self._connect_vnc()

    def _create_pod(self):
        cmd = [
            "kubectl", "run", self.pod_name, "--image", self.image,
            "--restart", "Never", "-n", self.namespace
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise Exception(f"Failed to create pod: {result.stderr.decode('utf-8')}")

    def _wait_for_pod_ready(self, timeout: int = 60):
        start_time = time.time()
        while True:
            cmd = [
                "kubectl", "get", "pod", self.pod_name, "-n", self.namespace,
                "-o", "jsonpath={.status.phase}"
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status = result.stdout.decode("utf-8").strip()
            if status == "Running":
                break
            if time.time() - start_time > timeout:
                raise Exception(f"Timeout waiting for pod {self.pod_name} to be running.")
            time.sleep(2)

    def _connect_vnc(self):
        self.vnc = api.connect(f"{self.vnc_host}::{self.vnc_port}", password=self.password)

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        temp_path = os.path.join(tempfile.mkdtemp(), "temp_screenshot.png")
        self.vnc.captureScreen(temp_path)
        with open(temp_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")
        os.remove(temp_path)
        return ScreenshotObservation(screenshot=b64_img)

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        """VNC doesn't support mouse state observation"""
        return None

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        """VNC doesn't support keyboard state observation"""
        return None

    def execute_command(self, action: CommandAction) -> bool:
        full_cmd = [
            "kubectl", "exec", self.pod_name, "-n", self.namespace, "--"
        ] + action.command.split()
        result = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=action.timeout if action.timeout is not None else 10
        )
        return result.returncode == 0

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
            cmd = [
                "kubectl", "delete", "pod", self.pod_name, "-n", self.namespace,
                "--grace-period=0", "--force"
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"Error deleting pod: {e}") 