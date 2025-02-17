import os
import subprocess
import time
from commandagi_j2.envs.base_computer_env import BaseComputerEnv


class BaseDockerComputerEnv(BaseComputerEnv):
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
        self.container_id = None

        self._build_docker_image()
        self._start_container()

    def _build_docker_image(self):
        # The build context is the directory containing the Dockerfile
        context_dir = os.path.dirname(self.dockerfile_path)
        build_cmd = (
            f"docker build -t {self.image_tag} -f {self.dockerfile_path} {context_dir}"
        )
        print(f"Building docker image with command: {build_cmd}")
        result = subprocess.run(
            build_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise Exception(f"Docker build failed: {result.stderr.decode('utf-8')}")
        print("Docker image built successfully.")

    def _start_container(self):
        # Remove any existing container with the same name
        subprocess.run(
            f"docker rm -f {self.container_name}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Prepare port mappings (format: "-p host:container")
        port_str = " ".join(
            [f"-p {host}:{container}" for host, container in self.ports.items()]
        )
        # Prepare environment variables (format: "-e KEY=VALUE")
        env_str = " ".join(
            [f"-e {key}={value}" for key, value in self.env_vars.items()]
        )

        run_cmd = f"docker run -d --name {self.container_name} {port_str} {env_str} {self.image_tag}"
        print(f"Starting docker container with command: {run_cmd}")
        result = subprocess.run(
            run_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise Exception(f"Failed to run container: {result.stderr.decode('utf-8')}")
        self.container_id = result.stdout.decode("utf-8").strip()
        # Allow time for the container to be fully up and running.
        time.sleep(5)

    def run_command_in_container(
        self, cmd: str, timeout: int = 10
    ) -> subprocess.CompletedProcess:
        """
        Executes a command inside the container and returns the CompletedProcess object.
        """
        full_cmd = f"docker exec {self.container_name} {cmd}"
        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            return result
        except Exception as e:
            print(f"Error executing command in container: {e}")
            raise e

    def execute_command_in_container(self, cmd: str) -> bool:
        result = self.run_command_in_container(cmd, timeout=10)
        return result.returncode == 0

    def close(self):
        subprocess.run(f"docker rm -f {self.container_name}", shell=True)
