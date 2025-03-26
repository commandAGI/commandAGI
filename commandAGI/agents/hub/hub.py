import base64
import pickle
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from commandAGI._internal.auth import AuthError
from commandAGI._internal.config import config
from commandAGI.agents.advanced_agent import Agent


class AgentMetadata(BaseModel):
    """Metadata for an agent stored on the hub"""

    id: Optional[str] = None
    name: str
    description: str
    version: str = "1.0.0"
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    is_public: bool = False
    downloads: int = 0
    likes: int = 0


class AgentBundle(BaseModel):
    """Bundle containing agent data and metadata for upload/download"""

    metadata: AgentMetadata
    pickle_data: str  # Base64 encoded pickle data
    source_files: Dict[str, str] = Field(default_factory=dict)  # Filename -> content


async def upload_agent(
    agent: Agent, metadata: AgentMetadata, source_files: Optional[Dict[str, str]] = None
) -> str:
    """
    Upload an agent to the CommandAGI Hub

    Args:
        agent: The agent to upload
        metadata: Metadata for the agent
        source_files: Optional dictionary of source files to include (path -> content)

    Returns:
        The ID of the uploaded agent

    Raises:
        AuthError: If not authenticated or authorization fails
        ValueError: If upload fails
    """
    if not config.current_token:
        raise AuthError("Not authenticated. Please login first.")

    # Serialize the agent to a pickle and encode as base64
    pickle_data = pickle.dumps(agent)
    encoded_pickle = base64.b64encode(pickle_data).decode("utf-8")

    # Create the bundle
    bundle = AgentBundle(
        metadata=metadata, pickle_data=encoded_pickle, source_files=source_files or {}
    )

    # Upload to the hub
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_base_url}/agents",
                headers={"Authorization": f"Bearer {config.current_token}"},
                json=bundle.model_dump(),
            )

            if response.status_code != 200 and response.status_code != 201:
                raise ValueError(f"Failed to upload agent: {response.text}")

            data = response.json()
            return data["id"]
    except httpx.RequestError as e:
        raise ValueError(f"Failed to upload agent: {str(e)}")


async def download_agent(agent_id: str) -> tuple[Agent, AgentMetadata, Dict[str, str]]:
    """
    Download an agent from the CommandAGI Hub

    Args:
        agent_id: The ID of the agent to download

    Returns:
        Tuple of (agent, metadata, source_files)

    Raises:
        AuthError: If not authenticated or authorization fails
        ValueError: If download fails or agent not found
    """
    if not config.current_token:
        raise AuthError("Not authenticated. Please login first.")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.api_base_url}/agents/{agent_id}",
                headers={"Authorization": f"Bearer {config.current_token}"},
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to download agent: {response.text}")

            data = response.json()
            bundle = AgentBundle.model_validate(data)

            # Decode the pickle data
            pickle_data = base64.b64decode(bundle.pickle_data)
            agent = pickle.loads(pickle_data)

            return agent, bundle.metadata, bundle.source_files
    except httpx.RequestError as e:
        raise ValueError(f"Failed to download agent: {str(e)}")


async def list_agents(
    tags: Optional[List[str]] = None,
    author: Optional[str] = None,
    public_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> List[AgentMetadata]:
    """
    List agents available on the CommandAGI Hub

    Args:
        tags: Optional list of tags to filter by
        author: Optional author to filter by
        public_only: If True, only return public agents
        limit: Maximum number of agents to return
        offset: Offset for pagination

    Returns:
        List of agent metadata

    Raises:
        AuthError: If not authenticated or authorization fails
        ValueError: If request fails
    """
    if not config.current_token:
        raise AuthError("Not authenticated. Please login first.")

    params = {"limit": limit, "offset": offset, "public_only": public_only}

    if tags:
        params["tags"] = ",".join(tags)

    if author:
        params["author"] = author

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.api_base_url}/agents",
                headers={"Authorization": f"Bearer {config.current_token}"},
                params=params,
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to list agents: {response.text}")

            data = response.json()
            return [AgentMetadata.model_validate(item) for item in data["agents"]]
    except httpx.RequestError as e:
        raise ValueError(f"Failed to list agents: {str(e)}")


async def delete_agent(agent_id: str) -> bool:
    """
    Delete an agent from the CommandAGI Hub

    Args:
        agent_id: The ID of the agent to delete

    Returns:
        True if successful

    Raises:
        AuthError: If not authenticated or authorization fails
        ValueError: If deletion fails
    """
    if not config.current_token:
        raise AuthError("Not authenticated. Please login first.")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{config.api_base_url}/agents/{agent_id}",
                headers={"Authorization": f"Bearer {config.current_token}"},
            )

            if response.status_code != 200 and response.status_code != 204:
                raise ValueError(f"Failed to delete agent: {response.text}")

            return True
    except httpx.RequestError as e:
        raise ValueError(f"Failed to delete agent: {str(e)}")


# Synchronous versions of the async functions
def upload_agent_sync(
    agent: Agent, metadata: AgentMetadata, source_files: Optional[Dict[str, str]] = None
) -> str:
    """Synchronous version of upload_agent"""
    import asyncio

    return asyncio.run(upload_agent(agent, metadata, source_files))


def download_agent_sync(agent_id: str) -> tuple[Agent, AgentMetadata, Dict[str, str]]:
    """Synchronous version of download_agent"""
    import asyncio

    return asyncio.run(download_agent(agent_id))


def list_agents_sync(
    tags: Optional[List[str]] = None,
    author: Optional[str] = None,
    public_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> List[AgentMetadata]:
    """Synchronous version of list_agents"""
    import asyncio

    return asyncio.run(list_agents(tags, author, public_only, limit, offset))


def delete_agent_sync(agent_id: str) -> bool:
    """Synchronous version of delete_agent"""
    import asyncio

    return asyncio.run(delete_agent(agent_id))
