"""Utility functions for building commandAGI daemon images."""

import logging
import os
from typing import Any, Dict

from rich.console import Console
from rich.status import Status

# Configure rich logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("build_images")
console = Console()


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
