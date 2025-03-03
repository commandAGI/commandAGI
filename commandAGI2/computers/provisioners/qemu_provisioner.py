import os
import subprocess
import time
import logging
from typing import Optional
from pathlib import Path
from .base_provisioner import BaseComputerProvisioner, ProvisionerStatus

logger = logging.getLogger(__name__)


class QEMUProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: int = 8000,
        daemon_token: Optional[str] = None,
        vm_name: str = "commandagi2-daemon",
        vm_image: str = None,
        max_provisioning_retries: int = 3,
        timeout: int = 300,  # 5 minutes
        max_health_retries: int = 10,
        health_check_timeout: int = 60,  # 1 minute
        memory: str = "2G",
        cpus: int = 2,
    ):
        super().__init__(
            daemon_base_url=daemon_base_url,
            daemon_port=daemon_port,
            daemon_token=daemon_token,
            max_provisioning_retries=max_provisioning_retries,
            timeout=timeout,
            max_health_retries=max_health_retries,
            health_check_timeout=health_check_timeout,
        )
        self.vm_name = vm_name
        self.vm_image = vm_image
        self.memory = memory
        self.cpus = cpus
        self._vm_pid = None

    def _provision_resource(self) -> None:
        """Start a QEMU VM and run the daemon."""
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
            f"user,id=net0,hostfwd=tcp::{self.daemon_port}-:{self.daemon_port}",
            "-device",
            "virtio-net-pci,netdev=net0",
            "-nographic",
            "-daemonize",
        ]

        # Start the VM
        subprocess.run(qemu_cmd, check=True)

        # Get VM PID
        ps_output = subprocess.check_output(["pgrep", "-f", self.vm_name]).decode()
        self._vm_pid = int(ps_output.strip())

        # Wait for SSH to be available and run daemon setup
        time.sleep(30)  # Basic delay for system boot
        subprocess.run(
            [
                "ssh",
                "-p",
                str(self.daemon_port),
                "user@localhost",
                f"pip install commandagi2[local,daemon-server] && python -m commandagi2.daemon.daemon --port {self.daemon_port} --token {self.daemon_token} --backend pynput",
            ],
            check=True,
        )

    def _deprovision_resource(self) -> None:
        """Stop and destroy the QEMU VM."""
        if not self._vm_pid:
            logger.info("No VM to teardown")
            return

        logger.info(f"Stopping VM {self.vm_name}")

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

        self._vm_pid = None
        logger.info(f"VM {self.vm_name} stopped")

    def is_running(self) -> bool:
        """Check if the QEMU VM is running."""
        if not self._vm_pid:
            return False

        try:
            os.kill(self._vm_pid, 0)  # Check if process exists
            return True
        except OSError:
            return False
