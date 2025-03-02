"""Utility functions for running commands with real-time output."""

import subprocess
import logging
from typing import List
from rich.console import Console
from rich.status import Status

# Configure rich logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("commandLAB")
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
                encoding="utf-8",
                errors="replace",
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
