#!/usr/bin/env python3
"""
CommandLAB Docker Example

This example demonstrates how to use the Docker provisioner to create and control
a Docker container.

Note: This example requires Docker to be installed and running on your system.

Status: ⚠️ Works with limitations
- Handles the error gracefully when the Docker image doesn't exist
- Provides helpful information about building the image
"""

import time

from commandLAB.computers.provisioners.qemu_provisioner import QEMUProvisioner
from commandLAB.computers.provisioners.virtualbox_provisioner import VirtualBoxProvisioner

try:
    from commandLAB.computers.provisioners.docker_provisioner import (
        DockerProvisioner,
        DockerPlatform,
    )
    from commandLAB.version import get_container_version
except ImportError:
    print(
        "Error: Required modules not found. Make sure CommandLAB is installed with the Docker extra:"
    )
    print("pip install commandlab[docker]")
    exit(1)


def main():
    print("Creating a Docker container...")

    try:
        # Create a Docker provisioner directly
        provisioner = DockerProvisioner(
            port=8000,
            platform=DockerPlatform.LOCAL,
            container_name="commandlab-example",
            version=get_container_version(),  # Use the default container version
            max_retries=3,
            timeout=60,  # 1 minute timeout
        )

        print("Setting up the Docker container...")
        print("This may take a while if the image needs to be pulled...")

        try:
            print("Provisioner status:", provisioner.get_status())
            provisioner.setup()
            print("Provisioner status:", provisioner.get_status())
            print("Docker container started successfully!")

            # Check if the container is running
            if provisioner.is_running():
                print("Container is running!")
            else:
                print("Container is not running.")

            print("Waiting for container to be ready...")
            time.sleep(5)  # Give the container time to start

        except Exception as setup_error:
            print(f"Error setting up container: {setup_error}")
            print("This may be because the Docker image doesn't exist.")
            print("You would normally need to build the image first using:")
            print(
                "poetry run python -m commandLAB.dev.dev_cli build build_docker_image"
            )

        print("\nExample completed!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if "provisioner" in locals():
            print("Cleaning up Docker container...")
            try:
                provisioner.teardown()
                print("Docker container stopped and removed.")
            except Exception as cleanup_error:
                print(f"Error cleaning up container: {cleanup_error}")


if __name__ == "__main__":
    main()
