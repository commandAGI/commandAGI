from email.message import Message
from typing import Union

from pydantic import BaseModel

from commandAGI.computers.base_computer import BaseComputer

###### DATABASE

# THE SERVER HAS THE SAME INTERFACE AS THE DAEMON DOES PLUS AUTHENTICATION PARAMS

###### THIS LIBRARY

class SLOPServer(BaseModel):
    url: str


class BaseMCPServer(BaseModel):
    pass


class StdIOMCPServer(BaseMCPServer):
    cwd: str
    command: str
    args: list[str] | None = None
    environment: dict[str, str] | None = None
    encoding: str = "utf-8"


class RemoteMCPServer(BaseMCPServer):
    url: str

MCPServer = Union[StdIOMCPServer, RemoteMCPServer]

class BaseResource(BaseModel):
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

Resource = Union[LiteralResource, FilesystemResource, WebResource, DatabaseResource, MCPResource, SLOPServerResource]

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

### Runtiem

from langchain.core.tools import tool
from langchain.core

class Rule(BaseModel):
    condition: str
    prompt: str

class Condition(BaseModel):
    def is_satisfied(self, context: Context) -> bool:
        pass

class Task(BaseModel):
    objective: str
    starting_conditions: str
    ending_conditions: str


class SimpleTask(BaseModel):
    objective: str
    starting_conditions: str
    ending_conditions: str


class BaseAgent(BaseModel):
    rules: list[Rule]
    tools: list[Tool]

    def command(self, task: Task, computer: BaseComputer):
        pass


####### DAEMON + THIS LIBRARY


