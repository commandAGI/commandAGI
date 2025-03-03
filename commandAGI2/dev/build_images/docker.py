"""Docker image building functionality for commandAGI2 daemon."""

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
def build_docker_image(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandAGI2.version)",
    )
) -> None:
    """Build the Docker image for the daemon"""
    dockerfile_path = PROJ_DIR / "resources" / "docker" / "Dockerfile"

    if not os.path.exists(dockerfile_path):
        logger.error(f"Dockerfile not found at {dockerfile_path}")
        return

    cmd = [
        "docker",
        "build",
        "-t",
        f"commandagi2-daemon:{version}",
        "--build-arg",
        f"VERSION={get_package_version()}",
        "-f",
        str(dockerfile_path),
        str(PROJ_DIR),
    ]
    run_command(cmd, "Docker image build")
