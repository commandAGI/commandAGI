"""Utility functions for building CommandLAB daemon images."""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.status import Status

from commandLAB._utils.config import APPDIR, PROJ_DIR

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("build_images")
console = Console()


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command with real-time stdout streaming and proper error handling and logging"""
    with Status(f"[bold blue]{description}...", console=console) as status:
        logger.info(f"Running: {' '.join(cmd)}")
        try:
            # Open the process and merge stdout and stderr
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            # Stream the output line by line
            while True:
                line = process.stdout.readline()
                if line:
                    console.print(line.rstrip())
                elif process.poll() is not None:
                    # No more output and the process is finished
                    break

            # Read and print any remaining output
            remainder = process.stdout.read()
            if remainder:
                console.print(remainder.rstrip())

            return_code = process.wait()
            if return_code == 0:
                status.update(f"[bold green]✓ {description} completed successfully")
                return True
            else:
                status.update(f"[bold red]✗ {description} failed")
                logger.error(f"{description} failed with exit code {return_code}")
                return False
        except Exception as e:
            status.update(f"[bold red]✗ {description} failed")
            logger.error(f"{description} failed with exception: {e}")
            return False


def ensure_packer_template(
    template_path: str, template_content: Dict[str, Any]
) -> None:
    """Ensure the packer template exists with the correct content"""
    import json

    with Status("[bold blue]Checking packer template...", console=console) as status:
        if not os.path.exists(template_path):
            status.update("[bold blue]Creating packer template...")
            with open(template_path, "w") as f:
                json.dump(template_content, f, indent=2)
            status.update("[bold green]✓ Packer template created")
        else:
            status.update("[bold green]✓ Packer template exists") 