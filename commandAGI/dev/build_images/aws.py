"""AWS AMI building functionality for commandAGI daemon."""

import logging
import os
from typing import Any, Dict, Optional

import typer

from commandAGI._utils.command import run_command
from commandAGI._internal.config import PROJ_DIR
from commandAGI.dev.build_images.cli import cli
from commandAGI.dev.build_images.utils import ensure_packer_template
from commandAGI.version import get_container_version

logger = logging.getLogger("build_images")


@cli.command()
def build_aws_ami(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandAGI.version)",
    )
) -> None:
    """Build AWS AMI using Packer"""
    packer_path = PROJ_DIR / "resources" / "packer"
    # Create packer directory if it doesn't exist
    packer_path.mkdir(parents=True, exist_ok=True)

    # Define AWS packer template
    aws_template = {
        "variables": {
            "version": "{{env `VERSION`}}",
            "region": "us-west-2",
            "instance_type": "t2.micro",
        },
        "builders": [
            {
                "type": "amazon-ebs",
                "region": "{{user `region`}}",
                "instance_type": "{{user `instance_type`}}",
                "source_ami_filter": {
                    "filters": {
                        "virtualization-type": "hvm",
                        "name": "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*",
                        "root-device-type": "ebs",
                    },
                    "owners": ["099720109477"],
                    "most_recent": True,
                },
                "ssh_username": "ubuntu",
                "ami_name": "commandagi-daemon-{{user `version`}}-{{timestamp}}",
                "ami_description": "commandAGI daemon image",
                "tags": {"Name": "commandagi-daemon", "Version": "{{user `version`}}"},
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

    aws_template_path = os.path.join(packer_path, "aws.json")
    ensure_packer_template(aws_template_path, aws_template)

    cmd = ["packer", "build", "-var", f"version={version}", aws_template_path]
    run_command(cmd, "AWS AMI build")
