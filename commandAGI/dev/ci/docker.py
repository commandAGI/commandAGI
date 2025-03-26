"""Docker image building functionality for commandAGI daemon."""

import logging
import os
from typing import Optional

import typer

from commandAGI._internal.config import PROJ_DIR
from commandAGI._utils.command import run_command
from commandAGI.dev.ci.cli import cli
from commandAGI.version import get_container_version, get_package_version

logger = logging.getLogger("build_images")


@cli.command()
def build_docker_image(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandAGI.version)",
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
        f"commandagi-daemon:{version}",
        "--build-arg",
        f"VERSION={get_package_version()}",
        "-f",
        str(dockerfile_path),
        str(PROJ_DIR),
    ]
    run_command(cmd, "Docker image build")
