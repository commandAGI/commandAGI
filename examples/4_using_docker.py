#!/usr/bin/env python3
"""
CommandLAB Docker Example

This example demonstrates how to use the Docker provisioner to create and control
a Docker container running the CommandLAB daemon.
"""

import time

try:
    from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
    from commandLAB.computers.provisioners.docker_provisioner import DockerPlatform
    from commandLAB.types import CommandAction, TypeAction
except ImportError:
    print("Error: Required modules not found. Make sure CommandLAB is installed with the Docker extra:")
    print("pip install commandlab[docker]")
    exit(1)

def main():
    print("Creating a DaemonClientComputer with Docker provisioning...")
    
    try:
        # Create a computer with Docker provisioning
        computer = DaemonClientComputer(
            provisioning_method=ProvisioningMethod.DOCKER,
            platform=DockerPlatform.LOCAL,
            container_name="commandlab-example"
        )
        
        print("Docker container started successfully!")
        print("Waiting for daemon to be ready...")
        time.sleep(5)  # Give the daemon time to start
        
        # Execute a command in the container
        print("Executing 'ls -la' command in the container...")
        result = computer.execute_command(CommandAction(
            command="ls -la",
            timeout=5
        ))
        
        print(f"Command execution {'succeeded' if result else 'failed'}")
        
        # Execute another command to show environment info
        print("Executing 'env' command to show environment variables...")
        result = computer.execute_command(CommandAction(
            command="env | sort",
            timeout=5
        ))
        
        print(f"Command execution {'succeeded' if result else 'failed'}")
        
        print("\nExample completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        if 'computer' in locals():
            print("Cleaning up Docker container...")
            computer.close()
            print("Docker container stopped and removed.")

if __name__ == "__main__":
    main()
