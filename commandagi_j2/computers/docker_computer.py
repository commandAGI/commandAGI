from typing import Optional
import time
import uuid
import docker
from docker.errors import DockerException, ImageNotFound

from commandagi_j2.computers.base_computer import Computer
from commandagi_j2.envs.computer_types import (
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)

class DockerComputer(Computer):
    """Base class for Docker-based computer implementations."""
    
    def __init__(
        self,
        dockerfile_path: str,
        container_name: Optional[str] = None,
        image_tag: str = "docker_computer",
        ports: dict = None,
        env_vars: dict = None,
    ):
        if container_name is None:
            prefix = dockerfile_path.split('/')[-1].split('.')[0]
            container_name = f"{prefix}-{uuid.uuid4().hex[:6]}"
            
        self.dockerfile_path = dockerfile_path
        self.container_name = container_name
        self.image_tag = image_tag
        self.ports = ports if ports is not None else {}
        self.env_vars = env_vars if env_vars is not None else {}

        try:
            self.docker_client = docker.from_env()
        except DockerException as e:
            raise Exception(f"Failed to initialize Docker client: {e}")

        self._build_docker_image()
        self._start_container()

    def _build_docker_image(self, force_rebuild: bool = False):
        """Build the Docker image if it doesn't exist or force_rebuild is True."""
        if not force_rebuild:
            try:
                self.docker_client.images.get(self.image_tag)
                print(f"Docker image {self.image_tag} exists, skipping build.")
                return
            except ImageNotFound:
                pass
            except Exception as e:
                raise Exception(f"Failed to check if image exists: {e}")

        context_dir = "/".join(self.dockerfile_path.split('/')[:-1])
        dockerfile_name = self.dockerfile_path.split('/')[-1]

        try:
            print(f"Building docker image {self.image_tag}...")
            self.docker_client.images.build(
                path=context_dir,
                dockerfile=dockerfile_name,
                tag=self.image_tag,
                rm=True,
            )
            print("Docker image built successfully.")
        except DockerException as e:
            raise Exception(f"Docker build failed: {e}")

    def _start_container(self):
        """Start the Docker container with the specified configuration."""
        try:
            # Remove existing container if it exists
            try:
                old_container = self.docker_client.containers.get(self.container_name)
                old_container.remove(force=True)
                print(f"Removed existing container: {self.container_name}")
            except docker.errors.NotFound:
                pass

            port_bindings = {
                f"{container_port}/tcp": host_port 
                for host_port, container_port in self.ports.items()
            }

            self.container = self.docker_client.containers.run(
                self.image_tag,
                name=self.container_name,
                detach=True,
                ports=port_bindings,
                environment=self.env_vars,
                remove=True,
            )
            print(f"Started container: {self.container_name}")
            time.sleep(5)  # Allow container to initialize
        except DockerException as e:
            raise Exception(f"Failed to start container: {e}")

    def execute_command(self, action: CommandAction) -> bool:
        """Execute a command in the Docker container."""
        try:
            exec_result = self.container.exec_run(
                action.command,
                tty=True,
                stdin=True,
                **({"timeout": action.timeout} if action.timeout else {})
            )
            return exec_result.exit_code == 0
        except Exception as e:
            print(f"Error executing command in container: {e}")
            return False

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        """Not implemented in base Docker computer."""
        return None

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        """Not implemented in base Docker computer."""
        return None

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        """Not implemented in base Docker computer."""
        return None

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Not implemented in base Docker computer."""
        return False

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Not implemented in base Docker computer."""
        return False

    def execute_type(self, action: TypeAction) -> bool:
        """Not implemented in base Docker computer."""
        return False

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Not implemented in base Docker computer."""
        return False

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Not implemented in base Docker computer."""
        return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Not implemented in base Docker computer."""
        return False

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Not implemented in base Docker computer."""
        return False

    def close(self):
        """Clean up Docker resources."""
        try:
            if hasattr(self, 'container'):
                try:
                    self.container.stop(timeout=10)
                    print(f"Stopped container: {self.container_name}")
                except Exception as e:
                    print(f"Error stopping container: {e}")

            if hasattr(self, 'docker_client'):
                self.docker_client.close()
                print("Closed Docker client connection")
        except Exception as e:
            print(f"Error during cleanup: {e}") 