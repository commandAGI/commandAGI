from email.message import Message
from typing import AsyncGenerator, Callable, Literal, TypedDict, Union

from pydantic import BaseModel
from commandAGI._utils.resource_schema import Resource
from commandAGI._utils.mcp_schema import MCPServerConnection
from langchain.schema import AnyContent
from langchain.core.tools import tool
from commandAGI.computers.base_computer import BaseComputer



class Task(BaseModel):
    pass


class SimpleTask(BaseModel):
    objective: str
    starting_conditions: str
    ending_conditions: str

class CompositeTask(BaseModel):
    tasks: dict[str, Task]
    task_dependencies: list[tuple[str, str]]

    # def suggested_actions(self) -> list[ComputerAction]:
    #     pass

    # def suggested_tasks(self) -> list[Task]:
    #     pass

    # def pause(self):
    #     pass

    # def resume(self):
    #     pass

    # def start(self):
    #     pass

    # def stop(self):
    #     pass
