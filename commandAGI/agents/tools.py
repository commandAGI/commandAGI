from typing import Any, Optional, Type
from pydantic import BaseModel
from commandAGI.computers.base_computer import BaseComputer
from langchain.tools import BaseTool

class ShellToolInput(BaseModel):
    command: str
class ShellToolOutput(BaseModel):
    output: str

class ShellTool(BaseTool):
    name: str = "shell"
    description: str = "Use the shell to run commands"
    args_schema: Type[BaseModel] = ShellToolInput
    computer: BaseComputer
    timeout: Optional[float] = None
    computer_shell_args: dict[str, Any] = {}

    def _run(self, command: str) -> ShellToolOutput:
        return self.computer.shell(command, timeout=self.timeout, **self.computer_shell_args)


