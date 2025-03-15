from contextlib import contextmanager
from email.message import Message
from typing import Any, AsyncGenerator, Callable, Literal, Optional, Protocol, TypedDict, Union

from pydantic import BaseModel, Field
from commandAGI._utils.partial import Partial
from commandAGI._utils.resource_schema import Resource
from commandAGI._utils.mcp_schema import MCPServerConnection, MCPServerTransport
from langchain.schema import AnyContent
from langchain.core.tools import tool
from commandAGI.agents.agent import Agent, AgentHooks, AgentRunSession
from commandAGI.agents.base_agent import BaseAgent, TSchema
from commandAGI.agents.events import UserInputEvent
from commandAGI.computers.base_computer import BaseComputer
from commandAGI.types import ComputerAction


class Task(BaseModel):
    objective: str
    directly_supplied_tools: list[BaseTool] = Field(default_factory=list)
    directly_supplied_resources: list[Resource] = Field(default_factory=list)
    mcp_servers: list[MCPServerTransport] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    agent_options: dict[str, Any] = Field(default_factory=dict)
    starting_conditions: str
    ending_conditions: str

class AtomicTask(Task):
    pass

class CompositeTask(BaseModel):
    tasks: dict[str, Task]
    task_dependencies: list[tuple[str, str]]


class OnTaskStartHook(Protocol):
    def __call__(self, task: Task) -> None: ...

class OnTaskFinishHook(Protocol):
    def __call__(self, task: Task) -> None: ...

class AdvancedAgentHooks(AgentHooks):
    on_task_start: OnTaskStartHook
    on_task_finish: OnTaskFinishHook

class AdvancedAgentRunSession(AgentRunSession):
    overall_task: Task
    current_task: Task

    _hooks: AdvancedAgentHooks = Field(default_factory=AdvancedAgentHooks)

    @property
    def tools(self) -> list[BaseTool]:
        return [
            *self.agent.tools,
            *self.task.tools
        ]

    def suggested_actions(self) -> list[ComputerAction]:
        raise NotImplementedError("AdvancedAgent does not support suggested actions yet")

    def suggested_tasks(self) -> list[Task]:
        raise NotImplementedError("AdvancedAgent does not support suggested tasks yet")

class AdvancedAgent(Agent):
    
    @contextmanager
    async def session(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> AsyncGenerator["AdvancedAgentRunSession", None]:
        with mcp_server_connections(self.mcp_servers) as mcp_server_connections:
            state = AdvancedAgentRunSession(
                agent=self,
                step_count=0,
                mcp_server_connections=mcp_server_connections,
                directly_supplied_tools=self.tools,
                objective=prompt,
            )
            # Initialize with user input
            state.add_event(UserInputEvent(content=prompt))
            yield state

    async def _run(self, state: AdvancedAgentRunSession) -> TSchema | None:
        try:
            while True:
                pass
        except Exception as e:
            state.add_error(e)
            raise e
