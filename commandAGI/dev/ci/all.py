"""CLI commands for building commandAGI daemon images."""

import logging
import subprocess
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from commandAGI.dev.ci.aws import build_aws_ami
from commandAGI.dev.ci.azure import build_azure_vm
from commandAGI.dev.ci.cli import cli
from commandAGI.dev.ci.docker import build_docker_image
from commandAGI.dev.ci.gcp import build_gcp_vm
from commandAGI.dev.ci.kubernetes import build_kubernetes_image
from commandAGI.version import get_container_version

logger = logging.getLogger("build_images")
console = Console()


@cli.command()
def build_all_images(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the images (defaults to version from commandAGI.version)",
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
