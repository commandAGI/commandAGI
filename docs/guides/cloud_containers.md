# Running CommandLAB in the Cloud

This guide helps you run CommandLAB daemons in various cloud container services without needing to manage full VMs.

## Quick Start

### AWS ECS (Elastic Container Service)

```python
from commandLAB.computers import DaemonClientComputer
from commandLAB.computers.provisioners.docker_provisioner import DockerPlatform

computer = DaemonClientComputer(
    provisioning_method="docker",
    platform=DockerPlatform.AWS_ECS,
    region="us-west-2"
)
```

### Azure Container Instances

```python
computer = DaemonClientComputer(
    provisioning_method="docker",
    platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
    resource_group="my-resource-group",
    region="eastus"
)
```

### Google Cloud Run

```python
computer = DaemonClientComputer(
    provisioning_method="docker",
    platform=DockerPlatform.GCP_CLOUD_RUN,
    project_id="my-project",
    region="us-central1"
)
```

## Managed Kubernetes Services

### Amazon EKS

```python
from commandLAB.computers.provisioners.kubernetes_provisioner import KubernetesPlatform

computer = DaemonClientComputer(
    provisioning_method="kubernetes",
    platform=KubernetesPlatform.AWS_EKS,
    cluster_name="my-cluster",
    region="us-west-2"
)
```

### Azure AKS

```python
computer = DaemonClientComputer(
    provisioning_method="kubernetes",
    platform=KubernetesPlatform.AZURE_AKS,
    cluster_name="my-cluster",
    resource_group="my-resource-group"
)
```

### Google GKE

```python
computer = DaemonClientComputer(
    provisioning_method="kubernetes",
    platform=KubernetesPlatform.GCP_GKE,
    cluster_name="my-cluster",
    project_id="my-project",
    region="us-central1"
)
```

## Cost Considerations

- AWS ECS with Fargate: Pay only for resources used
- Azure Container Instances: Per-second billing
- Google Cloud Run: Pay-per-use pricing
- Managed Kubernetes: Additional cluster management costs

## Best Practices

1. Use appropriate instance sizes
2. Clean up resources when done
3. Monitor usage and costs
4. Use auto-scaling when possible
5. Consider regional pricing differences 