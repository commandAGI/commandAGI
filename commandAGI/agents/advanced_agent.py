from email.message import Message
from typing import AsyncGenerator, Callable, Literal, TypedDict, Union

from pydantic import BaseModel
from commandAGI._utils.resource_schema import Resource
from commandAGI._utils.mcp_schema import MCPServerConnection
from langchain.schema import AnyContent
from langchain.core.tools import tool
from commandAGI.computers.base_computer import BaseComputer





class Context(BaseModel):
    resources: list[Resource]
    tools: list[Tool]
    mcp_server_connections: list[MCPServerConnection]


class BaseCondition(BaseModel):
    def is_satisfied(self, context: Context) -> bool:
        pass


class EmbeddingSimilarityCondition(BaseCondition):
    content: list[AnyContent]

    def is_satisfied(self, context: Context) -> bool:
        pass


class LLMEvaluationCondition(BaseCondition):
    prompt: str

    def is_satisfied(self, context: Context) -> bool:
        pass


Condition = Union[EmbeddingSimilarityCondition, LLMEvaluationCondition]


class Rule(BaseModel):
    condition: Condition
    prompt: str


class Task(BaseModel):
    pass


class SimpleTask(BaseModel):
    objective: str
    starting_conditions: str
    ending_conditions: str

class CompositeTask(BaseModel):
    tasks: dict[str, Task]
    task_dependencies: list[tuple[str, str]]


from commandAGI.types import ComputerAction


# i think i can do it with just responses api
class AgentEvent(BaseModel):
    type: Literal["thought", "action", "task", "resource"]
    content: str

class Agent(BaseModel):
    default_context: Context
    rules: list[Rule]
    tools: list[Tool]

    # also kind of make it a subclass of scrappybara's agent where you 
    # TODO: look at how openai swarms are managing this and try ot make my agent a superset of that (ie, just additional optional parameters)
    def run(
        self,
        task: str|Task,
        computer: BaseComputer,
        on_step: Callable[[str], None] = None,
        on_message_start: Callable[[str], None] = None,
        on_message_chunk: Callable[[str], None] = None,
        on_message_complete: Callable[[str], None] = None,
        on_tool_call: Callable[[str], None] = None,
        on_tool_result: Callable[[str], None] = None,
        on_finish: Callable[[str], None] = None,
    ):
        pass

    def suggested_actions(self) -> list[ComputerAction]:
        pass

    def suggested_tasks(self) -> list[Task]:
        pass

    def input(self, message: ChatMessage):
        pass

    def stream_events(self) -> AsyncGenerator[AgentEvent, None, None]:
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass
