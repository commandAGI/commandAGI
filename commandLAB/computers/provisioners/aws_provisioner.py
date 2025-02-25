import boto3
import subprocess
import time
import logging
from typing import List, Optional
from .base_provisioner import BaseComputerProvisioner

logger = logging.getLogger(__name__)


class AWSProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        port: int = 8000,
        region: str = "us-west-2",
        instance_type: str = "t2.micro",
        image_id: str = None,
        security_groups: List[str] = None,
        max_retries: int = 3,
        timeout: int = 300,  # 5 minutes
    ):
        super().__init__(port)
        self.region = region
        self.instance_type = instance_type
        self.instance_id = None
        self.image_id = image_id or "ami-commandlab"  # Default AMI ID
        self.security_groups = security_groups or ["commandlab-daemon"]
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"
        self.ec2 = boto3.client("ec2", region_name=self.region)

    def setup(self) -> None:
        self._status = "starting"
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Launch EC2 instance with the CommandLAB AMI
                logger.info(f"Launching EC2 instance with image {self.image_id}")
                response = self.ec2.run_instances(
                    ImageId=self.image_id,
                    InstanceType=self.instance_type,
                    MinCount=1,
                    MaxCount=1,
                    SecurityGroups=self.security_groups,
                    UserData=f"""#!/bin/bash
                        pip install commandlab[local,daemon]
                        python -m commandlab.daemon.daemon --port {self.port} --backend pynput
                    """,
                )
                self.instance_id = response["Instances"][0]["InstanceId"]
                logger.info(f"Successfully launched instance {self.instance_id}")

                # Wait for instance to be running
                logger.info(f"Waiting for instance {self.instance_id} to be running")
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(f"Instance {self.instance_id} is now running")
                        return
                    time.sleep(5)

                # If we get here, the instance didn't start in time
                self._status = "error"
                logger.error(
                    f"Timeout waiting for instance {self.instance_id} to start"
                )
                raise TimeoutError(
                    f"Timeout waiting for instance {self.instance_id} to start"
                )

            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    logger.error(
                        f"Failed to launch EC2 instance after {self.max_retries} attempts: {e}"
                    )
                    raise
                logger.warning(
                    f"Error launching EC2 instance, retrying ({retry_count}/{self.max_retries}): {e}"
                )
                time.sleep(2**retry_count)  # Exponential backoff

    def teardown(self) -> None:
        if not self.instance_id:
            return

        self._status = "stopping"
        logger.info(f"Terminating instance {self.instance_id}")

        try:
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

            self._status = "stopped"
        except Exception as e:
            self._status = "error"
            logger.error(f"Error terminating instance {self.instance_id}: {e}")

    def is_running(self) -> bool:
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
