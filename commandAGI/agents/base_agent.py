from abc import abstractmethod
from contextlib import contextmanager
from typing import AsyncGenerator, Optional, TypeVar, Union
from pydantic import BaseModel, HttpUrl
from commandAGI._utils.mcp_schema import MCPServerTransport
from langchain.tools import BaseTool

from agents import Agent, Runner

from commandAGI.computers.base_computer import BaseComputer

TSchema = TypeVar("TSchema", bound=BaseModel)




class ComputerUseAgent(BaseModel):
    system_prompt: str
    tools: list[BaseTool]
    """
    NOTE: tools are not necesarily the tools that the agnet's LLM kernel will have access to for the following reasons:
    1. the mcp_servers may supply additional tools
    2. the agent architecture may dynamicly select a subset of tools to offer to the LLM kernel based on the context at hand
    """
    mcp_servers: list[MCPServerTransport]
    """
    config info for conecting to mcp servers
    """

    @abstractmethod
    async def run(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> TSchema | None:
        pass
