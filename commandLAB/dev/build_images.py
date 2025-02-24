import os
import subprocess
from typing import Optional
import typer
from commandLAB.version import get_container_version, get_package_version

cli = typer.Typer(help="Build CommandLAB daemon images for different platforms")

def get_base_paths():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dockerfile_path = os.path.join(base_dir, "resources", "docker")
    return base_dir, dockerfile_path

@cli.command()
def build_docker_image(
    version: Optional[str] = typer.Option(
        get_container_version(), 
        help="Version tag for the image (defaults to version from commandLAB.version)"
    )
) -> None:
    """Build the Docker image for the daemon"""
    _, dockerfile_path = get_base_paths()
    
    cmd = [
        "docker", "build",
        "-t", f"commandlab-daemon:{version}",
        "--build-arg", f"VERSION={get_package_version()}",
        "-f", os.path.join(dockerfile_path, "Dockerfile"),
        "."
    ]
    subprocess.run(cmd, check=True)

@cli.command()
def build_aws_ami(
    version: Optional[str] = typer.Option(
        get_container_version(), 
        help="Version tag for the image (defaults to version from commandLAB.version)"
    )
) -> None:
    """Build AWS AMI using Packer"""
    base_dir, _ = get_base_paths()
    
    cmd = [
        "packer", "build",
        "-var", f"version={version}",
        os.path.join(base_dir, "resources", "packer", "aws.json")
    ]
    subprocess.run(cmd, check=True)

@cli.command()
def build_azure_vm(
    version: Optional[str] = typer.Option(
        get_container_version(), 
        help="Version tag for the image (defaults to version from commandLAB.version)"
    )
) -> None:
    """Build Azure VM image using Packer"""
    base_dir, _ = get_base_paths()
    
    cmd = [
        "packer", "build",
        "-var", f"version={version}",
        os.path.join(base_dir, "resources", "packer", "azure.json")
    ]
    subprocess.run(cmd, check=True)

@cli.command()
def build_gcp_vm(
    version: Optional[str] = typer.Option(
        get_container_version(), 
        help="Version tag for the image (defaults to version from commandLAB.version)"
    )
) -> None:
    """Build GCP VM image using Packer"""
    base_dir, _ = get_base_paths()
    
    cmd = [
        "packer", "build",
        "-var", f"version={version}",
        os.path.join(base_dir, "resources", "packer", "gcp.json")
    ]
    subprocess.run(cmd, check=True)

@cli.command()
def build_all_images(
    version: Optional[str] = typer.Option(
        get_container_version(), 
        help="Version tag for the images (defaults to version from commandLAB.version)"
    )
) -> None:
    """Build images for all platforms"""
    typer.echo("Building Docker image...")
    build_docker_image(version)
    typer.echo("Building AWS AMI...")
    build_aws_ami(version)
    typer.echo("Building Azure image...")
    build_azure_vm(version)
    typer.echo("Building GCP image...")
    build_gcp_vm(version)

if __name__ == "__main__":
    cli() 