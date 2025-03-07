import time
from commandAGI.computers.daemon_client_computer import DaemonClientComputer
from commandAGI.computers.provisioners.docker_provisioner import DockerProvisioner

# Create first provisioner with default port (8000)
provisioner1 = DockerProvisioner(
    container_name="commandagi-daemon-1",
    daemon_token="token-for-container-1"
)

# Create second provisioner with a different port
provisioner2 = DockerProvisioner(
    container_name="commandagi-daemon-2", 
    daemon_port=8001,  # Request a different port
    daemon_token="token-for-container-2"
)

# Create third provisioner with port range
provisioner3 = DockerProvisioner(
    container_name="commandagi-daemon-3",
    port_range=(8100, 8200),  # Use a port in this range
    daemon_token="token-for-container-3"
)

# Create computers with the provisioners
computer1 = DaemonClientComputer(provisioner=provisioner1)
computer2 = DaemonClientComputer(provisioner=provisioner2)
computer3 = DaemonClientComputer(provisioner=provisioner3)

# Now you can use all three computers independently
print(f"Computer 1 daemon URL: {provisioner1.daemon_url}")
print(f"Computer 2 daemon URL: {provisioner2.daemon_url}")
print(f"Computer 3 daemon URL: {provisioner3.daemon_url}")

# Test operations on each computer
computer1.shell("echo 'Hello from container 1'")
computer2.shell("echo 'Hello from container 2'")
computer3.shell("echo 'Hello from container 3'")

# Clean up when done
computer1.stop()
computer2.stop()
computer3.stop()
