from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from .base_provisioner import BaseComputerProvisioner
import os
import time
import logging

logger = logging.getLogger(__name__)

class AzureProvisioner(BaseComputerProvisioner):
    def __init__(self, port: int = 8000, resource_group: str = "commandlab-rg", 
                 location: str = "eastus", vm_size: str = "Standard_DS1_v2",
                 subscription_id: str = None, image_id: str = None,
                 max_retries: int = 3, timeout: int = 600):  # 10 minutes
        super().__init__(port)
        self.resource_group = resource_group
        self.location = location
        self.vm_size = vm_size
        self.vm_name = "commandlab-daemon"
        self.subscription_id = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID")
        self.image_id = image_id or "/your/custom/image/id"  # Should be configurable
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"
        
        if not self.subscription_id:
            raise ValueError("Azure subscription ID must be provided or set in AZURE_SUBSCRIPTION_ID environment variable")
        
        self.compute_client = ComputeManagementClient(
            credential=DefaultAzureCredential(),
            subscription_id=self.subscription_id
        )

    def setup(self) -> None:
        self._status = "starting"
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # Create VM using the CommandLAB image
                logger.info(f"Creating Azure VM {self.vm_name} in resource group {self.resource_group}")
                poller = self.compute_client.virtual_machines.begin_create_or_update(
                    self.resource_group,
                    self.vm_name,
                    {
                        'location': self.location,
                        'os_profile': {
                            'computer_name': self.vm_name,
                            'admin_username': 'commandlab',
                            'custom_data': f"""
                                pip install commandlab[local,daemon]
                                python -m commandlab.daemon.daemon --port {self.port} --backend pynput
                            """
                        },
                        'hardware_profile': {
                            'vm_size': self.vm_size
                        },
                        'storage_profile': {
                            'image_reference': {
                                'id': self.image_id
                            }
                        }
                    }
                )
                
                # Wait for the operation to complete with timeout
                logger.info(f"Waiting for VM creation to complete")
                start_time = time.time()
                while not poller.done() and time.time() - start_time < self.timeout:
                    time.sleep(10)
                
                if not poller.done():
                    self._status = "error"
                    logger.error(f"Timeout waiting for VM creation")
                    raise TimeoutError(f"Timeout waiting for VM creation")
                
                # Get the result to ensure it completed successfully
                result = poller.result()
                logger.info(f"VM {self.vm_name} created successfully")
                
                # Wait for VM to be running
                logger.info(f"Waiting for VM {self.vm_name} to be running")
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(f"VM {self.vm_name} is now running")
                        return
                    time.sleep(10)
                
                # If we get here, the VM didn't start in time
                self._status = "error"
                logger.error(f"Timeout waiting for VM {self.vm_name} to start")
                raise TimeoutError(f"Timeout waiting for VM {self.vm_name} to start")
                
            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    logger.error(f"Failed to create Azure VM after {self.max_retries} attempts: {e}")
                    raise
                logger.warning(f"Error creating Azure VM, retrying ({retry_count}/{self.max_retries}): {e}")
                time.sleep(2 ** retry_count)  # Exponential backoff

    def teardown(self) -> None:
        self._status = "stopping"
        logger.info(f"Deleting VM {self.vm_name} from resource group {self.resource_group}")
        
        try:
            poller = self.compute_client.virtual_machines.begin_delete(
                self.resource_group,
                self.vm_name
            )
            
            # Wait for the operation to complete with timeout
            start_time = time.time()
            while not poller.done() and time.time() - start_time < self.timeout:
                time.sleep(10)
            
            if not poller.done():
                self._status = "error"
                logger.error(f"Timeout waiting for VM deletion")
                raise TimeoutError(f"Timeout waiting for VM deletion")
            
            # Get the result to ensure it completed successfully
            poller.result()
            logger.info(f"VM {self.vm_name} deleted successfully")
            self._status = "stopped"
            
        except Exception as e:
            self._status = "error"
            logger.error(f"Error deleting VM {self.vm_name}: {e}")

    def is_running(self) -> bool:
        try:
            vm = self.compute_client.virtual_machines.get(
                self.resource_group,
                self.vm_name,
                expand='instanceView'
            )
            is_running = any(status.code == 'PowerState/running' 
                          for status in vm.instance_view.statuses)
            logger.debug(f"VM {self.vm_name} running status: {is_running}")
            return is_running
        except Exception as e:
            logger.error(f"Error checking VM status: {e}")
            return False
            
    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status 