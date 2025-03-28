import uuid
from abc import abstractmethod
from typing import Union

from langchain.schema import ChatMessage
from pydantic import BaseModel, Field

from commandAGI._utils.mcp_schema import MCPServerConnection


class BaseResource(BaseModel):
    resource_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @abstractmethod
    def get_relevant_items(self, query: str) -> list[ChatMessage]:
        pass


class ChatResource(BaseResource):
    messages: list[ChatMessage]

    def get_relevant_items(self, query: str) -> list[ChatMessage]:
        # Mock implementation - return all messages for now
        return self.messages


class FilesystemResource(BaseResource):
    path: str

    def get_relevant_items(self, query: str) -> list[ChatMessage]:
        # Mock implementation - return empty list
        return []


class WebResource(BaseResource):
    url: str

    def get_relevant_items(self, query: str) -> list[ChatMessage]:
        # Mock implementation - return empty list
        return []


class DatabaseResource(BaseResource):
    connection_string: str

    def get_relevant_items(self, query: str) -> list[ChatMessage]:
        # Mock implementation - return empty list
        return []


class MCPResource(BaseResource):
    mcp_server: MCPServerConnection

    def get_relevant_items(self, query: str) -> list[ChatMessage]:
        # Mock implementation - return empty list
        return []


Resource = Union[
    ChatResource,
    FilesystemResource,
    WebResource,
    DatabaseResource,
    MCPResource,
]
