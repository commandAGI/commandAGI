# Provisioner System for Developers

This guide provides detailed information about the CommandLAB provisioner system for library developers who want to extend or modify the system.

## Architecture Overview

The provisioner system is designed to handle the setup, management, and teardown of computer environments across various platforms. It follows a modular architecture with the following components:

1. **BaseComputerProvisioner**: Abstract base class that defines the common interface for all provisioners
1. **Platform-specific Provisioners**: Concrete implementations for different platforms (AWS, Azure, GCP, Docker, Kubernetes)
1. **Build System**: Tools for building and packaging images for different platforms

## BaseComputerProvisioner Interface

All provisioners implement the `BaseComputerProvisioner` interface:

```python
class BaseComputerProvisioner(ABC):
    def __init__(self, port: int = 8000):
        self.port = port
        
    @abstractmethod
    def setup(self) -> None:
        """Setup the computer environment"""
        
    @abstractmethod
    def teardown(self) -> None:
        """Cleanup resources"""
        
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the environment is running"""
        
    def get_status(self) -> str:
        """Get the current status of the provisioner"""
        return self._status
```

## Common Implementation Patterns

All provisioners follow these common implementation patterns:

### Status Tracking

Provisioners track their status using a `_status` field with these standard values:

- `"not_started"`: Initial state
- `"starting"`: During setup
- `"running"`: Successfully running
- `"stopping"`: During teardown
- `"stopped"`: Successfully stopped
- `"error"`: Error state

### Logging

Provisioners use Python's standard logging module:

```python
import logging
logger = logging.getLogger(__name__)

# Usage
logger.info("Starting setup...")
logger.error(f"Error during setup: {e}")
```

### Error Handling

Provisioners implement robust error handling with retry logic:

```python
retry_count = 0
while retry_count < self.max_retries:
    try:
        # Setup logic
        return
    except Exception as e:
        retry_count += 1
        if retry_count >= self.max_retries:
            self._status = "error"
            logger.error(f"Failed after {self.max_retries} attempts: {e}")
            raise
        logger.warning(f"Error, retrying ({retry_count}/{self.max_retries}): {e}")
        time.sleep(2 ** retry_count)  # Exponential backoff
```

### Timeouts

Provisioners implement timeouts for long-running operations:

```python
start_time = time.time()
while time.time() - start_time < self.timeout:
    if self.is_running():
        return True
    time.sleep(5)
raise TimeoutError("Operation timed out")
```

## Platform-Specific Provisioners

### AWS Provisioner

The AWS provisioner uses boto3 to create and manage EC2 instances:

```python
class AWSProvisioner(BaseComputerProvisioner):
    def __init__(
        self, 
        port: int = 8000, 
        region: str = "us-west-2", 
        instance_type: str = "t2.micro",
        image_id: str = None,
        security_groups: List[str] = None,
        max_retries: int = 3,
        timeout: int = 300
    ):
        # ...
```

Key implementation details:

- Uses boto3 EC2 client
- Configurable AMI ID and security groups
- Implements retry logic and timeouts
- Tracks instance state

### Azure Provisioner

The Azure provisioner uses the Azure SDK to create and manage VMs:

```python
class AzureProvisioner(BaseComputerProvisioner):
    def __init__(
        self, 
        port: int = 8000, 
        resource_group: str = "commandlab-rg", 
        location: str = "eastus", 
        vm_size: str = "Standard_DS1_v2",
        subscription_id: str = None, 
        image_id: str = None,
        max_retries: int = 3, 
        timeout: int = 600
    ):
        # ...
```

Key implementation details:

- Uses Azure Compute Management Client
- Supports environment variable fallback for credentials
- Configurable VM size and image ID

### GCP Provisioner

The GCP provisioner uses the Google Cloud SDK to create and manage VMs:

```python
class GCPProvisioner(BaseComputerProvisioner):
    def __init__(
        self, 
        port: int = 8000, 
        project: str = None, 
        zone: str = "us-central1-a", 
        machine_type: str = "n1-standard-1",
        source_image: str = None,
        max_retries: int = 3,
        timeout: int = 600
    ):
        # ...
```

Key implementation details:

- Uses Google Cloud Compute API
- Configurable project, zone, and machine type
- Configurable source image

### Docker Provisioner

The Docker provisioner supports multiple container platforms:

