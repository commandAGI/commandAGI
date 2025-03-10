import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Literal, Optional

from commandAGI.computers.clients.base_computer_client import BaseComputerComputerClient

logger = logging.getLogger(__name__)


class VMwareComputerClient(BaseComputerComputerClient):
    def __init__(
        self,
        port: int = 8000,
        vm_name: str = "commandagi-daemon",
        vm_image: str = None,
        provider: Literal["workstation", "fusion", "player"] = "workstation",
        max_retries: int = 3,
        timeout: int = 300,  # 5 minutes
    ):
        super().__init__(port)
        self.vm_name = vm_name
        self.vm_image = vm_image
        self.provider = provider
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"
        self._vm_id = None
        self._vm_path = None

    def setup(self) -> None:
        """Setup a VMware VM and start the daemon."""
        self._status = "starting"
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Clone VM if image is provided
                if self.vm_image:
                    logger.info(f"Cloning VM from {self.vm_image}")
                    vm_dir = f"./vmware/{self.vm_name}"
                    os.makedirs(vm_dir, exist_ok=True)

                    # Clone the VM
                    self._vmrun_command(
                        [
                            "clone",
                            self.vm_image,
                            f"{vm_dir}/{self.vm_name}.vmx",
                            "linked",
                        ]
                    )

                    self._vm_path = f"{vm_dir}/{self.vm_name}.vmx"
                else:
                    raise ValueError("VM image must be provided")

                # Start the VM
                logger.info(f"Starting VM {self.vm_name}")
                self._vmrun_command(["start", self._vm_path, "nogui"])

                # Set VM ID
                self._vm_id = self.vm_name

                # Wait for VM to be running
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(f"VM {self.vm_name} is now running")

                        # Setup port forwarding (using NAT)
                        self._vmrun_command(
                            [
                                "setPortForwarding",
                                self._vm_path,
                                "NAT",
                                f"daemon{self.port}",
                                "tcp",
                                str(self.port),
                                str(self.port),
                            ]
                        )

                        # Run daemon setup script
                        self._vmrun_command(
                            [
                                "runScriptInGuest",
                                self._vm_path,
                                "-gu",
                                "vagrant",
                                "-gp",
                                "vagrant",
                                "/bin/bash",
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
        """Stop and destroy the VMware VM."""
        if not self._vm_id or not self._vm_path:
            logger.info("No VM to teardown")
            return

        self._status = "stopping"
        logger.info(f"Stopping VM {self.vm_name}")

        try:
            # Power off the VM
            self._vmrun_command(["stop", self._vm_path, "hard"])

            # Wait for VM to stop
            time.sleep(5)

            # Delete the VM files
            vm_dir = os.path.dirname(self._vm_path)
            if os.path.exists(vm_dir):
                shutil.rmtree(vm_dir)

            self._status = "stopped"
            self._vm_id = None
            self._vm_path = None
            logger.info(f"VM {self.vm_name} stopped and deleted")
        except Exception as e:
            self._status = "error"
            logger.error(f"Error stopping VM {self.vm_name}: {e}")

    def is_running(self) -> bool:
        """Check if the VMware VM is running."""
        if not self._vm_id or not self._vm_path:
            return False

        try:
            # List running VMs
            result = self._vmrun_command(["list"], capture_output=True)
            return self._vm_path in result
        except Exception as e:
            logger.error(f"Error checking VM status: {e}")
            return False

    def _vmrun_command(self, args: list, capture_output: bool = False) -> Optional[str]:
        """Run a vmrun command."""
        # Determine the vmrun command based on provider
        if self.provider == "fusion":
            vmrun_cmd = ["vmrun", "-T", "fusion"]
        elif self.provider == "player":
            vmrun_cmd = ["vmrun", "-T", "player"]
        else:  # Default to workstation
            vmrun_cmd = ["vmrun", "-T", "ws"]

        cmd = vmrun_cmd + args
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
            logger.error(f"vmrun command failed: {e}")
            raise

    def get_status(self) -> str:
        """Get the current status of the computer_client."""
        return self._status
