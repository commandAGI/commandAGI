from typing import AsyncGenerator
from pydantic import BaseModel
from langchain.tools import BaseTool

from agents import Agent, Runner

from commandAGI.computers.base_computer import BaseComputer


class ComputerUseAgent(BaseModel):
    system_prompt: str
    tools: list[BaseTool]

    def run(self, prompt: str):
        pass
    
    def stop(self):
        pass
    
    def pause(self):
        pass

    def resume(self):
        pass

    def input(self, message: list[AnyChatMessage]):
        pass

    def stream(self) -> AsyncGenerator[AnyChatMessage, None, None]:
        pass


class OpenAIComputerUseAgent(ComputerUseAgent):
    client: OpenAIClient
    # its the repsonsibility ofthis class to replace any computer_use_tools withteh openai computer use tool

class AnthropicComputerUseAgent(ComputerUseAgent):
    client: AnthropicClient
    # its the repsonsibility ofthis class to replace any computer_use_tools withteh anthropic computer use tool

class ScrappybaraComputerUseAgent(ComputerUseAgent):
    client: ScrappybaraClient
    # its the repsonsibility ofthis class to replace any computer_use_tools withteh scrappybara computer use tool and do the same for shell tools and edit tool

class BaseAgentSession(BaseModel):
    agent: BaseAgent
