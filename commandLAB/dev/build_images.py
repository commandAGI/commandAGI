import os
from pathlib import Path
import subprocess
import logging
import sys
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.status import Status
from commandLAB.version import get_container_version, get_package_version

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("build_images")
console = Console()

cli = typer.Typer(help="Build CommandLAB daemon images for different platforms")


def get_base_paths():
    """Get base directory paths for resources"""
    with Status("[bold blue]Checking resource paths...", console=console):
        # First check if resources are in the dev directory
        base_dir = Path(__file__).parent.parent.parent
        dev_resources_path = base_dir / "resources"

        # If not found, check if resources are at project root
        if not dev_resources_path.exists():
            base_dir = Path(__file__).parent.parent

        dockerfile_path = base_dir / "resources" / "docker"
        packer_path = base_dir / "resources" / "packer"

        # Create packer directory if it doesn't exist
        packer_path.mkdir(parents=True, exist_ok=True)

    return base_dir, dockerfile_path, packer_path


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command with real-time stdout streaming and proper error handling and logging"""
    with Status(f"[bold blue]{description}...", console=console) as status:
        logger.info(f"Running: {' '.join(cmd)}")
        try:
            # Open the process and merge stdout and stderr
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            # Stream the output line by line
            while True:
                line = process.stdout.readline()
                if line:
                    console.print(line.rstrip())
                elif process.poll() is not None:
                    # No more output and the process is finished
                    break

            # Read and print any remaining output
            remainder = process.stdout.read()
            if remainder:
                console.print(remainder.rstrip())

            return_code = process.wait()
            if return_code == 0:
                status.update(f"[bold green]✓ {description} completed successfully")
                return True
            else:
                status.update(f"[bold red]✗ {description} failed")
                logger.error(f"{description} failed with exit code {return_code}")
                return False
        except Exception as e:
            status.update(f"[bold red]✗ {description} failed")
            logger.error(f"{description} failed with exception: {e}")
            return False


def ensure_packer_template(
    template_path: str, template_content: Dict[str, Any]
) -> None:
    """Ensure the packer template exists with the correct content"""
    import json

    with Status("[bold blue]Checking packer template...", console=console) as status:
        if not os.path.exists(template_path):
            status.update("[bold blue]Creating packer template...")
            with open(template_path, "w") as f:
                json.dump(template_content, f, indent=2)
            status.update("[bold green]✓ Packer template created")
        else:
            status.update("[bold green]✓ Packer template exists")


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
    console.print("[bold blue]Starting build of all images[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Build Docker image
        task = progress.add_task("Building Docker image...", total=None)
        build_docker_image(version)
        progress.update(task, completed=True)

        # Build Kubernetes image
        task = progress.add_task("Building Kubernetes image...", total=None)
        build_kubernetes_image(version)
        progress.update(task, completed=True)

        # Check if packer is installed before attempting to build cloud images
        try:
            subprocess.run(["packer", "--version"], check=True, capture_output=True)

            # Build AWS AMI
            task = progress.add_task("Building AWS AMI...", total=None)
            build_aws_ami(version)
            progress.update(task, completed=True)

            # Build Azure VM image
            task = progress.add_task("Building Azure image...", total=None)
            build_azure_vm(version)
            progress.update(task, completed=True)

            # Build GCP VM image
            task = progress.add_task("Building GCP image...", total=None)
            build_gcp_vm(version)
            progress.update(task, completed=True)

        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[bold yellow]⚠️ Packer not found. Skipping cloud image builds.[/]")
            console.print(
                "[bold yellow]To build cloud images, please install Packer: https://www.packer.io/downloads[/]"
            )

    console.print("[bold green]✓ All image builds completed[/]")


if __name__ == "__main__":
    cli()
