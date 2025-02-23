import subprocess
import time

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
    TypeAction,
)

try:
    import kubernetes
    from kubernetes.stream import stream as Kubernetesstream
except ImportError:
    raise ImportError(
        "kubernetes is not installed. Please install commandLAB with the kubernetes extra:\n\npip install commandLAB[kubernetes]"
    )


class BaseKubernetesComputer(BaseComputer):
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

        # Initialize kubernetes client
        kubernetes.config.load_kube_config()
        self.core_v1 = kubernetes.client.CoreV1Api()

        self._create_pod()
        self._wait_for_pod_ready()

    def _create_pod(self):
        # Convert env_vars to kubernetes format
        env = [
            kubernetes.client.V1EnvVar(name=key, value=str(value))
            for key, value in self.env_vars.items()
        ]

        # Convert ports to kubernetes format
        ports = [
            kubernetes.client.V1ContainerPort(container_port=container_port)
            for container_port in self.ports.values()
        ]

        # Create pod specification
        container = kubernetes.client.V1Container(
            name=self.pod_name, image=self.image, env=env, ports=ports
        )

        pod_spec = kubernetes.client.V1PodSpec(
            containers=[container], restart_policy="Never"
        )

        pod = kubernetes.client.V1Pod(
            metadata=kubernetes.client.V1ObjectMeta(name=self.pod_name), spec=pod_spec
        )

        print(f"Creating Kubernetes pod {self.pod_name}")
        try:
            self.core_v1.create_namespaced_pod(namespace=self.namespace, body=pod)
            print("Pod created successfully.")
        except kubernetes.client.rest.ApiException as e:
            raise Exception(f"Failed to create pod: {e}")

    def _wait_for_pod_ready(self, timeout: int = 60):
        start_time = time.time()
        while True:
            try:
                pod = self.core_v1.read_namespaced_pod(
                    name=self.pod_name, namespace=self.namespace
                )
                if pod.status.phase == "Running":
                    print(f"Pod {self.pod_name} is running.")
                    break
                if time.time() - start_time > timeout:
                    raise Exception(
                        f"Timeout waiting for pod {self.pod_name} to be running. Current status: {pod.status.phase}"
                    )
                print(
                    f"Waiting for pod {self.pod_name} to be running. Current status: {pod.status.phase}"
                )
                time.sleep(2)
            except kubernetes.client.rest.ApiException as e:
                raise Exception(f"Error checking pod status: {e}")

    def _exec_in_pod(self, cmd: str, timeout: int = 10):
        try:
            exec_command = ["/bin/sh", "-c", cmd]
            return kubernetes.stream.stream(
                self.core_v1.connect_get_namespaced_pod_exec,
                self.pod_name,
                self.namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=True,
            )
        except kubernetes.client.rest.ApiException as e:
            print(f"Error executing command in pod: {e}")
            return None

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
        if result is None:
            print("Error executing command: Command execution failed.")
            return False
        return True

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
        """Clean up Kubernetes resources."""
        try:
            self.core_v1.delete_namespaced_pod(
                name=self.pod_name,
                namespace=self.namespace,
                body=kubernetes.client.V1DeleteOptions(
                    grace_period_seconds=0, propagation_policy="Foreground"
                ),
            )
            print(f"Successfully deleted pod {self.pod_name}")
        except kubernetes.client.rest.ApiException as e:
            print(f"Error deleting pod: {e}")
        except Exception as e:
            print(f"Error cleaning up Kubernetes resources: {e}")

        super().close()
