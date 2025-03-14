from __future__ import annotations

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import Field
import time
from typing import AsyncGenerator, Optional, TypeVar, Union, Callable, Dict, Any, List
import uuid
from pydantic import BaseModel, HttpUrl
from commandAGI._utils.mcp_schema import MCPServerTransport
from langchain.tools import BaseTool

from agents import Agent, Runner

from commandAGI.computers.base_computer import BaseComputer

TSchema = TypeVar("TSchema", bound=BaseModel)

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

class ErrorEvent(AgentEvent):
    """Represents an error that occurred during agent execution"""
    error_type: str
    message: str
    traceback: Optional[str] = None

class BaseAgentHooks(BaseModel):
    on_step_hooks: list[Callable[["BaseAgentRunSession"], None]] = Field(default_factory=list)
    on_error_hooks: list[Callable[["BaseAgentRunSession", Exception], None]] = Field(
        default_factory=list
    )
    on_finish_hooks: list[Callable[["BaseAgentRunSession"], None]] = Field(
        default_factory=list
    )


class BaseAgentRunSession(BaseModel):
    """Schema for Fielding state during agent run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: "BaseAgent"
    directly_supplied_tools: list[BaseTool] = []
    events: List[AgentEvent] = Field(default_factory=list)

    @property
    def tools(self) -> list[BaseTool]:
        return self.directly_supplied_tools

    _hooks: BaseAgentHooks = Field(default_factory=BaseAgentHooks)

    def add_event(self, event: AgentEvent) -> None:
        """Add a new event to the session history"""
        self.events.append(event)

    def input(self, input: str):
        """Add user input to the session"""
        self.add_event(UserInputEvent(content=input))

    def add_system_message(self, content: str, type: str = "instruction"):
        """Add a system message to the session"""
        self.add_event(SystemInputEvent(content=content, type=type))

    def add_thought(self, thought: str, reasoning: Optional[str] = None):
        """Add an agent thought to the session"""
        self.add_event(ThoughtEvent(thought=thought, reasoning=reasoning))

    def add_agent_response(self, role: str, content: str, name: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None):
        """Add an agent response to the session"""
        self.add_event(AgentResponseEvent(role=role, content=content, name=name, tool_calls=tool_calls))

    def add_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Add a tool call event and return the call_id"""
        event = ToolCallEvent(tool_name=tool_name, arguments=arguments)
        self.add_event(event)
        return event.call_id

    def add_tool_result(self, call_id: str, result: Any, error: Optional[str] = None, success: bool = True):
        """Add a tool result event"""
        self.add_event(ToolResultEvent(call_id=call_id, result=result, error=error, success=success))

    def add_error(self, error_type: str, message: str, traceback: Optional[str] = None):
        """Add an error event"""
        self.add_event(ErrorEvent(error_type=error_type, message=message, traceback=traceback))

    def on_step(self, func: Callable[["BaseAgentRunSession"], None]):
        self._hooks.on_step_hooks.append(func)

    def on_error(self, func: Callable[["BaseAgentRunSession", Exception], None]):
        self._hooks.on_error_hooks.append(func)

    def on_finish(self, func: Callable[["BaseAgentRunSession"], None]):
        self._hooks.on_finish_hooks.append(func)


class BaseAgent(BaseModel):
    system_prompt: str
    tools: list[BaseTool]
    """
    NOTE: tools are not necesarily the tools that the agnet's LLM kernel will have access to for the following reasons:
    1. the mcp_servers may supply additional tools
    2. the agent architecture may dynamicly select a subset of tools to offer to the LLM kernel based on the context at hand
    """

    @contextmanager
    async def session(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> AsyncGenerator["BaseAgentRunSession", None]:
        state = BaseAgentRunSession(agent=self, directly_supplied_tools=self.tools)
        yield state

    async def run(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> TSchema | None:
        async with self.session(prompt, output_schema=output_schema) as state:
            return self._run(state)

    @abstractmethod
    async def _run(self, state: BaseAgentRunSession) -> TSchema | None:
        pass
