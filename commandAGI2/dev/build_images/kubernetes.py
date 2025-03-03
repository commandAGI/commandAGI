"""Kubernetes image building functionality for commandAGI2 daemon."""

import os
import logging
from typing import Optional
import typer
from commandAGI2.version import get_container_version, get_package_version
from commandAGI2._utils.command import run_command
from commandAGI2._utils.config import PROJ_DIR
from commandAGI2.dev.build_images.cli import cli

logger = logging.getLogger("build_images")


@cli.command()
def build_kubernetes_image(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandAGI2.version)",
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
        f"commandagi2-daemon-k8s:{version}",
        "--build-arg",
        f"VERSION={get_package_version()}",
        "-f",
        os.path.join(dockerfile_path, "Dockerfile"),
        ".",
    ]
    run_command(cmd, "Kubernetes Docker image build")
