from abc import abstractmethod
from typing import AsyncGenerator, Optional, TypeVar, Union
from pydantic import BaseModel
from langchain.tools import BaseTool

from agents import Agent, Runner

from commandAGI.computers.base_computer import BaseComputer

TSchema = TypeVar("TSchema", bound=BaseModel)


class ComputerUseAgent(BaseModel):
    system_prompt: str
    tools: list[BaseTool]

    def run(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> TSchema | None:
        pass


AgentProviderClient = Union[
    OpenAIClient, AnthropicClient, ScrappybaraClient, CommandAGIClient
]


class SimpleComputerUseAgent(ComputerUseAgent):
    client: AgentProviderClient
    is_complete_prompt: str

    def __init__(
        self, system_prompt: str, tools: list[BaseTool], client: AgentProviderClient
    ):
        super().__init__(system_prompt, tools)
        self.client = client
        self.tools = _replace_computer_tools_with_agent_provider_specific_tools(
            tools, client
        )

    def run(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> TSchema | None:
        history = [{"role": "user", "content": prompt}]

        while True:
            # Generate action based on history
            response = _chat_completion(history, client=self.client)
            history.append(response)

            # Execute any tool calls
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool = next(
                        t for t in self.tools if t.name == tool_call.function.name
                    )
                    result = tool.run(tool_call.function.arguments)
                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": str(result),
                        }
                    )

            # Check if we're done
            is_complete = _chat_completion(
                history + [{"role": "user", "content": self.is_complete_prompt}],
                client=self.client,
                output_schema=bool,
            )

            if is_complete:
                if output_schema:
                    return _chat_completion(
                        history
                        + [
                            {
                                "role": "user",
                                "content": "Summarize the final result in the requested schema",
                            }
                        ],
                        client=self.client,
                        output_schema=output_schema,
                    )
                return None


def _replace_computer_tools_with_agent_provider_specific_tools(
    cls, tools: list[BaseTool], client: AgentProviderClient
) -> list[BaseTool]:
    def _replace_tool_if_needed(tool: BaseTool) -> BaseTool:
        match type(client):
            case OpenAIClient:
                match tool._metadata.get("commandagi_tool_type"):
                    case "computer_use":
                        return OpenAIComputerUseTool(client)
                    case _:
                        return tool
                # TODO: in additionn to converting commandagi tools, you should also detect anthropic, openai, and scrappybara tools and convert them to the correct tool
            case AnthropicClient:
                match tool._metadata.get("commandagi_tool_type"):
                    case "computer_use":
                        return AnthropicComputerUseTool(client)
                    case _:
                        return tool

                # TODO: in additionn to converting commandagi tools, you should also detect anthropic, openai, and scrappybara tools and convert them to the correct tool
            case ScrappybaraClient:
                match tool._metadata.get("commandagi_tool_type"):
                    case "computer_use":
                        return OpenAIComputerUseTool(client)
                    case _:
                        return tool

                # TODO: in additionn to converting commandagi tools, you should also detect anthropic, openai, and scrappybara tools and convert them to the correct tool
            case CommandAGIClient:
                match tool._metadata.get("commandagi_tool_type"):
                    case "computer_use":
                        return OpenAIComputerUseTool(client)
                    case _:
                        return tool

                # TODO: in additionn to converting commandagi tools, you should also detect anthropic, openai, and scrappybara tools and convert them to the correct tool
            case _:
                return tool

    return [_replace_tool_if_needed(tool) for tool in tools]


def _chat_completion(
    messages: list[AnyChatMessage],
    client: AgentProviderClient,
    output_schema: Optional[type[TSchema]] = None,
) -> AnyChatMessage:
    match type(client):
        case OpenAIClient:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )
        case AnthropicClient:
            return client.messages.create(
                model="claude-3-5-sonnet-20240620",
                messages=messages,
            )
        case ScrappybaraClient:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )
        case CommandAGIClient:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )
        case _:
            raise ValueError(f"Unsupported client type: {type(client)}")
