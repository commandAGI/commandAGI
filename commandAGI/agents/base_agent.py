from typing import AsyncGenerator
from pydantic import BaseModel
from langchain.tools import BaseTool
from commandAGI.computers.base_computer import BaseComputer


class BaseAgent(BaseModel):
    system_prompt: str
    tools: list[BaseTool]
    computer: BaseComputer

    def start(self, prompt: str):
        pass

    def stop(self):
        pass
    
    def pause(self):
        pass

    def resume(self):
        pass

    def input(self, message: str):
        pass

    def stream(self) -> AsyncGenerator[AnyChatMessage, None, None]:
        pass
