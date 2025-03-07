# Running commandAGI in the Cloud

This guide helps you run commandAGI daemons in various cloud container services without needing to manage full VMs.

## Quick Start

### AWS ECS (Elastic Container Service)

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.docker_provisioner import DockerPlatform

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.AWS_ECS,
    region="us-west-2"
)
```

### Azure Container Instances

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.docker_provisioner import DockerPlatform

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
    resource_group="my-resource-group",
    region="eastus"
)
```

### Google Cloud Run

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.docker_provisioner import DockerPlatform

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.GCP_CLOUD_RUN,
    project_id="my-project",
    region="us-central1"
)
```

## Managed Kubernetes Services

### Amazon EKS

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.kubernetes_provisioner import KubernetesPlatform

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.KUBERNETES,
    platform=KubernetesPlatform.AWS_EKS,
    cluster_name="my-cluster",
    region="us-west-2"
)
```

### Azure AKS

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.kubernetes_provisioner import KubernetesPlatform

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.KUBERNETES,
    platform=KubernetesPlatform.AZURE_AKS,
    cluster_name="my-cluster",
    resource_group="my-resource-group"
)
```

### Google GKE

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.computers.provisioners.kubernetes_provisioner import KubernetesPlatform

computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.KUBERNETES,
    platform=KubernetesPlatform.GCP_GKE,
    cluster_name="my-cluster",
    project_id="my-project",
    region="us-central1"
)
```

## Cost Considerations

- **AWS ECS with Fargate**: Pay only for resources used
- **Azure Container Instances**: Per-second billing
- **Google Cloud Run**: Pay-per-use pricing
- **Managed Kubernetes**: Additional cluster management costs

## Best Practices

1. **Right-size your resources**: Choose appropriate CPU and memory settings
2. **Clean up resources**: Always call `computer.close()` when done
3. **Monitor usage and costs**: Set up billing alerts
4. **Use auto-scaling**: Configure scaling policies for variable workloads
5. **Consider regional pricing**: Choose regions with lower costs when possible

## Security Considerations

1. **API Token Security**: Store API tokens securely
2. **Network Access**: Limit network exposure of your daemon
3. **IAM Permissions**: Use least-privilege permissions
4. **Image Security**: Scan container images for vulnerabilities
5. **Data Protection**: Be careful with sensitive data in containers

## Troubleshooting

### Common Issues

- **Connection Timeouts**: Check network connectivity and security groups
- **Authentication Failures**: Verify credentials and API tokens
- **Resource Limits**: Check if you've hit quota limits
- **Image Pull Errors**: Ensure your container registry is accessible

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Create computer with debug logging
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.AWS_ECS,
    region="us-west-2"
)
