from google.cloud import compute_v1
import time
import logging
from typing import Optional
import secrets
from commandAGI.computers.backend.base_provisioner import BaseComputerProvisioner, ProvisionerStatus

logger = logging.getLogger(__name__)


class GCPProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = None,
        daemon_token: Optional[str] = None,
        project: str = None,
        zone: str = "us-central1-a",
        machine_type: str = "n1-standard-1",
        source_image: str = None,
        instance_name: Optional[str] = None,
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
        if not project:
            raise ValueError("Project ID must be specified")
        self.project = project
        self.zone = zone
        self.machine_type = machine_type
        self.name_prefix = name_prefix
        self.instance_name = instance_name
        self.source_image = (
            source_image or "projects/your-project/global/images/commandagi-daemon"
        )
        self.instance_client = compute_v1.InstancesClient()
        self.zone_operations_client = compute_v1.ZoneOperationsClient()

    def _generate_instance_name(self) -> str:
        """Generate a unique instance name"""
        if self.instance_name:
            return self.instance_name

        # For cloud resources, we'll use a timestamp-based name
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{self.name_prefix}-{timestamp}"

    def _provision_resource(self) -> None:
        """Provision a GCP Compute Engine instance"""
        # For cloud VMs, use fixed port 8000 if not specified
        if self.daemon_port is None:
            self.daemon_port = 8000
            print(f"Using default port {self.daemon_port} for GCP VM")

        # Generate a unique instance name if not provided
        if not self.instance_name:
            self.instance_name = self._generate_instance_name()

        print(
            f"Creating GCP VM {self.instance_name} in project {self.project}, zone {self.zone}"
        )

        instance = compute_v1.Instance()
        instance.name = self.instance_name
        instance.machine_type = f"zones/{self.zone}/machineTypes/{self.machine_type}"

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

        # Add access config to get an external IP
        access_config = compute_v1.AccessConfig()
        access_config.name = "External NAT"
        access_config.type_ = "ONE_TO_ONE_NAT"
        access_config.network_tier = "PREMIUM"
        network_interface.access_configs = [access_config]

        instance.network_interfaces = [network_interface]

        # Configure metadata for startup script
        metadata = compute_v1.Metadata()
        metadata_item = compute_v1.Metadata.ItemsEntry()
        metadata_item.key = "startup-script"
        metadata_item.value = f"""#!/bin/bash
            apt-get update
            apt-get install -y python3 python3-pip
            pip3 install commandagi[local,daemon]
            python3 -m commandagi.daemon.daemon --port {self.daemon_port} --token {self.daemon_token} --backend pynput
        """
        metadata.items = [metadata_item]
        instance.metadata = metadata

        # Create the instance
        print(f"Sending request to create VM {self.instance_name}")
        operation = self.instance_client.insert(
            project=self.project, zone=self.zone, instance_resource=instance
        )

        # Wait for the operation to complete with timeout
        print(f"Waiting for VM creation to complete (timeout: {self.timeout}s)")
        start_time = time.time()
        while not operation.done() and time.time() - start_time < self.timeout:
            operation = self.zone_operations_client.get(
                project=self.project, zone=self.zone, operation=operation.name
            )
            if operation.status == compute_v1.Operation.Status.DONE:
                break

            # Print progress every 10 seconds
            if int(time.time() - start_time) % 10 == 0:
                print(
                    f"VM creation in progress... ({int(time.time() - start_time)}s elapsed)"
                )

            time.sleep(5)

        if not operation.done():
            print(
                f"Timeout waiting for VM creation after {int(time.time() - start_time)}s"
            )
            raise TimeoutError(f"Timeout waiting for VM creation")

        # Check if the operation was successful
        if operation.error:
            print(f"Error creating VM: {operation.error.errors}")
            raise RuntimeError(f"Failed to create VM: {operation.error.errors}")

        print(f"VM {self.instance_name} created successfully")

        # Wait a bit for the VM to initialize
        print(f"Waiting for VM to initialize...")
        time.sleep(10)

    def _deprovision_resource(self) -> None:
        """Delete the GCP Compute Engine instance"""
        if not self.instance_name:
            print("No instance name found, nothing to delete")
            return

        print(
            f"Deleting VM {self.instance_name} from project {self.project}, zone {self.zone}"
        )

        try:
            operation = self.instance_client.delete(
                project=self.project, zone=self.zone, instance=self.instance_name
            )

            # Wait for the operation to complete with timeout
            print(f"Waiting for VM deletion to complete (timeout: {self.timeout}s)")
            start_time = time.time()
            while not operation.done() and time.time() - start_time < self.timeout:
                operation = self.zone_operations_client.get(
                    project=self.project, zone=self.zone, operation=operation.name
                )
                if operation.status == compute_v1.Operation.Status.DONE:
                    break

                # Print progress every 10 seconds
                if int(time.time() - start_time) % 10 == 0:
                    print(
                        f"VM deletion in progress... ({int(time.time() - start_time)}s elapsed)"
                    )

                time.sleep(5)

            if not operation.done():
                print(
                    f"Timeout waiting for VM deletion after {int(time.time() - start_time)}s"
                )
                print("The VM may still be deleting in the background")
                return

            # Check if the operation was successful
            if operation.error:
                print(f"Error deleting VM: {operation.error.errors}")
                return

            print(f"VM {self.instance_name} deleted successfully")

        except Exception as e:
            print(f"Error during VM deletion: {e}")

    def is_running(self) -> bool:
        """Check if the GCP Compute Engine instance is running"""
        if not self.instance_name:
            print("No instance name found, cannot check if running")
            return False

        try:
            print(f"Checking if VM {self.instance_name} is running")
            instance = self.instance_client.get(
                project=self.project, zone=self.zone, instance=self.instance_name
            )
            is_running = instance.status == "RUNNING"
            print(
                f"VM {self.instance_name} status: {instance.status}, running: {is_running}"
            )
            return is_running
        except Exception as e:
            print(f"Error checking VM status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status.value
