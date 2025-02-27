"""AWS AMI building functionality for CommandLAB daemon."""

import os
import logging
from typing import Optional, Dict, Any
import typer
from commandLAB.version import get_container_version
from commandLAB.dev.build_images.utils import run_command, get_base_paths, ensure_packer_template
from commandLAB.dev.build_images.cli import cli

logger = logging.getLogger("build_images")


@cli.command()
def build_aws_ami(
    version: Optional[str] = typer.Option(
        get_container_version(),
        help="Version tag for the image (defaults to version from commandLAB.version)",
    )
) -> None:
    """Build AWS AMI using Packer"""
    base_dir, _, packer_path = get_base_paths()

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
                "ami_name": "commandlab-daemon-{{user `version`}}-{{timestamp}}",
                "ami_description": "CommandLAB daemon image",
                "tags": {"Name": "commandlab-daemon", "Version": "{{user `version`}}"},
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

    aws_template_path = os.path.join(packer_path, "aws.json")
    ensure_packer_template(aws_template_path, aws_template)

    cmd = ["packer", "build", "-var", f"version={version}", aws_template_path]
    run_command(cmd, "AWS AMI build") 