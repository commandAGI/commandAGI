import subprocess
import time
from commandagi_j2.computers.base_computer import BaseComputer
from commandagi_j2.computers.computer_types import (
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


class KubernetesComputer(BaseComputer):
    """
    Environment that creates and manages a Kubernetes Pod for executing commands.
    Note: This environment primarily supports executing commands within a Kubernetes pod.
    Other interactions such as screenshot, keyboard, and mouse operations are not supported and will raise NotImplementedError.
    """

    def __init__(
        self,
        pod_name: str,
        image: str,
        namespace: str = "default",
        env_vars: dict = None,
        ports: dict = None,
    ):
        """
        Initialize the KubernetesComputerEnv.

        :param pod_name: Name of the Kubernetes pod to create.
        :param image: Container image to use for the pod.
        :param namespace: Kubernetes namespace where the pod will be created.
        :param env_vars: Dictionary of environment variables to set in the pod.
        :param ports: Dictionary of port mappings (host_port: container_port), note: port mapping support may be limited.
        """
        super().__init__()
        self.pod_name = pod_name
        self.image = image
        self.namespace = namespace
        self.env_vars = env_vars if env_vars is not None else {}
        self.ports = ports if ports is not None else {}
        self._create_pod()
        self._wait_for_pod_ready()

    def _create_pod(self):
        # Build the kubectl run command
        cmd = [
            "kubectl",
            "run",
            self.pod_name,
            "--image",
            self.image,
            "--restart",
            "Never",
            "-n",
            self.namespace,
        ]

        # Add environment variable flags
        for key, value in self.env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])

        # Add port flag (kubectl run supports --port for single port)
        # If multiple ports specified, choose one arbitrarily (first one)
        if self.ports:
            # Get the first port mapping (host_port: container_port)
            container_port = list(self.ports.values())[0]
            cmd.extend(["--port", str(container_port)])

        print(f"Creating Kubernetes pod with command: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise Exception(f"Failed to create pod: {result.stderr.decode('utf-8')}")
        print("Pod created successfully.")

    def _wait_for_pod_ready(self, timeout: int = 60):
        start_time = time.time()
        while True:
            cmd = [
                "kubectl",
                "get",
                "pod",
                self.pod_name,
                "-n",
                self.namespace,
                "-o",
                "jsonpath={.status.phase}",
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status = result.stdout.decode("utf-8").strip()
            if status == "Running":
                print(f"Pod {self.pod_name} is running.")
                break
            if time.time() - start_time > timeout:
                raise Exception(
                    f"Timeout waiting for pod {self.pod_name} to be running. Current status: {status}"
                )
            print(
                f"Waiting for pod {self.pod_name} to be running. Current status: {status}"
            )
            time.sleep(2)

    def _exec_in_pod(self, cmd: str, timeout: int = 10) -> subprocess.CompletedProcess:
        full_cmd = [
            "kubectl",
            "exec",
            self.pod_name,
            "-n",
            self.namespace,
            "--",
        ] + cmd.split()
        print(f"Executing command in pod: {' '.join(full_cmd)}")
        result = subprocess.run(
            full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
        return result

    def get_screenshot(self) -> ScreenshotObservation:
        raise NotImplementedError(
            "KubernetesComputerEnv does not support screenshot observation."
        )

    def get_mouse_state(self) -> MouseStateObservation:
        raise NotImplementedError(
            "KubernetesComputerEnv does not support mouse state observation."
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        raise NotImplementedError(
            "KubernetesComputerEnv does not support keyboard state observation."
        )

    def execute_command(self, action: CommandAction) -> bool:
        result = self._exec_in_pod(
            action.command, timeout=action.timeout if action.timeout is not None else 10
        )
        if result.returncode != 0:
            print(f"Error executing command: {result.stderr.decode('utf-8')}")
        return result.returncode == 0

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        raise NotImplementedError(
            "KubernetesComputerEnv does not support keyboard interactions."
        )

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        raise NotImplementedError(
            "KubernetesComputerEnv does not support keyboard interactions."
        )

    def execute_type(self, action: TypeAction):
        raise NotImplementedError(
            "KubernetesComputerEnv does not support typing interactions."
        )

    def execute_mouse_move(self, action: MouseMoveAction):
        raise NotImplementedError(
            "KubernetesComputerEnv does not support mouse interactions."
        )

    def execute_mouse_scroll(self, action: MouseScrollAction):
        raise NotImplementedError(
            "KubernetesComputerEnv does not support mouse interactions."
        )

    def execute_mouse_button_down(self, action: MouseButtonDownAction):
        raise NotImplementedError(
            "KubernetesComputerEnv does not support mouse interactions."
        )

    def execute_mouse_button_up(self, action: MouseButtonUpAction):
        raise NotImplementedError(
            "KubernetesComputerEnv does not support mouse interactions."
        )

    def close(self):
        """Clean up Kubernetes resources.
        
        Deletes the pod and cleans up any associated resources.
        """
        try:
            cmd = [
                "kubectl",
                "delete",
                "pod",
                self.pod_name,
                "-n",
                self.namespace,
                "--grace-period=0",
                "--force",
            ]
            print(f"Deleting Kubernetes pod with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                print(f"Successfully deleted pod {self.pod_name}")
            else:
                print(f"Error deleting pod: {result.stderr.decode('utf-8')}")
        except Exception as e:
            print(f"Error cleaning up Kubernetes resources: {e}")
        
        super().close()
