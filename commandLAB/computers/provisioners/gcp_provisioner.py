from google.cloud import compute_v1
import time
import logging
from typing import Optional
from .base_provisioner import BaseComputerProvisioner, ProvisionerStatus

logger = logging.getLogger(__name__)


class GCPProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: int = 8000,
        daemon_token: Optional[str] = None,
        project: str = None,
        zone: str = "us-central1-a",
        machine_type: str = "n1-standard-1",
        source_image: str = None,
        max_provisioning_retries: int = 3,
        timeout: int = 600,  # 10 minutes
        max_health_retries: int = 3,
        health_check_timeout: int = 60,  # 1 minute
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
        if not project:
            raise ValueError("Project ID must be specified")
        self.project = project
        self.zone = zone
        self.machine_type = machine_type
        self.instance_name = "commandlab-daemon"
        self.source_image = (
            source_image or "projects/your-project/global/images/commandlab-daemon"
        )
        self.instance_client = compute_v1.InstancesClient()

    def _provision_resource(self) -> None:
        """Provision a GCP Compute Engine instance"""
        logger.info(
            f"Creating GCP VM {self.instance_name} in project {self.project}, zone {self.zone}"
        )

        instance = compute_v1.Instance()
        instance.name = self.instance_name
        instance.machine_type = (
            f"zones/{self.zone}/machineTypes/{self.machine_type}"
        )

        # Configure the boot disk
        disk = compute_v1.AttachedDisk()
        disk.boot = True
        disk.auto_delete = True
        initialize_params = compute_v1.AttachedDiskInitializeParams()
        initialize_params.source_image = self.source_image
        disk.initialize_params = initialize_params
        instance.disks = [disk]

        # Configure network
        network_interface = compute_v1.NetworkInterface()
        network_interface.name = "global/networks/default"
        instance.network_interfaces = [network_interface]

        # Configure metadata for startup script
        metadata = compute_v1.Metadata()
        metadata_item = compute_v1.Metadata.ItemsEntry()
        metadata_item.key = "startup-script"
        metadata_item.value = f"""
            pip install commandlab[local,daemon]
            python -m commandlab.daemon.daemon --port {self.daemon_port} --token {self.daemon_token} --backend pynput
        """
        metadata.items = [metadata_item]
        instance.metadata = metadata

        # Create the instance
        operation = self.instance_client.insert(
            project=self.project, zone=self.zone, instance_resource=instance
        )

        # Wait for the operation to complete with timeout
        logger.info(f"Waiting for VM creation to complete")
        start_time = time.time()
        while not operation.done() and time.time() - start_time < self.timeout:
            time.sleep(10)

        if not operation.done():
            logger.error(f"Timeout waiting for VM creation")
            raise TimeoutError(f"Timeout waiting for VM creation")

        # Get the result to ensure it completed successfully
        result = operation.result()
        logger.info(f"VM {self.instance_name} created successfully")

    def _deprovision_resource(self) -> None:
        """Delete the GCP Compute Engine instance"""
        logger.info(
            f"Deleting VM {self.instance_name} from project {self.project}, zone {self.zone}"
        )

        operation = self.instance_client.delete(
            project=self.project, zone=self.zone, instance=self.instance_name
        )

        # Wait for the operation to complete with timeout
        start_time = time.time()
        while not operation.done() and time.time() - start_time < self.timeout:
            time.sleep(10)

        if not operation.done():
            logger.error(f"Timeout waiting for VM deletion")
            raise TimeoutError(f"Timeout waiting for VM deletion")

        # Get the result to ensure it completed successfully
        operation.result()
        logger.info(f"VM {self.instance_name} deleted successfully")

    def is_running(self) -> bool:
        """Check if the GCP Compute Engine instance is running"""
        try:
            instance = self.instance_client.get(
                project=self.project, zone=self.zone, instance=self.instance_name
            )
            is_running = instance.status == "RUNNING"
            logger.debug(f"VM {self.instance_name} running status: {is_running}")
            return is_running
        except Exception as e:
            logger.error(f"Error checking VM status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status
