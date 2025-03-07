import os
import subprocess
import time
import logging
from typing import Optional
from pathlib import Path
from .base_provisioner import BaseComputerProvisioner

logger = logging.getLogger(__name__)


class VirtualBoxProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        port: int = 8000,
        vm_name: str = "commandagi-daemon",
        vm_image: str = None,
        max_retries: int = 3,
        timeout: int = 300,  # 5 minutes
    ):
        super().__init__(port)
        self.vm_name = vm_name
        self.vm_image = vm_image
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"
        self._vm_id = None

    def setup(self) -> None:
        """Setup a VirtualBox VM and start the daemon."""
        self._status = "starting"
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Import VM if image is provided
                if self.vm_image:
                    logger.info(f"Importing VM from {self.vm_image}")
                    self._vboxmanage_command(
                        [
                            "import",
                            self.vm_image,
                            "--vsys",
                            "0",
                            "--vmname",
                            self.vm_name,
                        ]
                    )

                # Start the VM
                logger.info(f"Starting VM {self.vm_name}")
                self._vboxmanage_command(
                    ["startvm", self.vm_name, "--type", "headless"]
                )

                # Set VM ID
                self._vm_id = self.vm_name

                # Wait for VM to be running
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(f"VM {self.vm_name} is now running")

                        # Setup port forwarding
                        self._vboxmanage_command(
                            [
                                "modifyvm",
                                self.vm_name,
                                "--natpf1",
                                f"daemon,tcp,,{self.port},,{self.port}",
                            ]
                        )

                        # Run daemon setup script
                        self._vboxmanage_command(
                            [
                                "guestcontrol",
                                self.vm_name,
                                "run",
                                "--exe",
                                "/bin/bash",
                                "--username",
                                "vagrant",
                                "--password",
                                "vagrant",
                                "--",
                                "bash",
                                "-c",
                                f"pip install commandagi[local,daemon] && python -m commandagi.daemon.daemon --port {
                                    self.port} --backend pynput",
                            ]
                        )

                        return
                    time.sleep(5)

                # If we get here, the VM didn't start in time
                self._status = "error"
                logger.error(f"Timeout waiting for VM {self.vm_name} to start")
                raise TimeoutError(
                    f"Timeout waiting for VM {
                        self.vm_name} to start"
                )

            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    logger.error(
                        f"Failed to start VM after {
                            self.max_retries} attempts: {e}"
                    )
                    raise
                logger.warning(
                    f"Error starting VM, retrying ({retry_count}/{self.max_retries}): {e}"
                )
                time.sleep(2**retry_count)  # Exponential backoff

    def teardown(self) -> None:
        """Stop and destroy the VirtualBox VM."""
        if not self._vm_id:
            logger.info("No VM to teardown")
            return

        self._status = "stopping"
        logger.info(f"Stopping VM {self.vm_name}")

        try:
            # Power off the VM
            self._vboxmanage_command(["controlvm", self.vm_name, "poweroff"])

            # Wait for VM to stop
            time.sleep(5)

            # Unregister and delete the VM
            self._vboxmanage_command(["unregistervm", self.vm_name, "--delete"])

            self._status = "stopped"
            self._vm_id = None
            logger.info(f"VM {self.vm_name} stopped and deleted")
        except Exception as e:
            self._status = "error"
            logger.error(f"Error stopping VM {self.vm_name}: {e}")

    def is_running(self) -> bool:
        """Check if the VirtualBox VM is running."""
        if not self._vm_id:
            return False

        try:
            # Get VM info
            result = self._vboxmanage_command(
                ["showvminfo", self.vm_name, "--machinereadable"], capture_output=True
            )
            return 'VMState="running"' in result
        except Exception as e:
            logger.error(f"Error checking VM status: {e}")
            return False

    def _vboxmanage_command(
        self, args: list, capture_output: bool = False
    ) -> Optional[str]:
        """Run a VBoxManage command."""
        cmd = ["VBoxManage"] + args
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=capture_output,
                text=True if capture_output else False,
            )

            if capture_output:
                return result.stdout
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"VBoxManage command failed: {e}")
            raise

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status
