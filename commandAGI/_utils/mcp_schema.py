from contextlib import contextmanager
from typing import Any, Generator, TypeAlias, Union

from pydantic import BaseModel, HttpUrl


class StdIOMCPServerTransport(BaseModel):
    cwd: str
    command: str
    args: list[str] | None = None
    environment: dict[str, str] | None = None
    encoding: str = "utf-8"


class RemoteMCPTransport(BaseModel):
    url: str


MCPServerTransport = Union[StdIOMCPServerTransport, RemoteMCPTransport, HttpUrl]

# TODO: fix this
MCPServerConnection: TypeAlias = Any


@contextmanager
def mcp_server_connections(
    mcp_servers: list[MCPServerTransport],
) -> Generator[list[MCPServerConnection], None, None]:
    connections = []
    for mcp_server in mcp_servers:
        connection = (
            mcp_server.connect()
        )  # TODO: this is psuedocode, the actual implementation will be different
        connections.append(connection)
    yield connections
    for connection in connections:
        connection.close()
