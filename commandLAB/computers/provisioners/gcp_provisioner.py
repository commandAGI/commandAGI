from google.cloud import compute_v1
from .base_provisioner import BaseComputerProvisioner


class GCPProvisioner(BaseComputerProvisioner):
    def __init__(self, port: int = 8000, project: str = "your-project-id", 
                 zone: str = "us-central1-a", machine_type: str = "n1-standard-1"):
        super().__init__(port)
        self.project = project
        self.zone = zone
        self.machine_type = machine_type
        self.instance_name = "commandlab-daemon"
        self.instance_client = compute_v1.InstancesClient()

    def setup(self) -> None:
        instance_config = {
            "name": self.instance_name,
            "machine_type": f"zones/{self.zone}/machineTypes/{self.machine_type}",
            "disks": [{
                "boot": True,
                "auto_delete": True,
                "initialize_params": {
                    "source_image": "projects/your-project/global/images/commandlab-daemon",
                }
            }],
            "metadata": {
                "items": [{
                    "key": "startup-script",
                    "value": f"""
                        pip install commandlab[local,daemon]
                        python -m commandlab.daemon.daemon --port {self.port} --backend pynput
                    """
                }]
            }
        }
        
        operation = self.instance_client.insert(
            project=self.project,
            zone=self.zone,
            instance_resource=instance_config
        )
        operation.result()

    def teardown(self) -> None:
        operation = self.instance_client.delete(
            project=self.project,
            zone=self.zone,
            instance=self.instance_name
        )
        operation.result()

    def is_running(self) -> bool:
        try:
            instance = self.instance_client.get(
                project=self.project,
                zone=self.zone,
                instance=self.instance_name
            )
            return instance.status == "RUNNING"
        except Exception:
            return False 