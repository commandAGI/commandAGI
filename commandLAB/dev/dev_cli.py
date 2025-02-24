import typer
from commandLAB.dev.build_images import cli as build_images_cli
from commandLAB.dev.update_daemon_client import generate_openapi_client

cli = typer.Typer()

cli.add_typer(build_images_cli, name="build")

@cli.command()
def update_client():
    generate_openapi_client()

if __name__ == "__main__":
    cli()
