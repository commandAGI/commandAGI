from pydantic import BaseModel
from typing import AnyContent, Literal, Union

from langchain.schema import ChatMessage

from commandAGI._utils.mcp_schema import MCPServerConnection
from commandAGI.agents.advanced_agent import Context

Context
class BaseResource(BaseModel):
    pass

class ChatResource(BaseResource):
    messages: list[ChatMessage]


class FilesystemResource(BaseResource):
    path: str


class WebResource(BaseResource):
    url: str


class DatabaseResource(BaseResource):
    connection_string: str


class MCPResource(BaseResource):
    mcp_server: MCPServerConnection



Resource = Union[
    ChatResource,
    FilesystemResource,
    WebResource,
    DatabaseResource,
    MCPResource,
]