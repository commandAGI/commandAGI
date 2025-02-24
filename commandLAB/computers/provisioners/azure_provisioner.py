from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from .base_provisioner import BaseComputerProvisioner


class AzureProvisioner(BaseComputerProvisioner):
    def __init__(self, port: int = 8000, resource_group: str = "commandlab-rg", 
                 location: str = "eastus", vm_size: str = "Standard_DS1_v2"):
        super().__init__(port)
        self.resource_group = resource_group
        self.location = location
        self.vm_size = vm_size
        self.vm_name = "commandlab-daemon"
        self.compute_client = ComputeManagementClient(
            credential=DefaultAzureCredential(),
            subscription_id="your-subscription-id"
        )

    def setup(self) -> None:
        # Create VM using the CommandLAB image
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
                        'id': '/your/custom/image/id'  # Reference to your CommandLAB image
                    }
                }
            }
        )
        poller.result()

    def teardown(self) -> None:
        poller = self.compute_client.virtual_machines.begin_delete(
            self.resource_group,
            self.vm_name
        )
        poller.result()

    def is_running(self) -> bool:
        try:
            vm = self.compute_client.virtual_machines.get(
                self.resource_group,
                self.vm_name,
                expand='instanceView'
            )
            return any(status.code == 'PowerState/running' 
                      for status in vm.instance_view.statuses)
        except Exception:
            return False 