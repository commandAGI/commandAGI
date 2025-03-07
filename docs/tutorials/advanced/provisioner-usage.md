# Using Provisioners in commandAGI

Provisioners in commandAGI allow you to automatically set up and manage computer environments across different platforms. This guide explains how to use provisioners in your projects.

## What are Provisioners?

Provisioners handle the lifecycle of computer environments:

1. **Setup**: Creating and configuring the environment
2. **Status Checking**: Monitoring the environment's state
3. **Teardown**: Cleaning up resources when they're no longer needed

This allows you to work with ephemeral environments that can be created and destroyed as needed.

## Available Provisioners

commandAGI includes provisioners for various platforms:

### Local Docker

Run environments in Docker containers on your local machine:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.docker_provisioner import DockerPlatform

# Create a computer with local Docker provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.LOCAL
)

# Use the computer
# ...

# Clean up when done
computer.close()  # Stops and removes the container
```

### AWS

Run environments in AWS EC2 instances:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer with AWS provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.AWS,
    region="us-west-2",
    instance_type="t2.micro",
    image_id="ami-0123456789abcdef0",  # Optional: custom AMI ID
    security_groups=["my-security-group"]  # Optional: custom security groups
)

# Use the computer
# ...

# Clean up when done
computer.close()  # Terminates the EC2 instance
```

### Azure

Run environments in Azure VMs:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer with Azure provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.AZURE,
    resource_group="my-resource-group",
    location="eastus",
    vm_size="Standard_DS1_v2",
    subscription_id="your-subscription-id",  # Optional: can use AZURE_SUBSCRIPTION_ID env var
    image_id="your-image-id"  # Optional: custom image ID
)

# Use the computer
# ...

# Clean up when done
computer.close()  # Deletes the Azure VM
```

### Google Cloud Platform

Run environments in GCP VMs:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer with GCP provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.GCP,
    project="your-project-id",
    zone="us-central1-a",
    machine_type="n1-standard-1",
    source_image="your-image-id"  # Optional: custom image ID
)

# Use the computer
# ...

# Clean up when done
computer.close()  # Deletes the GCP VM
```

### Kubernetes

Run environments in Kubernetes clusters:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.kubernetes_provisioner import KubernetesPlatform

# Create a computer with Kubernetes provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.KUBERNETES,
    platform=KubernetesPlatform.GCP_GKE,  # Or AWS_EKS, AZURE_AKS, LOCAL
    namespace="my-namespace",
    cluster_name="my-cluster",
    project_id="my-project",  # For GCP_GKE
    region="us-central1"  # For AWS_EKS and GCP_GKE
)

# Use the computer
# ...

# Clean up when done
computer.close()  # Deletes the Kubernetes resources
```

### Container Services

Run environments in managed container services:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.docker_provisioner import DockerPlatform

# AWS ECS
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.AWS_ECS,
    region="us-west-2",
    subnets=["subnet-12345"],
    security_groups=["sg-12345"]
)

# Azure Container Instances
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
    region="eastus",
    resource_group="my-resource-group",
    subscription_id="your-subscription-id"
)

# Google Cloud Run
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.GCP_CLOUD_RUN,
    project_id="your-project-id",
    region="us-central1"
)

# Use the computer
# ...

# Clean up when done
computer.close()
```

## Advanced Configuration

### Timeouts and Retries

You can configure timeouts and retry behavior:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.AWS,
    region="us-west-2",
    max_retries=5,  # Default: 3
    timeout=600     # Default: 300 (5 minutes)
)
```

### Status Checking

You can check the status of a provisioner:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER
)

# Get the provisioner status
status = computer.provisioner.get_status()
print(f"Provisioner status: {status}")
# Possible values: "not_started", "starting", "running", "stopping", "stopped", "error"

# Check if the environment is running
is_running = computer.provisioner.is_running()
print(f"Is running: {is_running}")
```

## Best Practices

### Resource Management

Always clean up resources when you're done:

```python
try:
    computer = DaemonClientComputer(provisioning_method=ProvisioningMethod.AWS)
    # Use the computer
finally:
    computer.close()  # Ensure resources are cleaned up
```

### Error Handling

Handle potential errors during provisioning:

```python
try:
    computer = DaemonClientComputer(provisioning_method=ProvisioningMethod.AWS)
    # Use the computer
except Exception as e:
    print(f"Error during provisioning: {e}")
    # Handle the error
finally:
    if 'computer' in locals():
        computer.close()
```

### Environment Variables

Use environment variables for sensitive information:

```python
# Set environment variables
import os
os.environ["AZURE_SUBSCRIPTION_ID"] = "your-subscription-id"
os.environ["AZURE_CLIENT_ID"] = "your-client-id"
os.environ["AZURE_CLIENT_SECRET"] = "your-client-secret"
os.environ["AZURE_TENANT_ID"] = "your-tenant-id"

# Create computer without explicitly passing credentials
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.AZURE,
    resource_group="my-resource-group"
)
```

## Troubleshooting

### Common Issues

1. **Connection Timeouts**: Check network connectivity and security groups/firewall rules.
2. **Authentication Errors**: Verify your credentials and permissions.
3. **Resource Limits**: Check if you've reached your cloud provider's resource limits.
4. **Image Not Found**: Ensure the specified image ID exists and is accessible.

### Logging

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

- Learn about [Cloud Containers](cloud_containers.md) for more advanced cloud deployment options
- Explore [Computers](../concepts/computers.md) to understand how to interact with provisioned environments
- Check out the [Daemon](../concepts/daemon.md) documentation to learn about the remote control protocol
