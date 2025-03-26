"""CLI commands for building commandAGI daemon images."""

import logging

import typer
from rich.console import Console


logger = logging.getLogger("build_images")
console = Console()

cli = typer.Typer(help="Build commandAGI daemon images for different platforms")
