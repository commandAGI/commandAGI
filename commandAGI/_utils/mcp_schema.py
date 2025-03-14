from contextlib import contextmanager
from pydantic import BaseModel
from typing import Union
from pydantic import HttpUrl


class StdIOMCPServerTransport(BaseModel):
    cwd: str
    command: str
    args: list[str] | None = None
    environment: dict[str, str] | None = None
    encoding: str = "utf-8"


class RemoteMCPTransport(BaseModel):
    url: str


MCPServerTransport = Union[StdIOMCPServerTransport, RemoteMCPTransport, HttpUrl]


@contextmanager
def mcp_server_connections(mcp_servers: list[MCPServerTransport]):
    connections = []
    for mcp_server in mcp_servers:
        connection = mcp_server.connect() # NOTE: this is psuedocode, the actual implementation will be different
        connections.append(connection)
    yield connections