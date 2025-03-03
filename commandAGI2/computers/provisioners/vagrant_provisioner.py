import os
import subprocess
import time
import logging
from typing import Optional
from pathlib import Path
from .base_provisioner import BaseComputerProvisioner

logger = logging.getLogger(__name__)


class VagrantProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        port: int = 8000,
        box_name: str = "generic/ubuntu2004",
        vagrant_file_path: str = "./vagrant",
        provider: str = "virtualbox",
        max_retries: int = 3,
        timeout: int = 300,  # 5 minutes
    ):
        super().__init__(port)
        self.box_name = box_name
        self.vagrant_file_path = vagrant_file_path
        self.provider = provider
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"

    def setup(self) -> None:
        """Setup a Vagrant VM and start the daemon."""
        self._status = "starting"
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Create Vagrantfile if it doesn't exist
                self._create_vagrantfile()

                # Start the VM
                logger.info(f"Starting Vagrant VM with box {self.box_name}")
                self._vagrant_command(["up", f"--provider={self.provider}"])

                # Wait for VM to be running
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(f"Vagrant VM is now running")
                        return
                    time.sleep(5)

                # If we get here, the VM didn't start in time
                self._status = "error"
                logger.error(f"Timeout waiting for Vagrant VM to start")
                raise TimeoutError(f"Timeout waiting for Vagrant VM to start")

            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    logger.error(
                        f"Failed to start Vagrant VM after {self.max_retries} attempts: {e}"
                    )
                    raise
                logger.warning(
                    f"Error starting Vagrant VM, retrying ({retry_count}/{self.max_retries}): {e}"
                )
                time.sleep(2**retry_count)  # Exponential backoff

    def teardown(self) -> None:
        """Stop and destroy the Vagrant VM."""
        self._status = "stopping"
        logger.info(f"Stopping Vagrant VM")

        try:
            # Halt the VM
            self._vagrant_command(["halt", "-f"])

            # Destroy the VM
            self._vagrant_command(["destroy", "-f"])

            self._status = "stopped"
            logger.info(f"Vagrant VM stopped and destroyed")
        except Exception as e:
            self._status = "error"
            logger.error(f"Error stopping Vagrant VM: {e}")

    def is_running(self) -> bool:
        """Check if the Vagrant VM is running."""
        if self._status != "running":
            return False

        try:
            # Get VM status
            result = self._vagrant_command(["status"], capture_output=True)
            return "running" in result.lower()
        except Exception as e:
            logger.error(f"Error checking Vagrant VM status: {e}")
            return False

    def _vagrant_command(
        self, args: list, capture_output: bool = False
    ) -> Optional[str]:
        """Run a vagrant command."""
        cmd = ["vagrant"] + args
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            # Change to the Vagrant directory
            cwd = os.getcwd()
            os.makedirs(self.vagrant_file_path, exist_ok=True)
            os.chdir(self.vagrant_file_path)

            # Run the command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=capture_output,
                text=True if capture_output else False,
            )

            # Change back to the original directory
            os.chdir(cwd)

            if capture_output:
                return result.stdout
            return None
        except subprocess.CalledProcessError as e:
            # Change back to the original directory
            os.chdir(cwd)
            logger.error(f"Vagrant command failed: {e}")
            raise

    def _create_vagrantfile(self) -> None:
        """Create a Vagrantfile if it doesn't exist."""
        vagrantfile_path = Path(self.vagrant_file_path) / "Vagrantfile"

        if os.path.exists(vagrantfile_path):
            logger.debug(f"Vagrantfile already exists at {vagrantfile_path}")
            return

        logger.info(f"Creating Vagrantfile at {vagrantfile_path}")

        vagrantfile_content = f"""
Vagrant.configure("2") do |config|
  config.vm.box = "{self.box_name}"
  config.vm.network "forwarded_port", guest: {self.port}, host: {self.port}
  
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y python3-pip
    pip3 install commandagi2[local,daemon]
    python3 -m commandagi2.daemon.daemon --port {self.port} --backend pynput
  SHELL
end
"""

        with open(vagrantfile_path, "w") as f:
            f.write(vagrantfile_content)

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status
