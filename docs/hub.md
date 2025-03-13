# CommandAGI Hub

The CommandAGI Hub is a central repository for sharing and discovering agents. It allows you to:

- Upload your agents to share with others
- Download agents created by others
- List available agents with filtering options
- Delete your agents from the hub

## Authentication

Before using the hub, you need to authenticate with your CommandAGI account:

```bash
commandagi auth login
```

This will prompt you for your email and password. If you don't have an account, you can register:

```bash
commandagi auth register
```

## Command Line Interface

The hub functionality is available through the `commandagi hub` command:

### Upload an Agent

```bash
commandagi hub upload my_agent.pkl --name "My Agent" --description "A description of my agent" --tag "tag1" --tag "tag2" --version "1.0.0" --public
```

Options:
- `--name`, `-n`: Name of the agent (required)
- `--description`, `-d`: Description of the agent (required)
- `--version`, `-v`: Version of the agent (default: "1.0.0")
- `--tag`, `-t`: Tags for the agent (can be specified multiple times)
- `--public`: Make the agent publicly available (default: private)
- `--source-dir`, `-s`: Directory containing source files to include

### Download an Agent

```bash
commandagi hub download agent_id --output my_downloaded_agent.pkl --source-dir ./agent_source
```

Options:
- `--output`, `-o`: Path to save the downloaded agent (default: "./downloaded_agent.pkl")
- `--save-source/--no-save-source`: Whether to save source files (default: save)
- `--source-dir`, `-s`: Directory to save source files (default: "./agent_source")

### List Agents

```bash
commandagi hub list --tag "tag1" --author "user@example.com" --public-only --limit 10 --offset 0
```

Options:
- `--limit`, `-l`: Maximum number of agents to list (default: 20)
- `--offset`, `-o`: Offset for pagination (default: 0)
- `--tag`, `-t`: Filter by tags (can be specified multiple times)
- `--author`, `-a`: Filter by author
- `--public-only`: Show only public agents (default: show all)

### Delete an Agent

```bash
commandagi hub delete agent_id --force
```

Options:
- `--force`, `-f`: Force deletion without confirmation

## Programmatic Usage

You can also use the hub functionality programmatically in your Python code:

```python
from commandAGI.agents.hub import (
    AgentMetadata,
    upload_agent_sync,
    download_agent_sync,
    list_agents_sync,
    delete_agent_sync
)
from commandAGI.agents.utils import (
    save_agent,
    load_agent,
    collect_source_files,
    save_source_files
)

# Upload an agent
agent, _ = load_agent("my_agent.pkl")
metadata = AgentMetadata(
    name="My Agent",
    description="A description of my agent",
    version="1.0.0",
    tags=["tag1", "tag2"],
    is_public=False
)
source_files = collect_source_files("./my_source_dir")
agent_id = upload_agent_sync(agent, metadata, source_files)

# Download an agent
agent, metadata, source_files = download_agent_sync(agent_id)
save_agent(agent, "downloaded_agent.pkl", metadata=metadata)
save_source_files(source_files, "./downloaded_source")

# List agents
agents = list_agents_sync(tags=["tag1"], author="user@example.com", public_only=True)
for agent in agents:
    print(f"{agent.name} (ID: {agent.id})")

# Delete an agent
success = delete_agent_sync(agent_id)
```

For asynchronous usage, you can use the async versions of these functions:

```python
import asyncio
from commandAGI.agents.hub import (
    upload_agent,
    download_agent,
    list_agents,
    delete_agent
)

async def main():
    # Upload an agent
    agent_id = await upload_agent(agent, metadata, source_files)
    
    # Download an agent
    agent, metadata, source_files = await download_agent(agent_id)
    
    # List agents
    agents = await list_agents(tags=["tag1"])
    
    # Delete an agent
    success = await delete_agent(agent_id)

asyncio.run(main())
```

## Example

See the `examples/hub_example.py` file for a complete example of using the hub functionality. 