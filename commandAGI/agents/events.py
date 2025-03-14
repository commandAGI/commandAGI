
from typing import List, Optional, Dict, Any
import time
import uuid
from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    """Base class for all agent events"""
    timestamp: float = Field(default_factory=lambda: time.time())
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class AgentResponseEvent(AgentEvent):
    """Represents an agent's response in the conversation"""
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ContextRetrievalEvent(AgentEvent):
    """Represents a context retrieval operation"""
    query: str
    results: List[Dict[str, Any]]
    source: str

class ThoughtEvent(AgentEvent):
    """Represents an agent's internal thought process"""
    thought: str
    reasoning: Optional[str] = None

class ToolCallEvent(AgentEvent):
    """Represents a tool call attempt"""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ToolResultEvent(AgentEvent):
    """Represents the result of a tool call"""
    call_id: str
    result: Any
    error: Optional[str] = None
    success: bool = True

class UserInputEvent(AgentEvent):
    """Represents user input to the agent"""
    content: str

class SystemInputEvent(AgentEvent):
    """Represents system messages or instructions"""
    content: str
    type: str = "instruction"  # Could be 'instruction', 'warning', 'error', etc.

class ResourceCalloutEvent(AgentEvent):
    """Represents a request to query a specific resource before the next agent step"""
    resource_id: str
    query: str

class ResourceRetrievalEvent(AgentEvent):
    """Represents the results from querying a resource"""
    resource_id: str
    query: str
    results: List[ChatMessage]

class ErrorEvent(AgentEvent):
    """Represents an error that occurred during agent execution"""
    error_type: str
    message: str
    traceback: Optional[str] = None