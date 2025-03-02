from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from .base_provisioner import BaseComputerProvisioner, ProvisionerStatus
import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AzureProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: int = 8000,
        daemon_token: Optional[str] = None,
        resource_group: str = "commandlab-rg",
        location: str = "eastus",
        vm_size: str = "Standard_DS1_v2",
        subscription_id: str = None,
        image_id: str = None,
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
        self.resource_group = resource_group
        self.location = location
        self.vm_size = vm_size
        self.vm_name = "commandlab-daemon"
        self.subscription_id = subscription_id or os.environ.get(
            "AZURE_SUBSCRIPTION_ID"
        )
        self.image_id = image_id or "/your/custom/image/id"  # Should be configurable

        if not self.subscription_id:
            raise ValueError(
                "Azure subscription ID must be provided or set in AZURE_SUBSCRIPTION_ID environment variable"
            )

        self.compute_client = ComputeManagementClient(
            credential=DefaultAzureCredential(), subscription_id=self.subscription_id
        )

    def _provision_resource(self) -> None:
        """Provision an Azure VM with the CommandLAB image"""
        logger.info(
            f"Creating Azure VM {self.vm_name} in resource group {self.resource_group}"
        )
        poller = self.compute_client.virtual_machines.begin_create_or_update(
            self.resource_group,
            self.vm_name,
            {
                "location": self.location,
                "os_profile": {
                    "computer_name": self.vm_name,
                    "admin_username": "commandlab",
                    "custom_data": f"""
                        pip install commandlab[local,daemon]
                        python -m commandlab.daemon.daemon --port {self.daemon_port} --token {self.daemon_token} --backend pynput
                    """,
                },
                "hardware_profile": {"vm_size": self.vm_size},
                "storage_profile": {"image_reference": {"id": self.image_id}},
            },
        )

        # Wait for the operation to complete with timeout
        logger.info(f"Waiting for VM creation to complete")
        start_time = time.time()
        while not poller.done() and time.time() - start_time < self.timeout:
            time.sleep(10)

        if not poller.done():
            logger.error(f"Timeout waiting for VM creation")
            raise TimeoutError(f"Timeout waiting for VM creation")

        # Get the result to ensure it completed successfully
        result = poller.result()
        logger.info(f"VM {self.vm_name} created successfully")

    def _deprovision_resource(self) -> None:
        """Delete the Azure VM"""
        logger.info(
            f"Deleting VM {self.vm_name} from resource group {self.resource_group}"
        )

        poller = self.compute_client.virtual_machines.begin_delete(
            self.resource_group, self.vm_name
        )

        # Wait for the operation to complete with timeout
        start_time = time.time()
        while not poller.done() and time.time() - start_time < self.timeout:
            time.sleep(10)

        if not poller.done():
            logger.error(f"Timeout waiting for VM deletion")
            raise TimeoutError(f"Timeout waiting for VM deletion")

        # Get the result to ensure it completed successfully
        poller.result()
        logger.info(f"VM {self.vm_name} deleted successfully")

    def is_running(self) -> bool:
        """Check if the Azure VM is running"""
        try:
            vm = self.compute_client.virtual_machines.get(
                self.resource_group, self.vm_name, expand="instanceView"
            )
            is_running = any(
                status.code == "PowerState/running"
                for status in vm.instance_view.statuses
            )
            logger.debug(f"VM {self.vm_name} running status: {is_running}")
            return is_running
        except Exception as e:
            logger.error(f"Error checking VM status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status
