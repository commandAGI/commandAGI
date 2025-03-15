import time
import uuid
from typing import Any, Dict, List, Optional, Type

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
    structured_content: Optional[BaseModel] = None

    @classmethod
    def from_structured(
        cls,
        role: str,
        structured: BaseModel,
        name: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> "AgentResponseEvent":
        """Create an AgentResponseEvent from a structured object, automatically converting it to JSON for content."""
        return cls(
            role=role,
            content=structured.model_dump_json(),
            structured_content=structured,
            name=name,
            tool_calls=tool_calls,
        )

    def get_structured(
        self, schema_type: Optional[Type[TSchema]] = None
    ) -> Optional[BaseModel]:
        """Get the structured content, optionally parsing from JSON if not already available.

        Args:
            schema_type: Optional type to parse the content into if structured_content is not set

        Returns:
            The structured content if available or parseable, None otherwise
        """
        if self.structured_content is not None:
            return self.structured_content
        elif schema_type is not None:
            try:
                return schema_type.model_validate_json(self.content)
            except:
                return None
        return None


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
