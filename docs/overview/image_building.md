# Building Images

CommandLAB provides tools for building daemon images across different platforms using the `build_images.py` script.

## Prerequisites

- Docker (for Docker images)
- Packer (for cloud provider images)
- Cloud provider CLI tools configured:
  - AWS CLI
  - Azure CLI
  - Google Cloud SDK

## Usage

### Basic Usage

Build images for all platforms:

```bash
python -m commandLAB.build_images --platforms docker aws azure gcp --version 1.0.0
```

Build for specific platforms:

```bash
# Build only Docker image
python -m commandLAB.build_images --platforms docker --version latest

# Build AWS and Azure images
python -m commandLAB.build_images --platforms aws azure --version 1.0.0
```

### Platform-Specific Details

#### Docker Images

The Docker image includes:

- Python environment with CommandLAB installed
- Required system dependencies
- Daemon configuration

#### AWS AMI

The AWS AMI includes:

- Base Ubuntu image
- Python environment
- CommandLAB daemon
- Startup scripts

#### Azure VM Image

The Azure VM image includes:

- Base Ubuntu image
- Python environment
- CommandLAB daemon
- Azure-specific configurations

#### GCP VM Image

The GCP VM image includes:

- Base Ubuntu image
- Python environment
- CommandLAB daemon
- GCP-specific configurations

## Custom Image Building

You can customize the image building process by modifying:

- `resources/docker/Dockerfile` - Docker image definition
- `resources/packer/aws.json` - AWS AMI template
- `resources/packer/azure.json` - Azure VM image template
- `resources/packer/gcp.json` - GCP VM image template

Example Dockerfile customization:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# Install CommandLAB
RUN pip install commandlab[local,daemon]

# Copy daemon configuration
COPY resources/daemon/config.json /etc/commandlab/

# Set startup command
CMD ["python", "-m", "commandlab.daemon.daemon", "--port", "8000", "--backend", "pynput"]
```

## Container Registry Support

### Cloud Provider Registries

Build and push to cloud container registries:

```bash
# AWS ECR
python -m commandLAB.build_images --platforms docker --registry aws-ecr --region us-west-2

# Azure Container Registry
python -m commandLAB.build_images --platforms docker --registry azure-acr --resource-group my-rg

# Google Container Registry
python -m commandLAB.build_images --platforms docker --registry gcr --project my-project
```

## Registry Configuration

### AWS ECR

```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com
```

### Azure Container Registry

```bash
az acr login --name myregistry
```

### Google Container Registry

```bash
gcloud auth configure-docker
```
