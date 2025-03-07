"""Azure VM building functionality for commandAGI daemon."""

import logging
import os
from typing import Optional

import typer

from commandAGI._utils.command import run_command
from commandAGI._utils.config import PROJ_DIR
from commandAGI.dev.build_images.cli import cli
from commandAGI.dev.build_images.utils import ensure_packer_template
from commandAGI.version import get_container_version

logger = logging.getLogger("build_images")


@cli.command()
def build_azure_vm(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandAGI.version)",
    )
) -> None:
    """Build Azure VM image using Packer"""
    packer_path = PROJ_DIR / "resources" / "packer"
    # Create packer directory if it doesn't exist
    packer_path.mkdir(parents=True, exist_ok=True)

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
                "managed_image_resource_group_name": "commandagi-rg",
                "managed_image_name": "commandagi-daemon-{{user `version`}}",
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
                    "sudo pip3 install commandagi[local,daemon]=={{user `version`}}",
                ],
            }
        ],
    }

    azure_template_path = os.path.join(packer_path, "azure.json")
    ensure_packer_template(azure_template_path, azure_template)

    cmd = ["packer", "build", "-var", f"version={version}", azure_template_path]
    run_command(cmd, "Azure VM image build")
