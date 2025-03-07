import typer
import logging
import sys
from commandAGI.dev.build_images import cli as build_images_cli
from commandAGI.dev.update_daemon_client import generate_openapi_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dev_cli")

cli = typer.Typer(help="commandAGI development tools")

cli.add_typer(build_images_cli, name="build")


@cli.command()
def update_client():
    """Update the daemon client from the OpenAPI spec"""
    logger.info("Updating daemon client from OpenAPI spec")
    generate_openapi_client()
    logger.info("Daemon client updated successfully")


if __name__ == "__main__":
    cli()
