import os
import time

try:
    import docker
except ImportError:
    raise ImportError("docker is not installed. Please install commandLAB with the docker extra:\n\npip install commandLAB[docker]")

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import CommandAction
from docker.errors import DockerException


class BaseDockerComputer(BaseComputer):
    # Class-level shared Docker client
    docker_client: docker.DockerClient

    def __init__(
        self,
        container_name: str,
        dockerfile_path: str,
        image_tag: str = "custom_env",
        ports: dict = None,
        env_vars: dict = None,
    ):
        super().__init__()
        self.container_name = container_name
        self.dockerfile_path = dockerfile_path
        self.image_tag = image_tag
        self.ports = ports if ports is not None else {}
        self.env_vars = env_vars if env_vars is not None else {}
        self.container = None

        try:
            self.docker_client = docker.from_env()
        except DockerException as e:
            raise Exception(f"Failed to initialize Docker client: {e}")

        self._build_docker_image()
        self._start_container()

    def _build_docker_image(self, force_rebuild: bool = False):
        if not force_rebuild:
            try:
                # Check if image already exists
                self.docker_client.images.get(self.image_tag)
                print(f"Docker image {self.image_tag} already exists, skipping build.")
                return
            except docker.errors.ImageNotFound:
                pass
            except Exception as e:
                raise Exception(f"Failed to check if image exists: {e}")

        # Image doesn't exist, proceed with build
        # Get build context directory (containing Dockerfile)
        context_dir = os.path.dirname(self.dockerfile_path)
        dockerfile_name = os.path.basename(self.dockerfile_path)

        try:
            print(f"Building docker image {self.image_tag}...")
            image, logs = self.docker_client.images.build(
                path=context_dir,
                dockerfile=dockerfile_name,
                tag=self.image_tag,
                rm=True,  # Remove intermediate containers
            )
            print("Docker image built successfully.")
            return image
        except DockerException as e:
            raise Exception(f"Docker build failed: {e}")

    def _start_container(self):
        # Remove existing container if it exists
        try:
            old_container = self.docker_client.containers.get(self.container_name)
            old_container.remove(force=True)
            print(f"Removed existing container: {self.container_name}")
        except docker.errors.NotFound:
            pass

        try:
            # Convert ports dict to Docker format
            port_bindings = {
                f"{container}/tcp": host for host, container in self.ports.items()
            }

            self.container = self.docker_client.containers.run(
                self.image_tag,
                name=self.container_name,
                detach=True,
                ports=port_bindings,
                environment=self.env_vars,
                remove=True,  # Auto-remove when stopped
            )
            print(f"Started container: {self.container_name}")

            # Allow time for container to initialize
            time.sleep(5)
        except DockerException as e:
            raise Exception(f"Failed to start container: {e}")

    def run_command_in_container(
        self, cmd: str, timeout: int = 10
    ) -> docker.models.containers.ExecResult:
        """
        Executes a command inside the container and returns the ExecResult.
        """
        try:
            exec_result = self.container.exec_run(
                cmd, tty=True, stdin=True, privileged=True
            )
            return exec_result
        except DockerException as e:
            print(f"Error executing command in container: {e}")
            raise e

    def execute_command_in_container(self, cmd: str, timeout: int = 10) -> bool:
        result = self.run_command_in_container(
            cmd, **({"timeout": timeout} if timeout else {})
        )
        return result.exit_code == 0

    def close(self):
        """Clean up Docker resources.

        Stops and removes the container if it exists, and closes the Docker client connection.
        Handles race conditions and retries for container cleanup.
        """
        if self.container:
            try:
                # Try to stop the container first
                try:
                    self.container.stop(timeout=10)
                    print(f"Stopped container: {self.container_name}")
                except docker.errors.NotFound:
                    print(f"Container {self.container_name} already stopped")
                except docker.errors.APIError as e:
                    print(f"Error stopping container: {e}")

                # Wait a moment for the container to fully stop
                time.sleep(2)

                # Try to remove the container with retries
                max_retries = 3
                retry_delay = 2
                for attempt in range(max_retries):
                    try:
                        self.container.remove(force=True)
                        print(f"Removed container: {self.container_name}")
                        break
                    except docker.errors.NotFound:
                        print(f"Container {self.container_name} already removed")
                        break
                    except docker.errors.APIError as e:
                        if attempt < max_retries - 1:
                            print(
                                f"Retry {attempt + 1}/{max_retries}: Error removing container: {e}"
                            )
                            time.sleep(retry_delay)
                        else:
                            print(f"Final attempt failed to remove container: {e}")
            except Exception as e:
                print(f"Unexpected error during container cleanup: {e}")

        try:
            self.docker_client.close()
            print("Closed Docker client connection")
        except Exception as e:
            print(f"Error closing Docker client: {e}")

        super().close()

    def execute_command(self, action: CommandAction) -> bool:
        # Delegate to parent's container command executor.
        return self.execute_command_in_container(action.command)
