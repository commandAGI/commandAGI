#!/usr/bin/env python3
"""
Example script demonstrating how to use the CommandAGI Hub functionality
"""

import os
import sys
import asyncio
from pathlib import Path

from commandAGI.agents.advanced_agent import Agent
from commandAGI.agents.hub import (
    AgentMetadata,
    upload_agent,
    download_agent,
    list_agents,
    delete_agent
)
from commandAGI.agents.utils import (
    save_agent,
    load_agent,
    collect_source_files,
    save_source_files
)
from commandAGI._internal.auth import login


async def main():
    print("CommandAGI Hub Example")
    print("=====================")
    
    # First, ensure we're logged in
    try:
        # You can replace this with your own credentials
        # Or comment it out if you're already logged in
        await login(email="example@example.com", password="your_password")
        print("✅ Logged in successfully")
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        print("Please run 'commandagi auth login' to login first")
        return
    
    # Create a simple agent for demonstration
    print("\nCreating a simple agent...")
    agent = Agent(
        default_context=None,  # Replace with actual context
        rules=[],  # Add rules as needed
        tools=[]   # Add tools as needed
    )
    
    # Save the agent locally
    agent_path, metadata_path = save_agent(
        agent, 
        "example_agent.pkl", 
        metadata=AgentMetadata(
            name="Example Agent",
            description="An example agent for demonstration",
            version="1.0.0",
            tags=["example", "demo"],
            is_public=False
        )
    )
    print(f"✅ Agent saved locally to {agent_path}")
    
    # Upload the agent to the hub
    print("\nUploading agent to hub...")
    try:
        # Collect source files from the current directory
        source_files = collect_source_files(".")
        print(f"📁 Found {len(source_files)} source files")
        
        # Upload the agent
        agent_id = await upload_agent(
            agent,
            AgentMetadata(
                name="Example Agent",
                description="An example agent for demonstration",
                version="1.0.0",
                tags=["example", "demo"],
                is_public=False
            ),
            source_files
        )
        print(f"✅ Agent uploaded successfully with ID: {agent_id}")
        
        # List available agents
        print("\nListing available agents...")
        agents = await list_agents()
        print(f"Found {len(agents)} agents:")
        for i, agent_metadata in enumerate(agents):
            print(f"{i+1}. {agent_metadata.name} (ID: {agent_metadata.id})")
        
        # Download the agent
        print(f"\nDownloading agent {agent_id}...")
        downloaded_agent, metadata, source_files = await download_agent(agent_id)
        print(f"✅ Agent downloaded successfully")
        print(f"📄 Metadata: {metadata.model_dump()}")
        print(f"📁 Source files: {len(source_files)} files")
        
        # Save the downloaded agent
        download_path, _ = save_agent(
            downloaded_agent, 
            "downloaded_agent.pkl", 
            metadata=metadata
        )
        print(f"✅ Downloaded agent saved to {download_path}")
        
        # Save source files
        source_dir = Path("downloaded_source")
        saved_files = save_source_files(source_files, source_dir)
        print(f"✅ {len(saved_files)} source files saved to {source_dir}")
        
        # Delete the agent from the hub
        print(f"\nDeleting agent {agent_id}...")
        success = await delete_agent(agent_id)
        if success:
            print(f"✅ Agent {agent_id} deleted successfully")
        else:
            print(f"❌ Failed to delete agent {agent_id}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 