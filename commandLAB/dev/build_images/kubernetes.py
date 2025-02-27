"""Kubernetes image building functionality for CommandLAB daemon."""

import os
import logging
from typing import Optional
import typer
from commandLAB.version import get_container_version, get_package_version
from commandLAB.dev.build_images.utils import run_command, get_base_paths
from commandLAB.dev.build_images.cli import cli
logger = logging.getLogger("build_images")


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