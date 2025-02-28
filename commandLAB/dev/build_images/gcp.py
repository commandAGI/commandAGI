"""GCP VM building functionality for CommandLAB daemon."""

import os
import logging
from typing import Optional
import typer
from commandLAB.version import get_container_version
from commandLAB.dev.build_images.utils import run_command, ensure_packer_template
from commandLAB._utils.config import PROJ_DIR
from commandLAB.dev.build_images.cli import cli
logger = logging.getLogger("build_images")


@cli.command()
def build_gcp_vm(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build GCP VM image using Packer"""
    packer_path = PROJ_DIR / "resources" / "packer"
    # Create packer directory if it doesn't exist
    packer_path.mkdir(parents=True, exist_ok=True)

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