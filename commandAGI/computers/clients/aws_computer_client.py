import logging
import secrets
import time
from typing import List, Optional

import boto3

from commandAGI.computers.backend.base_computer_client import (
    BaseComputerComputerClient,
    ComputerClientStatus,
)

logger = logging.getLogger(__name__)


class AWSComputerClient(BaseComputerComputerClient):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = None,
        daemon_token: Optional[str] = None,
        region: str = "us-west-2",
        instance_type: str = "t2.micro",
        image_id: str = None,
        instance_name: Optional[str] = None,
        name_prefix: str = "commandagi-daemon",
        security_groups: List[str] = None,
        max_provisioning_retries: int = 3,
        timeout: int = 300,  # 5 minutes
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
        self.region = region
        self.instance_type = instance_type
        self.instance_id = None
        self.name_prefix = name_prefix
        self.instance_name = instance_name
        self.image_id = image_id or "ami-commandagi"  # Default AMI ID
        self.security_groups = security_groups or ["commandagi-daemon"]
        self.ec2 = boto3.client("ec2", region_name=self.region)

    def _provision_resource(self) -> None:
        """Provision an EC2 instance with the commandAGI AMI"""
        print(f"Launching EC2 instance with image {self.image_id}")

        # For cloud VMs, use fixed port 8000 if not specified
        if self.daemon_port is None:
            self.daemon_port = 8000
            print(f"Using default port {self.daemon_port} for AWS EC2")

        # Generate a unique instance name if not provided
        if self.instance_name is None:
            # For cloud resources, we'll use a timestamp-based name
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            self.instance_name = f"{self.name_prefix}-{timestamp}"
            print(f"Using instance name: {self.instance_name}")

        # Add name tag to the instance
        tags = [
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": self.instance_name}],
            }
        ]

        # Launch the instance
        print(f"Launching EC2 instance with name {self.instance_name}")
        response = self.ec2.run_instances(
            ImageId=self.image_id,
            InstanceType=self.instance_type,
            MinCount=1,
            MaxCount=1,
            SecurityGroups=self.security_groups,
            TagSpecifications=tags,
            UserData=f"""#!/bin/bash
                pip install commandagi[local,daemon]
                python -m commandagi.daemon.daemon --port {self.daemon_port} --token {self.daemon_token} --backend pynput
            """,
        )
        self.instance_id = response["Instances"][0]["InstanceId"]
        print(
            f"Successfully launched instance {
                self.instance_id} with name {
                self.instance_name}"
        )

        # Wait for the instance to reach running state
        print(
            f"Waiting for instance {
                self.instance_id} to reach running state"
        )
        waiter = self.ec2.get_waiter("instance_running")
        try:
            waiter.wait(
                InstanceIds=[self.instance_id],
                WaiterConfig={
                    "Delay": 10,
                    "MaxAttempts": self.timeout
                    // 10,  # Convert timeout to number of attempts
                },
            )
            print(f"Instance {self.instance_id} is now in running state")
        except Exception as e:
            print(f"Error waiting for instance to reach running state: {e}")
            raise

    def _deprovision_resource(self) -> None:
        """Terminate the EC2 instance"""
        if not self.instance_id:
            print("No instance ID found, nothing to terminate")
            return

        print(
            f"Terminating instance {
                self.instance_id} ({
                self.instance_name})"
        )
        self.ec2.terminate_instances(InstanceIds=[self.instance_id])

        # Wait for termination with timeout
        print(f"Waiting for instance {self.instance_id} to terminate")
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                response = self.ec2.describe_instances(InstanceIds=[self.instance_id])
                if not response.get("Reservations") or not response["Reservations"][
                    0
                ].get("Instances"):
                    print(f"Instance {self.instance_id} no longer exists")
                    break

                state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
                if state == "terminated":
                    print(
                        f"Instance {
                            self.instance_id} successfully terminated"
                    )
                    break

                print(f"Instance {self.instance_id} state: {state}")
                time.sleep(5)
            except Exception as e:
                # Instance might be gone already
                print(f"Instance {self.instance_id} no longer exists: {e}")
                break

        if time.time() - start_time >= self.timeout:
            print(
                f"Timeout waiting for instance {
                    self.instance_id} to terminate"
            )

    def is_running(self) -> bool:
        """Check if the EC2 instance is running"""
        if not self.instance_id:
            print("No instance ID found, cannot check if running")
            return False

        try:
            print(f"Checking if instance {self.instance_id} is running")
            response = self.ec2.describe_instances(InstanceIds=[self.instance_id])

            if not response.get("Reservations") or not response["Reservations"][0].get(
                "Instances"
            ):
                print(f"Instance {self.instance_id} not found")
                return False

            state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
            is_running = state == "running"
            print(
                f"Instance {
                    self.instance_id} state: {state}, running: {is_running}"
            )
            return is_running
        except Exception as e:
            print(f"Error checking instance status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the computer_client."""
        return self._status.value
