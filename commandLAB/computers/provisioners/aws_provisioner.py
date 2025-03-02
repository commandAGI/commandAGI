import boto3
import time
import logging
from typing import List, Optional
from .base_provisioner import BaseComputerProvisioner, ProvisionerStatus

logger = logging.getLogger(__name__)


class AWSProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: int = 8000,
        daemon_token: Optional[str] = None,
        region: str = "us-west-2",
        instance_type: str = "t2.micro",
        image_id: str = None,
        security_groups: List[str] = None,
        max_provisioning_retries: int = 3,
        timeout: int = 300,  # 5 minutes
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
        self.region = region
        self.instance_type = instance_type
        self.instance_id = None
        self.image_id = image_id or "ami-commandlab"  # Default AMI ID
        self.security_groups = security_groups or ["commandlab-daemon"]
        self.ec2 = boto3.client("ec2", region_name=self.region)

    def _provision_resource(self) -> None:
        """Provision an EC2 instance with the CommandLAB AMI"""
        logger.info(f"Launching EC2 instance with image {self.image_id}")
        response = self.ec2.run_instances(
            ImageId=self.image_id,
            InstanceType=self.instance_type,
            MinCount=1,
            MaxCount=1,
            SecurityGroups=self.security_groups,
            UserData=f"""#!/bin/bash
                pip install commandlab[local,daemon]
                python -m commandlab.daemon.daemon --port {self.daemon_port} --token {self.daemon_token} --backend pynput
            """,
        )
        self.instance_id = response["Instances"][0]["InstanceId"]
        logger.info(f"Successfully launched instance {self.instance_id}")

    def _deprovision_resource(self) -> None:
        """Terminate the EC2 instance"""
        if not self.instance_id:
            return

        logger.info(f"Terminating instance {self.instance_id}")
        self.ec2.terminate_instances(InstanceIds=[self.instance_id])

        # Wait for termination with timeout
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                response = self.ec2.describe_instances(
                    InstanceIds=[self.instance_id]
                )
                if not response.get("Reservations") or not response["Reservations"][
                    0
                ].get("Instances"):
                    break
                state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
                if state == "terminated":
                    logger.info(
                        f"Instance {self.instance_id} successfully terminated"
                    )
                    break
                logger.debug(f"Instance {self.instance_id} state: {state}")
                time.sleep(5)
            except Exception as e:
                # Instance might be gone already
                logger.info(f"Instance {self.instance_id} no longer exists: {e}")
                break

    def is_running(self) -> bool:
        """Check if the EC2 instance is running"""
        if not self.instance_id:
            return False
        try:
            response = self.ec2.describe_instances(InstanceIds=[self.instance_id])
            if not response.get("Reservations") or not response["Reservations"][0].get(
                "Instances"
            ):
                return False
            state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
            return state == "running"
        except Exception as e:
            logger.error(f"Error checking instance status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status
