"""
Utility functions for working with agents
"""

import os
import pickle
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple

from commandAGI.agents.advanced_agent import Agent
from commandAGI.agents.hub import AgentMetadata


def save_agent(agent: Agent, path: str, save_metadata: bool = True, metadata: Optional[AgentMetadata] = None) -> Tuple[Path, Optional[Path]]:
    """
    Save an agent to disk
    
    Args:
        agent: The agent to save
        path: Path to save the agent to
        save_metadata: Whether to save metadata alongside the agent
        metadata: Optional metadata to save (if None, will create minimal metadata)
        
    Returns:
        Tuple of (agent_path, metadata_path)
    """
    # Ensure the directory exists
    agent_path = Path(path)
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the agent
    with open(agent_path, "wb") as f:
        pickle.dump(agent, f)
    
    metadata_path = None
    if save_metadata:
        # Create minimal metadata if not provided
        if metadata is None:
            metadata = AgentMetadata(
                name=agent_path.stem,
                description="Agent saved from commandAGI",
                version="1.0.0"
            )
        
        # Save metadata
        metadata_path = agent_path.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(metadata.model_dump(), f, indent=2)
    
    return agent_path, metadata_path


def load_agent(path: str, load_metadata: bool = True) -> Tuple[Agent, Optional[AgentMetadata]]:
    """
    Load an agent from disk
    
    Args:
        path: Path to load the agent from
        load_metadata: Whether to load metadata alongside the agent
        
    Returns:
        Tuple of (agent, metadata)
    """
    agent_path = Path(path)
    
    # Load the agent
    with open(agent_path, "rb") as f:
        agent = pickle.load(f)
    
    metadata = None
    if load_metadata:
        # Try to load metadata
        metadata_path = agent_path.with_suffix(".json")
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata_dict = json.load(f)
                metadata = AgentMetadata.model_validate(metadata_dict)
    
    return agent, metadata


def collect_source_files(source_dir: str, file_patterns: List[str] = ["**/*.py"]) -> Dict[str, str]:
    """
    Collect source files from a directory
    
    Args:
        source_dir: Directory to collect source files from
        file_patterns: Glob patterns for files to include
        
    Returns:
        Dictionary of {relative_path: file_content}
    """
    source_files = {}
    source_dir_path = Path(source_dir)
    
    if not source_dir_path.exists() or not source_dir_path.is_dir():
        raise ValueError(f"Source directory {source_dir} does not exist or is not a directory")
    
    for pattern in file_patterns:
        for file_path in source_dir_path.glob(pattern):
            if file_path.is_file():
                rel_path = file_path.relative_to(source_dir_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    source_files[str(rel_path)] = f.read()
    
    return source_files


def save_source_files(source_files: Dict[str, str], output_dir: str) -> List[Path]:
    """
    Save source files to disk
    
    Args:
        source_files: Dictionary of {relative_path: file_content}
        output_dir: Directory to save source files to
        
    Returns:
        List of saved file paths
    """
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for file_path, content in source_files.items():
        full_path = output_dir_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        saved_files.append(full_path)
    
    return saved_files 