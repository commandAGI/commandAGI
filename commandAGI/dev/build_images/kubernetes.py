"""Kubernetes image building functionality for commandAGI daemon."""

import logging
import os
from typing import Optional

import typer

from commandAGI._utils.command import run_command
from commandAGI._utils.config import PROJ_DIR
from commandAGI.dev.build_images.cli import cli
from commandAGI.version import get_container_version, get_package_version

logger = logging.getLogger("build_images")


@cli.command()
def build_kubernetes_image(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandAGI.version)",
    )
) -> None:
    """Build Docker image for Kubernetes deployment"""
    # This is essentially the same as the Docker image but with a different tag
    dockerfile_path = PROJ_DIR / "resources" / "docker"

    if not os.path.exists(os.path.join(dockerfile_path, "Dockerfile")):
        logger.error(f"Dockerfile not found at {dockerfile_path}")
        return

    cmd = [
        "docker",
        "build",
        "-t",
        f"commandagi-daemon-k8s:{version}",
        "--build-arg",
        f"VERSION={get_package_version()}",
        "-f",
        os.path.join(dockerfile_path, "Dockerfile"),
        ".",
    ]
    run_command(cmd, "Kubernetes Docker image build")
