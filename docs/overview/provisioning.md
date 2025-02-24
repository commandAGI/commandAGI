# Provisioning

## Container Services

### Docker Platforms

CommandLAB supports multiple Docker deployment platforms:

```python
from commandLAB.computers.provisioners.docker_provisioner import DockerPlatform

# Local Docker
provisioner = DockerProvisioner(
    platform=DockerPlatform.LOCAL,
    port=8000
)

# AWS ECS
provisioner = DockerProvisioner(
    platform=DockerPlatform.AWS_ECS,
    region="us-west-2",
    port=8000
)

# Azure Container Instances
provisioner = DockerProvisioner(
    platform=DockerPlatform.AZURE_CONTAINER_INSTANCES,
    resource_group="my-rg",
    region="eastus",
    port=8000
)

# Google Cloud Run
provisioner = DockerProvisioner(
    platform=DockerPlatform.GCP_CLOUD_RUN,
    project_id="my-project",
    region="us-central1",
    port=8000
)
```

### Kubernetes Platforms

Support for various Kubernetes distributions:

```python
from commandLAB.computers.provisioners.kubernetes_provisioner import KubernetesPlatform

# Local Kubernetes/Minikube
provisioner = KubernetesProvisioner(
    platform=KubernetesPlatform.LOCAL,
    namespace="default"
)

# Amazon EKS
provisioner = KubernetesProvisioner(
    platform=KubernetesPlatform.AWS_EKS,
    cluster_name="my-cluster",
    region="us-west-2"
)

# Azure AKS
provisioner = KubernetesProvisioner(
    platform=KubernetesPlatform.AZURE_AKS,
    cluster_name="my-cluster",
    resource_group="my-rg"
)

# Google GKE
provisioner = KubernetesProvisioner(
    platform=KubernetesPlatform.GCP_GKE,
    cluster_name="my-cluster",
    project_id="my-project",
    region="us-central1"
)
```

## Implementation Details

### Docker Provisioner

The DockerProvisioner handles:
- Container creation and management
- Port mapping
- Platform-specific configurations
- Health checking
- Resource cleanup

### Kubernetes Provisioner

The KubernetesProvisioner manages:
- Deployment creation
- Service exposure
- Load balancer configuration
- Cluster authentication
- Resource lifecycle

## Cloud Provider Requirements

### AWS
- AWS credentials configured
- ECS cluster (for Docker)
- EKS cluster (for Kubernetes)
- Appropriate IAM roles

### Azure
- Azure credentials configured
- Resource group
- AKS cluster (for Kubernetes)
- Service principal or managed identity

### GCP
- GCP credentials configured
- Project configured
- GKE cluster (for Kubernetes)
- Appropriate IAM roles 