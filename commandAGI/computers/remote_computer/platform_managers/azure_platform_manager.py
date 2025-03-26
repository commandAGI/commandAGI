import logging
import os
import secrets
import time
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

from commandAGI.computers.platform_managers.base_platform_manager import (
    BaseComputerPlatformManager,
)

logger = logging.getLogger(__name__)


class AzurePlatformManager(BaseComputerPlatformManager):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = None,
        daemon_token: Optional[str] = None,
        resource_group: str = "commandagi-rg",
        location: str = "eastus",
        vm_size: str = "Standard_DS1_v2",
        subscription_id: str = None,
        image_id: str = None,
        vm_name: Optional[str] = None,
        name_prefix: str = "commandagi-daemon",
        max_provisioning_retries: int = 3,
        timeout: int = 600,  # 10 minutes
        max_health_retries: int = 10,
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
        self.name_prefix = name_prefix
        self.vm_name = vm_name
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

    def _generate_vm_name(self) -> str:
        """Generate a unique VM name"""
        if self.vm_name:
            return self.vm_name

        # For cloud resources, we'll use a timestamp-based name
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{self.name_prefix}-{timestamp}"

    def _provision_resource(self) -> None:
        """Provision an Azure VM with the commandAGI image"""
        # For cloud VMs, use fixed port 8000 if not specified
        if self.daemon_port is None:
            self.daemon_port = 8000
            print(f"Using default port {self.daemon_port} for Azure VM")

        # Generate a unique VM name if not provided
        if not self.vm_name:
            self.vm_name = self._generate_vm_name()

        print(
            f"Creating Azure VM {
                self.vm_name} in resource group {
                self.resource_group}, location {
                self.location}"
        )

        # Define VM parameters
        vm_parameters = {
            "location": self.location,
            "os_profile": {
                "computer_name": self.vm_name,
                "admin_username": "commandagi",
                "admin_password": secrets.token_urlsafe(16)
                + "Aa1!",  # Generate a secure random password
            },
            "hardware_profile": {"vm_size": self.vm_size},
            "storage_profile": {"image_reference": {"id": self.image_id}},
            "network_profile": {
                "network_interfaces": [
                    {
                        "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Network/networkInterfaces/{self.vm_name}-nic",
                        "properties": {"primary": True},
                    }
                ]
            },
        }

        # Add custom script extension for daemon setup
        custom_data = f"""#!/bin/bash
            apt-get update
            apt-get install -y python3 python3-pip
            pip3 install commandagi[local,daemon]
            python3 -m commandagi.daemon.daemon --port {self.daemon_port} --token {self.daemon_token} --backend pynput
        """

        # Base64 encode the custom data
        import base64

        encoded_custom_data = base64.b64encode(custom_data.encode()).decode()
        vm_parameters["os_profile"]["custom_data"] = encoded_custom_data

        print(f"Sending request to create VM {self.vm_name}")
        poller = self.compute_client.virtual_machines.begin_create_or_update(
            self.resource_group, self.vm_name, vm_parameters
        )

        # Wait for the operation to complete with timeout
        print(
            f"Waiting for VM creation to complete (timeout: {
                self.timeout}s)"
        )
        start_time = time.time()
        while not poller.done() and time.time() - start_time < self.timeout:
            # Print progress every 10 seconds
            if int(time.time() - start_time) % 10 == 0:
                print(
                    f"VM creation in progress... ({int(time.time() - start_time)}s elapsed)"
                )
            time.sleep(5)

        if not poller.done():
            print(
                f"Timeout waiting for VM creation after {int(time.time() - start_time)}s"
            )
            raise TimeoutError(f"Timeout waiting for VM creation")

        try:
            # Get the result to ensure it completed successfully
            result = poller.result()
            print(f"VM {self.vm_name} created successfully")

            # Wait a bit for the VM to initialize
            print(f"Waiting for VM to initialize...")
            time.sleep(10)
        except Exception as e:
            print(f"Error during VM creation: {e}")
            raise

    def _deprovision_resource(self) -> None:
        """Delete the Azure VM"""
        if not self.vm_name:
            print("No VM name found, nothing to delete")
            return

        print(
            f"Deleting VM {
                self.vm_name} from resource group {
                self.resource_group}"
        )

        try:
            poller = self.compute_client.virtual_machines.begin_delete(
                self.resource_group, self.vm_name
            )

            # Wait for the operation to complete with timeout
            print(
                f"Waiting for VM deletion to complete (timeout: {
                    self.timeout}s)"
            )
            start_time = time.time()
            while not poller.done() and time.time() - start_time < self.timeout:
                # Print progress every 10 seconds
                if int(time.time() - start_time) % 10 == 0:
                    print(
                        f"VM deletion in progress... ({int(time.time() - start_time)}s elapsed)"
                    )
                time.sleep(5)

            if not poller.done():
                print(
                    f"Timeout waiting for VM deletion after {int(time.time() - start_time)}s"
                )
                print("The VM may still be deleting in the background")
                return

            # Get the result to ensure it completed successfully
            poller.result()
            print(f"VM {self.vm_name} deleted successfully")

        except Exception as e:
            print(f"Error during VM deletion: {e}")

    def is_running(self) -> bool:
        """Check if the Azure VM is running"""
        if not self.vm_name:
            print("No VM name found, cannot check if running")
            return False

        try:
            print(f"Checking if VM {self.vm_name} is running")
            vm = self.compute_client.virtual_machines.get(
                self.resource_group, self.vm_name, expand="instanceView"
            )

            # Check for PowerState/running status
            is_running = any(
                status.code == "PowerState/running"
                for status in vm.instance_view.statuses
            )

            # Get the actual power state for logging
            power_state = next(
                (
                    status.code
                    for status in vm.instance_view.statuses
                    if status.code.startswith("PowerState/")
                ),
                "PowerState/unknown",
            )

            print(
                f"VM {
                    self.vm_name} power state: {power_state}, running: {is_running}"
            )
            return is_running
        except Exception as e:
            print(f"Error checking VM status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the platform_manager."""
        return self._status.value
