import boto3
import subprocess
from .base_provisioner import BaseComputerProvisioner


class AWSProvisioner(BaseComputerProvisioner):
    def __init__(self, port: int = 8000, region: str = "us-west-2", instance_type: str = "t2.micro"):
        super().__init__(port)
        self.region = region
        self.instance_type = instance_type
        self.instance_id = None
        self.ec2 = boto3.client('ec2', region_name=self.region)

    def setup(self) -> None:
        # Launch EC2 instance with the CommandLAB AMI
        response = self.ec2.run_instances(
            ImageId='ami-commandlab',  # You'll need to create this AMI
            InstanceType=self.instance_type,
            MinCount=1,
            MaxCount=1,
            SecurityGroups=['commandlab-daemon'],  # Security group allowing port access
            UserData=f"""#!/bin/bash
                pip install commandlab[local,daemon]
                python -m commandlab.daemon.daemon --port {self.port} --backend pynput
            """
        )
        self.instance_id = response['Instances'][0]['InstanceId']

    def teardown(self) -> None:
        if self.instance_id:
            self.ec2.terminate_instances(InstanceIds=[self.instance_id])

    def is_running(self) -> bool:
        if not self.instance_id:
            return False
        response = self.ec2.describe_instances(InstanceIds=[self.instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        return state == 'running' 