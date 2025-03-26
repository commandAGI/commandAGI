import sys
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.theme import Theme

from commandAGI._internal.auth import AuthError
from commandAGI.agents.hub import (
    AgentMetadata,
    delete_agent_sync,
    download_agent_sync,
    list_agents_sync,
    upload_agent_sync,
)
from commandAGI.agents.utils import (
    collect_source_files,
    load_agent,
    save_agent,
    save_source_files,
)

console = Console(theme=Theme({"info": "cyan", "success": "green", "error": "red"}))
app = typer.Typer(help="Manage agents on the CommandAGI Hub")


@app.command()
def upload(
    agent_path: str = typer.Argument(..., help="Path to the pickled agent file"),
    name: str = typer.Option(..., "--name", "-n", help="Name of the agent"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the agent"
    ),
    version: str = typer.Option(
        "1.0.0", "--version", "-v", help="Version of the agent"
    ),
    tags: List[str] = typer.Option(
        [], "--tag", "-t", help="Tags for the agent (can be specified multiple times)"
    ),
    public: bool = typer.Option(
        False, "--public", help="Make the agent publicly available"
    ),
    source_dir: Optional[str] = typer.Option(
        None, "--source-dir", "-s", help="Directory containing source files to include"
    ),
):
    """Upload an agent to the CommandAGI Hub"""
    try:
        # Load the agent
        console.print(f"🔄 Loading agent from {agent_path}...", style="info")
        agent, existing_metadata = load_agent(agent_path)

        # Create metadata
        metadata = AgentMetadata(
            name=name,
            description=description,
            version=version,
            tags=tags,
            is_public=public,
        )

        # Collect source files if specified
        source_files = {}
        if source_dir:
            console.print(
                f"🔄 Collecting source files from {source_dir}...", style="info"
            )
            source_files = collect_source_files(source_dir)
            console.print(f"📁 Found {len(source_files)} source files", style="info")

        # Upload the agent
        console.print("🔄 Uploading agent to hub...", style="info")
        agent_id = upload_agent_sync(agent, metadata, source_files)

        console.print(
            f"✅ Agent uploaded successfully with ID: {agent_id}", style="success"
        )

    except AuthError as e:
        console.print(f"❌ Authentication error: {str(e)}", style="error")
        console.print("Please login first using 'commandagi auth login'", style="info")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error uploading agent: {str(e)}", style="error")
        sys.exit(1)


@app.command()
def download(
    agent_id: str = typer.Argument(..., help="ID of the agent to download"),
    output_path: str = typer.Option(
        "./downloaded_agent.pkl",
        "--output",
        "-o",
        help="Path to save the downloaded agent",
    ),
    save_source: bool = typer.Option(
        True, "--save-source/--no-save-source", help="Whether to save source files"
    ),
    source_dir: Optional[str] = typer.Option(
        None,
        "--source-dir",
        "-s",
        help="Directory to save source files (defaults to ./agent_source)",
    ),
):
    """Download an agent from the CommandAGI Hub"""
    try:
        console.print(f"🔄 Downloading agent {agent_id}...", style="info")
        agent, metadata, source_files = download_agent_sync(agent_id)

        # Save the agent
        agent_path, metadata_path = save_agent(
            agent, output_path, save_metadata=True, metadata=metadata
        )
        console.print(f"✅ Agent saved to {agent_path}", style="success")
        console.print(f"📄 Metadata saved to {metadata_path}", style="info")

        # Save source files if requested
        if save_source and source_files:
            if source_dir is None:
                source_dir = "./agent_source"

            console.print(
                f"🔄 Saving {len(source_files)} source files to {source_dir}...",
                style="info",
            )
            saved_files = save_source_files(source_files, source_dir)
            console.print(
                f"✅ {len(saved_files)} source files saved to {source_dir}",
                style="success",
            )

    except AuthError as e:
        console.print(f"❌ Authentication error: {str(e)}", style="error")
        console.print("Please login first using 'commandagi auth login'", style="info")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error downloading agent: {str(e)}", style="error")
        sys.exit(1)


@app.command()
def list(
    limit: int = typer.Option(
        20, "--limit", "-l", help="Maximum number of agents to list"
    ),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    tags: List[str] = typer.Option(
        [], "--tag", "-t", help="Filter by tags (can be specified multiple times)"
    ),
    author: Optional[str] = typer.Option(
        None, "--author", "-a", help="Filter by author"
    ),
    public_only: bool = typer.Option(
        False, "--public-only", help="Show only public agents"
    ),
):
    """List agents available on the CommandAGI Hub"""
    try:
        console.print("🔄 Fetching agents from hub...", style="info")
        agents = list_agents_sync(tags, author, public_only, limit, offset)

        if not agents:
            console.print("No agents found matching the criteria", style="info")
            return

        table = Table(title="Available Agents")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Author", style="yellow")
        table.add_column("Public", style="magenta")
        table.add_column("Downloads", style="blue")
        table.add_column("Tags", style="cyan")

        for agent in agents:
            table.add_row(
                agent.id or "",
                agent.name,
                agent.version,
                agent.author or "Unknown",
                "✓" if agent.is_public else "✗",
                str(agent.downloads),
                ", ".join(agent.tags),
            )

        console.print(table)

    except AuthError as e:
        console.print(f"❌ Authentication error: {str(e)}", style="error")
        console.print("Please login first using 'commandagi auth login'", style="info")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error listing agents: {str(e)}", style="error")
        sys.exit(1)


@app.command()
def delete(
    agent_id: str = typer.Argument(..., help="ID of the agent to delete"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
):
    """Delete an agent from the CommandAGI Hub"""
    try:
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete agent {agent_id}?"
            )
            if not confirm:
                console.print("Operation cancelled", style="info")
                return

        console.print(f"🔄 Deleting agent {agent_id}...", style="info")
        success = delete_agent_sync(agent_id)

        if success:
            console.print(f"✅ Agent {agent_id} deleted successfully", style="success")
        else:
            console.print(f"❌ Failed to delete agent {agent_id}", style="error")

    except AuthError as e:
        console.print(f"❌ Authentication error: {str(e)}", style="error")
        console.print("Please login first using 'commandagi auth login'", style="info")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error deleting agent: {str(e)}", style="error")
        sys.exit(1)


if __name__ == "__main__":
    app()
