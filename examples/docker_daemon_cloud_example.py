#!/usr/bin/env python3
"""
Docker Daemon Cloud Example

This example demonstrates how to use the Docker provisioner with cloud platforms
(AWS ECS, Azure Container Instances, GCP Cloud Run) to create a daemon computer client
and send commands to it.

Note: This example requires:
1. Docker to be installed and running on your system
2. Appropriate cloud provider credentials configured
3. Required cloud SDKs installed

Usage:
    python docker_daemon_cloud_example.py [aws|azure|gcp]
"""

import sys
import time
import argparse
from pathlib import Path

from commandLAB.computers.daemon_client_computer import DaemonClientComputer
from commandLAB.computers.provisioners.docker_provisioner import (
    DockerProvisioner,
    DockerPlatform,
)
from commandLAB.version import get_container_version
from commandLAB.types import (
    KeyboardKey,
    MouseButton,
    TypeAction,
    MouseMoveAction,
    ClickAction,
    KeyboardHotkeyAction,
    ShellCommandAction,
)


def setup_aws_ecs_computer():
    """Set up a Docker daemon computer on AWS ECS."""
    print("=== Setting up AWS ECS Docker Daemon ===")

    # Create a Docker provisioner for AWS ECS
    provisioner = DockerProvisioner(
        port=8000,
        platform=DockerPlatform.AWS_ECS,
        container_name="commandlab-daemon-aws",
        version=get_container_version(),
        region="us-west-2",  # Change to your preferred AWS region
        subnets=["subnet-xxxxxxxx"],  # Replace with your subnet IDs
        security_groups=["sg-xxxxxxxx"],  # Replace with your security group IDs
        max_retries=3,
        timeout=300,  # 5 minutes timeout for cloud setup
    )

    # Create a daemon client computer with the AWS ECS provisioner
    computer = DaemonClientComputer(
        daemon_base_url="http://your-ecs-service-url",  # This will be determined during setup
        daemon_port=8000,
        daemon_token="my-token",  # This should match the token used in the daemon
        provisioner=provisioner,
    )

    return computer


def setup_azure_container_instances_computer():
    """Set up a Docker daemon computer on Azure Container Instances."""
    print("=== Setting up Azure Container Instances Docker Daemon ===")

    # Create a Docker provisioner for Azure Container Instances
    provisioner = DockerProvisioner(
        port=8000,
        platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
        container_name="commandlab-daemon-azure",
        version=get_container_version(),
        resource_group="my-resource-group",  # Replace with your resource group
        subscription_id="your-subscription-id",  # Replace with your subscription ID
        max_retries=3,
        timeout=300,  # 5 minutes timeout for cloud setup
    )

    # Create a daemon client computer with the Azure Container Instances provisioner
    computer = DaemonClientComputer(
        daemon_base_url="http://your-aci-service-url",  # This will be determined during setup
        daemon_port=8000,
        daemon_token="my-token",  # This should match the token used in the daemon
        provisioner=provisioner,
    )

    return computer


def setup_gcp_cloud_run_computer():
    """Set up a Docker daemon computer on GCP Cloud Run."""
    print("=== Setting up GCP Cloud Run Docker Daemon ===")

    # Create a Docker provisioner for GCP Cloud Run
    provisioner = DockerProvisioner(
        port=8000,
        platform=DockerPlatform.GCP_CLOUD_RUN,
        container_name="commandlab-daemon-gcp",
        version=get_container_version(),
        project_id="your-gcp-project-id",  # Replace with your GCP project ID
        region="us-central1",  # Change to your preferred GCP region
        max_retries=3,
        timeout=300,  # 5 minutes timeout for cloud setup
    )

    # Create a daemon client computer with the GCP Cloud Run provisioner
    computer = DaemonClientComputer(
        daemon_base_url="http://your-cloud-run-url",  # This will be determined during setup
        daemon_port=8000,
        daemon_token="my-token",  # This should match the token used in the daemon
        provisioner=provisioner,
    )

    return computer


def run_example_commands(computer):
    """Run example commands on the daemon computer."""
    try:
        print("Docker container started successfully!")
        print("Waiting for daemon to be ready...")
        time.sleep(5)  # Give the daemon time to start in the cloud

        # Example 1: Get system information
        print("\n=== Example 1: Get System Information ===")
        success = computer.shell(command="uname -a")
        print(f"Command execution success: {success}")

        # Example 2: Type some text
        print("\n=== Example 2: Typing Text ===")
        success = computer.execute_type(text="Hello from CommandLAB Cloud!")
        print(f"Type action success: {success}")

        # Example 3: Take a screenshot
        print("\n=== Example 3: Taking Screenshot ===")
        screenshot = computer.get_screenshot(format="path")
        if screenshot and screenshot.path:
            print(f"Screenshot saved to: {screenshot.path}")
        else:
            print("Failed to take screenshot")

        # Example 4: Get observation
        print("\n=== Example 4: Getting Observation ===")
        observation = computer.get_observation()
        print(
            "Observation keys:",
            list(observation.keys()) if observation else "No observation data",
        )

        print("\nAll examples completed successfully!")

    except Exception as e:
        print(f"Error running commands: {e}")


def main():
    parser = argparse.ArgumentParser(description="Run Docker daemon on cloud platforms")
    parser.add_argument(
        "platform",
        choices=["aws", "azure", "gcp", "local"],
        help="Cloud platform to use (aws, azure, gcp, or local)",
    )

    if len(sys.argv) < 2:
        parser.print_help()
        return

    args = parser.parse_args()

    computer = None
    try:
        # Set up the computer based on the selected platform
        if args.platform == "aws":
            computer = setup_aws_ecs_computer()
        elif args.platform == "azure":
            computer = setup_azure_container_instances_computer()
        elif args.platform == "gcp":
            computer = setup_gcp_cloud_run_computer()
        elif args.platform == "local":
            # Create a Docker provisioner for local
            provisioner = DockerProvisioner(
                port=8000,
                platform=DockerPlatform.LOCAL,
                container_name="commandlab-daemon-local",
                version=get_container_version(),
                max_retries=3,
                timeout=60,  # 1 minute timeout
            )

            # Create a daemon client computer with the local Docker provisioner
            computer = DaemonClientComputer(
                daemon_base_url="http://localhost",
                daemon_port=8000,
                daemon_token="my-token",
                provisioner=provisioner,
            )

        # Run example commands on the computer
        if computer:
            run_example_commands(computer)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if computer:
            print("\nCleaning up resources...")
            computer.stop()
            print(f"Docker container on {args.platform} stopped and removed.")


if __name__ == "__main__":
    main()
