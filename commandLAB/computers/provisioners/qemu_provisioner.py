import os
import subprocess
import time
import logging
from typing import Optional
from pathlib import Path
from .base_provisioner import BaseComputerProvisioner

logger = logging.getLogger(__name__)


class QEMUProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        port: int = 8000,
        vm_name: str = "commandlab-daemon",
        vm_image: str = None,
        max_retries: int = 3,
        timeout: int = 300,  # 5 minutes
        memory: str = "2G",
        cpus: int = 2,
    ):
        super().__init__(port)
        self.vm_name = vm_name
        self.vm_image = vm_image
        self.max_retries = max_retries
        self.timeout = timeout
        self.memory = memory
        self.cpus = cpus
        self._status = "not_started"
        self._vm_pid = None

    def setup(self) -> None:
        """Setup a QEMU VM and start the daemon."""
        self._status = "starting"
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                if not self.vm_image:
                    raise ValueError("VM image must be provided")

                logger.info(f"Starting QEMU VM {self.vm_name}")

                # Build QEMU command
                qemu_cmd = [
                    "qemu-system-x86_64",
                    "-name",
                    self.vm_name,
                    "-m",
                    self.memory,
                    "-smp",
                    str(self.cpus),
                    "-drive",
                    f"file={self.vm_image},format=qcow2",
                    "-netdev",
                    f"user,id=net0,hostfwd=tcp::{self.port}-:{self.port}",
                    "-device",
                    "virtio-net-pci,netdev=net0",
                    "-nographic",
                    "-daemonize",
                ]

                # Start the VM
                subprocess.run(qemu_cmd, check=True)

                # Get VM PID
                ps_output = subprocess.check_output(
                    ["pgrep", "-f", self.vm_name]
                ).decode()
                self._vm_pid = int(ps_output.strip())

                # Wait for VM to be running
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(f"VM {self.vm_name} is now running")

                        # Wait for SSH to be available and run daemon setup
                        time.sleep(30)  # Basic delay for system boot
                        subprocess.run(
                            [
                                "ssh",
                                "-p",
                                str(self.port),
                                "user@localhost",
                                f"pip install commandlab[local,daemon-server] && python -m commandlab.daemon.daemon --port {self.port} --backend pynput",
                            ],
                            check=True,
                        )

                        return
                    time.sleep(5)

                # If we get here, the VM didn't start in time
                self._status = "error"
                logger.error(f"Timeout waiting for VM {self.vm_name} to start")
                raise TimeoutError(f"Timeout waiting for VM {self.vm_name} to start")

            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    logger.error(
                        f"Failed to start VM after {self.max_retries} attempts: {e}"
                    )
                    raise
                logger.warning(
                    f"Error starting VM, retrying ({retry_count}/{self.max_retries}): {e}"
                )
                time.sleep(2**retry_count)  # Exponential backoff

    def teardown(self) -> None:
        """Stop and destroy the QEMU VM."""
        if not self._vm_pid:
            logger.info("No VM to teardown")
            return

        self._status = "stopping"
        logger.info(f"Stopping VM {self.vm_name}")

        try:
            # Kill the QEMU process
            subprocess.run(["kill", str(self._vm_pid)], check=True)

            # Wait for process to terminate
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
                    os.kill(self._vm_pid, 0)  # Check if process exists
                    time.sleep(1)
                except OSError:
                    break

            self._status = "stopped"
            self._vm_pid = None
            logger.info(f"VM {self.vm_name} stopped")
        except Exception as e:
            self._status = "error"
            logger.error(f"Error stopping VM {self.vm_name}: {e}")

    def is_running(self) -> bool:
        """Check if the QEMU VM is running."""
        if not self._vm_pid:
            return False

        try:
            os.kill(self._vm_pid, 0)  # Check if process exists
            return True
        except OSError:
            return False

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status