```python
class DockerProvisioner(BaseComputerProvisioner):
    def __init__(
        self, 
        port: int = 8000, 
        container_name: str = "commandlab-daemon",
        platform: DockerPlatform = DockerPlatform.LOCAL,
        version: Optional[str] = None,
        region: str = None,
        resource_group: str = None,
        project_id: str = None,
        subnets: List[str] = None,
        security_groups: List[str] = None,
        subscription_id: str = None,
        max_retries: int = 3,
        timeout: int = 300
    ):
        # ...
```

Key implementation details:

- Supports multiple platforms (LOCAL, AWS_ECS, AZURE_CONTAINER_INSTANCES, GCP_CLOUD_RUN)
- Platform-specific setup and teardown methods
- Configurable container name and version

### Kubernetes Provisioner

The Kubernetes provisioner supports multiple Kubernetes platforms:

```python
class KubernetesProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        port: int = 8000,
        platform: KubernetesPlatform = KubernetesPlatform.LOCAL,
        namespace: str = "default",
        cluster_name: Optional[str] = None,
        region: Optional[str] = None,
        resource_group: Optional[str] = None,
        project_id: Optional[str] = None,
        version: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 300
    ):
        # ...
```

Key implementation details:

- Supports multiple platforms (LOCAL, AWS_EKS, AZURE_AKS, GCP_GKE)
- Creates Kubernetes deployments and services
- Configurable namespace and cluster

## Build System

The build system is responsible for creating images for different platforms:

### Build Images CLI

The `build_images.py` script provides a CLI for building images:

```python
cli = typer.Typer(help="Build CommandLAB daemon images for different platforms")

@cli.command()
def build_docker_image(version: Optional[str] = ...):
    """Build the Docker image for the daemon"""
    # ...

@cli.command()
def build_aws_ami(version: Optional[str] = ...):
    """Build AWS AMI using Packer"""
    # ...

@cli.command()
def build_azure_vm(version: Optional[str] = ...):
    """Build Azure VM image using Packer"""
    # ...

@cli.command()
def build_gcp_vm(version: Optional[str] = ...):
    """Build GCP VM image using Packer"""
    # ...

@cli.command()
def build_kubernetes_image(version: Optional[str] = ...):
    """Build Docker image for Kubernetes deployment"""
    # ...

@cli.command()
def build_all_images(version: Optional[str] = ...):
    """Build images for all platforms"""
    # ...
```

### Packer Templates

The build system automatically generates Packer templates for cloud platforms:

- AWS AMI template
- Azure VM template
- GCP VM template

These templates define how to build the images with the necessary dependencies.

## Extending the Provisioner System

### Creating a New Provisioner

To create a new provisioner:

1. Create a new class that inherits from `BaseComputerProvisioner`
1. Implement the required methods: `setup()`, `teardown()`, and `is_running()`
1. Follow the common implementation patterns for status tracking, logging, error handling, and timeouts

Example:

```python
class MyCustomProvisioner(BaseComputerProvisioner):
    def __init__(self, port: int = 8000, custom_param: str = "default"):
        super().__init__(port)
        self.custom_param = custom_param
        self._status = "not_started"
        
    def setup(self) -> None:
        self._status = "starting"
        # Implementation...
        self._status = "running"
        
    def teardown(self) -> None:
        self._status = "stopping"
        # Implementation...
        self._status = "stopped"
        
    def is_running(self) -> bool:
        # Implementation...
        return True
```

### Adding Build Support for a New Platform

To add build support for a new platform:

1. Add a new command to `build_images.py`
1. Implement the build logic for the new platform
1. Add the new command to `build_all_images()`

Example:

```python
@cli.command()
def build_my_platform(version: Optional[str] = ...):
    """Build image for my platform"""
    # Implementation...

# Update build_all_images
@cli.command()
def build_all_images(version: Optional[str] = ...):
    # Existing code...
    logger.info("Building My Platform image...")
    build_my_platform(version)
    # Rest of existing code...
```

## Best Practices

1. **Error Handling**: Always implement robust error handling with retry logic
1. **Logging**: Use the standard logging module with appropriate log levels
1. **Timeouts**: Implement timeouts for all long-running operations
1. **Status Tracking**: Use the standard status values for consistency
1. **Configuration**: Make all platform-specific parameters configurable
1. **Resource Cleanup**: Ensure proper cleanup in the `teardown()` method
1. **Validation**: Validate required parameters in the constructor

By following these guidelines, you can create robust and maintainable provisioners that integrate seamlessly with the CommandLAB ecosystem.
