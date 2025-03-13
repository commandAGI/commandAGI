from email.message import Message
from typing import AsyncGenerator, Callable, Literal, TypedDict, Union

from pydantic import BaseModel
from langchain.schema import AnyContent


class BaseContent(TypedDict, total=False):
    type: str


class TextContent(BaseContent, TypedDict):
    type: Literal["text"]
    text: str


class ImageContent(BaseContent, TypedDict):
    type: Literal["image"]
    image: str


class VideoContent(BaseContent, TypedDict):
    type: Literal["video"]
    video: str


class AudioContent(BaseContent, TypedDict):
    type: Literal["audio"]
    audio: str


AnyContent = Union[TextContent, ImageContent, VideoContent, AudioContent]


from commandAGI.computers.base_computer import BaseComputer


class SLOPServer(BaseModel):
    url: str


class StdIOMCPServerTransport(BaseModel):
    cwd: str
    command: str
    args: list[str] | None = None
    environment: dict[str, str] | None = None
    encoding: str = "utf-8"


class RemoteMCPTransport(BaseModel):
    url: str


MCPServerTransport = Union[StdIOMCPServerTransport, RemoteMCPTransport]


class MCPServer(BaseModel):
    transport: MCPServerTransport


class BaseResource(BaseModel):
    def relevant_text(self, context: Context) -> str:
        pass

    @property
    def relevant(self) -> list[AnyContent]:
        pass


class LiteralResource(BaseResource):
    text: str


class ChatResource(BaseResource):
    messages: list[Message]


class FilesystemResource(BaseResource):
    path: str


class WebResource(BaseResource):
    url: str


class DatabaseResource(BaseResource):
    connection_string: str


class MCPResource(BaseResource):
    mcp_server: MCPServer


class SLOPServerResource(BaseResource):
    slop_server: SLOPServer


Resource = Union[
    LiteralResource,
    FilesystemResource,
    WebResource,
    DatabaseResource,
    MCPResource,
    SLOPServerResource,
]


class ToolParam(BaseModel):
    name: str
    description: str
    required: bool


class Tool(BaseModel):
    name: str
    description: str
    parameters: list[ToolParam]


class Context(BaseModel):
    resources: list[BaseResource]
    tools: list[Tool]
    mcp_servers: list[MCPServer]
    slop_servers: list[SLOPServer]


from langchain.core.tools import tool


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
