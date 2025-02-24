import argparse
import subprocess
import os
from typing import List, Optional
from commandLAB.version import get_container_version, get_package_version


class ImageBuilder:
    def __init__(self, platforms: List[str], version: Optional[str] = None):
        self.platforms = platforms
        self.version = version or get_container_version()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dockerfile_path = os.path.join(self.base_dir, "resources", "docker")

    def build_docker_image(self) -> None:
        """Build the Docker image for the daemon"""
        cmd = [
            "docker", "build",
            "-t", f"commandlab-daemon:{self.version}",
            "--build-arg", f"VERSION={get_package_version()}",
            "-f", os.path.join(self.dockerfile_path, "Dockerfile"),
            "."
        ]
        subprocess.run(cmd, check=True)

    def build_aws_ami(self) -> None:
        """Build AWS AMI using Packer"""
        cmd = [
            "packer", "build",
            "-var", f"version={self.version}",
            os.path.join(self.base_dir, "resources", "packer", "aws.json")
        ]
        subprocess.run(cmd, check=True)

    def build_azure_image(self) -> None:
        """Build Azure VM image using Packer"""
        cmd = [
            "packer", "build",
            "-var", f"version={self.version}",
            os.path.join(self.base_dir, "resources", "packer", "azure.json")
        ]
        subprocess.run(cmd, check=True)

    def build_gcp_image(self) -> None:
        """Build GCP VM image using Packer"""
        cmd = [
            "packer", "build",
            "-var", f"version={self.version}",
            os.path.join(self.base_dir, "resources", "packer", "gcp.json")
        ]
        subprocess.run(cmd, check=True)

    def build_all(self) -> None:
        """Build images for all specified platforms"""
        builders = {
            "docker": self.build_docker_image,
            "aws": self.build_aws_ami,
            "azure": self.build_azure_image,
            "gcp": self.build_gcp_image
        }

        for platform in self.platforms:
            if platform in builders:
                print(f"Building image for {platform}...")
                builders[platform]()
            else:
                print(f"Unknown platform: {platform}")


def main():
    parser = argparse.ArgumentParser(description="Build CommandLAB daemon images")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["docker"],
        choices=["docker", "aws", "azure", "gcp"],
        help="Platforms to build images for"
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Version tag for the images (defaults to version from commandLAB.version)"
    )

    args = parser.parse_args()
    builder = ImageBuilder(args.platforms, args.version)
    builder.build_all()


if __name__ == "__main__":
    main() 