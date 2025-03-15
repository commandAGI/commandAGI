import time
from commandAGI.computers.computer import Computer
from commandAGI.computers.provisioners.docker_provisioner import DockerProvisioner

# Number of containers to create
num_containers = 10

# Create containers with dynamic port allocation
computers = []
for i in range(num_containers):
    # Create provisioner with a unique name and token
    provisioner = DockerProvisioner(
        container_name=f"commandagi-daemon-{i}",
        port_range=(8000, 9000),  # Use a port in this range
        daemon_token=f"token-for-container-{i}",
    )

    # Create computer with the provisioner
    computer = Computer(provisioner=provisioner)
    computers.append(computer)

    print(f"Container {i} started at {provisioner.daemon_url}")

    # Optional: Add a small delay between container starts
    time.sleep(1)

# Use the computers
for i, computer in enumerate(computers):
    result = computer.shell(f"echo 'Hello from container {i}'")
    print(f"Container {i} result: {result}")

# Clean up
for computer in computers:
    computer.stop()
