"""Azure VM building functionality for CommandLAB daemon."""

import os
import logging
from typing import Optional
import typer
from commandLAB.version import get_container_version
from commandLAB.dev.build_images.utils import run_command, get_base_paths, ensure_packer_template
from commandLAB.dev.build_images.cli import cli

logger = logging.getLogger("build_images")


@cli.command()
def build_azure_vm(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build Azure VM image using Packer"""
    base_dir, _, packer_path = get_base_paths()

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
                "managed_image_resource_group_name": "commandlab-rg",
                "managed_image_name": "commandlab-daemon-{{user `version`}}",
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
                    "sudo pip3 install commandlab[local,daemon]=={{user `version`}}",
                ],
            }
        ],
    }

    azure_template_path = os.path.join(packer_path, "azure.json")
    ensure_packer_template(azure_template_path, azure_template)

    cmd = ["packer", "build", "-var", f"version={version}", azure_template_path]
    run_command(cmd, "Azure VM image build") 