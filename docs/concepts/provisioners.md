# Provisioners

**Provisioners** in CommandLAB handle the setup, management, and teardown of computer environments. They're especially useful for cloud and container deployments.

![Provisioner Architecture](../assets/images/provisioner_architecture.png)

## What is a Provisioner?

A provisioner is responsible for:

1. **Setting up** a computer environment (e.g., starting a Docker container)
2. **Checking** if the environment is running
3. **Tearing down** the environment when it's no longer needed

This allows CommandLAB to work with ephemeral environments that can be created and destroyed as needed.

## The BaseComputerProvisioner Interface

All provisioners implement the `BaseComputerProvisioner` interface:

```python
class BaseComputerProvisioner:
    def __init__(self, port: int = 8000):
        self.port = port
        
    def setup(self) -> None:
        """Setup the computer environment"""
        
    def teardown(self) -> None:
        """Cleanup resources"""
        
    def is_running(self) -> bool:
        """Check if the environment is running"""
        
    def get_status(self) -> str:
        """Get the current status of the provisioner"""
        return self._status
```

## Available Provisioners

CommandLAB includes provisioners for various deployment options:

### ManualProvisioner

Provides instructions for manual setup:

```python
from commandLAB.computers.provisioners.manual_provisioner import ManualProvisioner

provisioner = ManualProvisioner(port=8000)
provisioner.setup()  # Prints instructions
```

### DockerProvisioner

Deploys environments in Docker containers:

```python
from commandLAB.computers.provisioners.docker_provisioner import DockerProvisioner, DockerPlatform

provisioner = DockerProvisioner(
    port=8000,
    platform=DockerPlatform.LOCAL
)
provisioner.setup()  # Creates and starts a Docker container
```

### KubernetesProvisioner

Manages deployments in Kubernetes clusters:

```python
from commandLAB.computers.provisioners.kubernetes_provisioner import KubernetesProvisioner, KubernetesPlatform

provisioner = KubernetesProvisioner(
    port=8000,
    platform=KubernetesPlatform.GCP_GKE,
    namespace="commandlab"
)
```

### Cloud Provisioners

Provision VMs in various cloud providers:

```python
# AWS EC2
from commandLAB.computers.provisioners.aws_provisioner import AWSProvisioner
provisioner = AWSProvisioner(region="us-west-2")

# Azure VM
from commandLAB.computers.provisioners.azure_provisioner import AzureProvisioner
provisioner = AzureProvisioner(resource_group="my-resource-group")

# Google Cloud
from commandLAB.computers.provisioners.gcp_provisioner import GCPProvisioner
provisioner = GCPProvisioner(project="my-project")
```

## How Provisioners Work with Computers

The `DaemonClientComputer` uses provisioners to manage its environment:

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer with Docker provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER
)

# This automatically:
# 1. Creates a provisioner based on the method
# 2. Calls provisioner.setup() to create the environment
# 3. Connects to the daemon in that environment

# When you're done:
computer.close()  # Calls provisioner.teardown()
```

## Creating Custom Provisioners

You can create custom provisioners by implementing the `BaseComputerProvisioner` interface:

```python
from commandLAB.computers.provisioners.base_provisioner import BaseComputerProvisioner

class MyCustomProvisioner(BaseComputerProvisioner):
    def setup(self) -> None:
        # Your setup logic here
        
    def teardown(self) -> None:
        # Your cleanup logic here
        
    def is_running(self) -> bool:
        # Your status check logic here
```

This allows you to integrate CommandLAB with any infrastructure or deployment system.

## Advanced Features

The provisioners in CommandLAB include several advanced features:

- **Retry Logic**: Automatically retry operations that fail transiently
- **Timeouts**: Prevent operations from hanging indefinitely
- **Status Tracking**: Monitor the state of resources
- **Logging**: Detailed logging for troubleshooting
- **Resource Cleanup**: Ensure proper cleanup of all resources

## Further Reading

- [Using Provisioners Guide](../guides/provisioners.md) - A user-focused guide on using provisioners
- [Provisioner System for Developers](../developers/provisioners.md) - Detailed information for library developers
- [Cloud Containers Guide](../guides/cloud_containers.md) - Guide for running CommandLAB in cloud container services