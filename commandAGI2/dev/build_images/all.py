"""CLI commands for building commandAGI2 daemon images."""

import subprocess
import logging
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from commandAGI2.version import get_container_version

from commandAGI2.dev.build_images.cli import cli
from commandAGI2.dev.build_images.docker import build_docker_image
from commandAGI2.dev.build_images.kubernetes import build_kubernetes_image
from commandAGI2.dev.build_images.aws import build_aws_ami
from commandAGI2.dev.build_images.azure import build_azure_vm
from commandAGI2.dev.build_images.gcp import build_gcp_vm

logger = logging.getLogger("build_images")
console = Console()


@cli.command()
def build_all_images(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the images (defaults to version from commandAGI2.version)",
    )
) -> None:
    """Build images for all platforms"""
    console.print("[bold blue]Starting build of all images[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
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
            console.print(
                "[bold yellow]⚠️ Packer not found. Skipping cloud image builds.[/]"
            )
            console.print(
                "[bold yellow]To build cloud images, please install Packer: https://www.packer.io/downloads[/]"
            )

    console.print("[bold green]✓ All image builds completed[/]")
