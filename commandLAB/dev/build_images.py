import os
import subprocess
import logging
import sys
from typing import Optional, List, Dict, Any
import typer
from commandLAB.version import get_container_version, get_package_version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("build_images")

cli = typer.Typer(help="Build CommandLAB daemon images for different platforms")


def get_base_paths():
    """Get base directory paths for resources"""
    # First check if resources are in the dev directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dev_resources_path = os.path.join(base_dir, "resources")

    # If not found, check if resources are at project root
    if not os.path.exists(dev_resources_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    dockerfile_path = os.path.join(base_dir, "resources", "docker")
    packer_path = os.path.join(base_dir, "resources", "packer")

    # Create packer directory if it doesn't exist
    os.makedirs(packer_path, exist_ok=True)

    return base_dir, dockerfile_path, packer_path


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command with proper error handling and logging"""
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed with exit code {e.returncode}")
        logger.error(f"Command output: {e.stdout}")
        logger.error(f"Command error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"{description} failed with exception: {e}")
        return False


def ensure_packer_template(
    template_path: str, template_content: Dict[str, Any]
) -> None:
    """Ensure the packer template exists with the correct content"""
    import json

    if not os.path.exists(template_path):
        logger.info(f"Creating packer template: {template_path}")
        with open(template_path, "w") as f:
            json.dump(template_content, f, indent=2)
    else:
        logger.info(f"Packer template already exists: {template_path}")


@cli.command()
def build_docker_image(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build the Docker image for the daemon"""
    _, dockerfile_path, _ = get_base_paths()

    if not os.path.exists(os.path.join(dockerfile_path, "Dockerfile")):
        logger.error(f"Dockerfile not found at {dockerfile_path}")
        return

    cmd = [
        "docker",
        "build",
        "-t",
        f"commandlab-daemon:{version}",
        "--build-arg",
        f"VERSION={get_package_version()}",
        "-f",
        os.path.join(dockerfile_path, "Dockerfile"),
        ".",
    ]
    run_command(cmd, "Docker image build")


@cli.command()
def build_aws_ami(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build AWS AMI using Packer"""
    base_dir, _, packer_path = get_base_paths()

    # Define AWS packer template
    aws_template = {
        "variables": {
            "version": "{{env `VERSION`}}",
            "region": "us-west-2",
            "instance_type": "t2.micro",
        },
        "builders": [
            {
                "type": "amazon-ebs",
                "region": "{{user `region`}}",
                "instance_type": "{{user `instance_type`}}",
                "source_ami_filter": {
                    "filters": {
                        "virtualization-type": "hvm",
                        "name": "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*",
                        "root-device-type": "ebs",
                    },
                    "owners": ["099720109477"],
                    "most_recent": true,
                },
                "ssh_username": "ubuntu",
                "ami_name": "commandlab-daemon-{{user `version`}}-{{timestamp}}",
                "ami_description": "CommandLAB daemon image",
                "tags": {"Name": "commandlab-daemon", "Version": "{{user `version`}}"},
            }
        ],
        "provisioners": [
            {
                "type": "shell",
                "inline": [
                    "sudo apt-get update",
                    "sudo apt-get install -y python3 python3-pip",
                    "sudo pip3 install commandlab[local,daemon]=={{user `version`}}",
                ],
            }
        ],
    }

    aws_template_path = os.path.join(packer_path, "aws.json")
    ensure_packer_template(aws_template_path, aws_template)

    cmd = ["packer", "build", "-var", f"version={version}", aws_template_path]
    run_command(cmd, "AWS AMI build")


@cli.command()
def build_azure_vm(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build Azure VM image using Packer"""
    base_dir, _, packer_path = get_base_paths()

    # Define Azure packer template
    azure_template = {
        "variables": {
            "version": "{{env `VERSION`}}",
            "client_id": "{{env `AZURE_CLIENT_ID`}}",
            "client_secret": "{{env `AZURE_CLIENT_SECRET`}}",
            "subscription_id": "{{env `AZURE_SUBSCRIPTION_ID`}}",
            "tenant_id": "{{env `AZURE_TENANT_ID`}}",
            "location": "eastus",
        },
        "builders": [
            {
                "type": "azure-arm",
                "client_id": "{{user `client_id`}}",
                "client_secret": "{{user `client_secret`}}",
                "subscription_id": "{{user `subscription_id`}}",
                "tenant_id": "{{user `tenant_id`}}",
                "managed_image_resource_group_name": "commandlab-rg",
                "managed_image_name": "commandlab-daemon-{{user `version`}}",
                "os_type": "Linux",
                "image_publisher": "Canonical",
                "image_offer": "UbuntuServer",
                "image_sku": "18.04-LTS",
                "location": "{{user `location`}}",
                "vm_size": "Standard_DS1_v2",
            }
        ],
        "provisioners": [
            {
                "type": "shell",
                "inline": [
                    "sudo apt-get update",
                    "sudo apt-get install -y python3 python3-pip",
                    "sudo pip3 install commandlab[local,daemon]=={{user `version`}}",
                ],
            }
        ],
    }

    azure_template_path = os.path.join(packer_path, "azure.json")
    ensure_packer_template(azure_template_path, azure_template)

    cmd = ["packer", "build", "-var", f"version={version}", azure_template_path]
    run_command(cmd, "Azure VM image build")


@cli.command()
def build_gcp_vm(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build GCP VM image using Packer"""
    base_dir, _, packer_path = get_base_paths()

    # Define GCP packer template
    gcp_template = {
        "variables": {
            "version": "{{env `VERSION`}}",
            "project_id": "{{env `GCP_PROJECT_ID`}}",
            "zone": "us-central1-a",
        },
        "builders": [
            {
                "type": "googlecompute",
                "project_id": "{{user `project_id`}}",
                "source_image_family": "ubuntu-2004-lts",
                "source_image_project_id": "ubuntu-os-cloud",
                "zone": "{{user `zone`}}",
                "image_name": "commandlab-daemon-{{user `version`}}-{{timestamp}}",
                "image_description": "CommandLAB daemon image",
                "ssh_username": "ubuntu",
            }
        ],
        "provisioners": [
            {
                "type": "shell",
                "inline": [
                    "sudo apt-get update",
                    "sudo apt-get install -y python3 python3-pip",
                    "sudo pip3 install commandlab[local,daemon]=={{user `version`}}",
                ],
            }
        ],
    }

    gcp_template_path = os.path.join(packer_path, "gcp.json")
    ensure_packer_template(gcp_template_path, gcp_template)

    cmd = ["packer", "build", "-var", f"version={version}", gcp_template_path]
    run_command(cmd, "GCP VM image build")


@cli.command()
def build_kubernetes_image(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build Docker image for Kubernetes deployment"""
    # This is essentially the same as the Docker image but with a different tag
    _, dockerfile_path, _ = get_base_paths()

    if not os.path.exists(os.path.join(dockerfile_path, "Dockerfile")):
        logger.error(f"Dockerfile not found at {dockerfile_path}")
        return

    cmd = [
        "docker",
        "build",
        "-t",
        f"commandlab-daemon-k8s:{version}",
        "--build-arg",
        f"VERSION={get_package_version()}",
        "-f",
        os.path.join(dockerfile_path, "Dockerfile"),
        ".",
    ]
    run_command(cmd, "Kubernetes Docker image build")


@cli.command()
def build_all_images(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the images (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build images for all platforms"""
    logger.info("Starting build of all images")

    # Build Docker image
    logger.info("Building Docker image...")
    build_docker_image(version)

    # Build Kubernetes image
    logger.info("Building Kubernetes image...")
    build_kubernetes_image(version)

    # Check if packer is installed before attempting to build cloud images
    try:
        subprocess.run(["packer", "--version"], check=True, capture_output=True)

        # Build AWS AMI
        logger.info("Building AWS AMI...")
        build_aws_ami(version)

        # Build Azure VM image
        logger.info("Building Azure image...")
        build_azure_vm(version)

        # Build GCP VM image
        logger.info("Building GCP image...")
        build_gcp_vm(version)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Packer not found. Skipping cloud image builds.")
        logger.info(
            "To build cloud images, please install Packer: https://www.packer.io/downloads"
        )

    logger.info("All image builds completed")


if __name__ == "__main__":
    cli()
