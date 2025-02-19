import subprocess
import time
from typing import Optional

from commandagi_j2.computers.base_computer import Computer
from commandagi_j2.envs.computer_types import (
    CommandAction,
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
)

class KubernetesComputer(Computer):
    """
    Computer implementation for Kubernetes pods.
    Only command execution is supported; other interactions are not provided.
    """

    def __init__(self, pod_name: str, image: str, namespace: str = "default"):
        self.pod_name = pod_name
        self.image = image
        self.namespace = namespace
        self._create_pod()
        self._wait_for_pod_ready()

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

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        raise NotImplementedError("KubernetesComputer does not support screenshot observation.")

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        raise NotImplementedError("KubernetesComputer does not support mouse state observation.")

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        raise NotImplementedError("KubernetesComputer does not support keyboard state observation.")

    def execute_command(self, action: CommandAction) -> bool:
        full_cmd = [
            "kubectl", "exec", self.pod_name, "-n", self.namespace, "--"
        ] + action.command.split()
        result = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=action.timeout if action.timeout is not None else 10)
        return result.returncode == 0

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        raise NotImplementedError("KubernetesComputer does not support keyboard interactions.")

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        raise NotImplementedError("KubernetesComputer does not support keyboard interactions.")

    def execute_type(self, action: TypeAction) -> bool:
        raise NotImplementedError("KubernetesComputer does not support typing interactions.")

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        raise NotImplementedError("KubernetesComputer does not support mouse interactions.")

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        raise NotImplementedError("KubernetesComputer does not support mouse interactions.")

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        raise NotImplementedError("KubernetesComputer does not support mouse interactions.")

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        raise NotImplementedError("KubernetesComputer does not support mouse interactions.")

    def close(self):
        try:
            cmd = [
                "kubectl", "delete", "pod", self.pod_name, "-n", self.namespace,
                "--grace-period=0", "--force"
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"Error cleaning up pod: {e}") 