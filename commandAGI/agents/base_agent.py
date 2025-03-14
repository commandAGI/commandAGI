from __future__ import annotations

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import Field
from typing import AsyncGenerator, Optional, TypeVar, Union, Callable
import uuid
from pydantic import BaseModel, HttpUrl
from commandAGI._utils.mcp_schema import MCPServerTransport
from langchain.tools import BaseTool

from agents import Agent, Runner

from commandAGI.computers.base_computer import BaseComputer

TSchema = TypeVar("TSchema", bound=BaseModel)


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

    @property
    def tools(self) -> list[BaseTool]:
        return self.directly_supplied_tools

    _hooks: BaseAgentHooks = Field(default_factory=BaseAgentHooks)

    def input(self, input: str):
        self.events.append(
            ChatMessage(role="user", content=[{"type": "text", "text": input}])
        )

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
