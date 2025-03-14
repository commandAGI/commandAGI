from abc import abstractmethod
from contextlib import contextmanager
from typing import AsyncGenerator, Optional, TypeVar, Union
from pydantic import BaseModel
from commandAGI._utils.mcp_schema import MCPServerTransport, mcp_server_connections
from commandAGI.agents.base_agent import ComputerUseAgent, TSchema
from langchain.tools import BaseTool

from agents import Agent, Runner

from commandAGI.computers.base_computer import BaseComputer


AgentProviderClient = Union[
    CommandAGIClient, OpenAIClient, AnthropicClient, ScrappybaraClient, GeminiClient
]


class SimpleComputerUseAgent(ComputerUseAgent):
    client: AgentProviderClient
    is_complete_prompt: str
    min_steps: Optional[int]
    max_steps: Optional[int]

    def __init__(
        self, 
        system_prompt: str, 
        tools: list[BaseTool], 
        client: AgentProviderClient,
        mcp_servers: list[MCPServerTransport] = [],
        min_steps: Optional[int] = None,
        max_steps: Optional[int] = None,
    ):
        if min_steps is not None and max_steps is not None and min_steps > max_steps:
            raise ValueError("min_steps cannot be greater than max_steps")
        
        super().__init__(
            system_prompt=system_prompt,
            tools=tools,
            mcp_servers=mcp_servers
        )
        self.client = client
        self.min_steps = min_steps
        self.max_steps = max_steps
        self.tools = _replace_computer_tools_with_agent_provider_specific_tools(
            tools, client
        )

    def _format_output(
        self,
        history: list,
        output_schema: Optional[type[TSchema]] = None,
    ) -> TSchema | None:
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

    def run(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> TSchema | None:
        with mcp_server_connections(self.mcp_servers) as mcp_server_connections:

            tools = self.tools + [
                *[
                    mcp_server_connection.get_tool()
                    for mcp_server_connection in mcp_server_connections
                ]
            ]

            history = [{"role": "user", "content": prompt}]
            step_count = 0

            while True:
                # Generate action based on history
                response = _chat_completion(history, client=self.client, tools=tools)
                history.append(response)
                step_count += 1

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

                # If we've hit max_steps, finish
                if self.max_steps is not None and step_count >= self.max_steps:
                    return self._format_output(history, output_schema)

                # Only check completion if we're past min_steps
                if self.min_steps is None or step_count >= self.min_steps:
                    is_complete = _chat_completion(
                        history + [{"role": "user", "content": self.is_complete_prompt}],
                        client=self.client,
                        output_schema=bool,
                    )

                    if is_complete:
                        return self._format_output(history, output_schema)


def _replace_computer_tools_with_agent_provider_specific_tools(
    cls, tools: list[BaseTool], client: AgentProviderClient
) -> list[BaseTool]:
    def _replace_tool_if_needed(tool: BaseTool) -> BaseTool:
        match type(client):
            case CommandAGIClient:
                match tool._metadata.get("commandagi_tool_type"):
                    case "computer_use":
                        return OpenAIComputerUseTool(client)
                    case _:
                        return tool

                # TODO: in additionn to converting commandagi tools, you should also detect anthropic, openai, and scrappybara tools and convert them to the correct tool
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
            case GeminiClient:
                match tool._metadata.get("commandagi_tool_type"):
                    case "computer_use":
                        return GeminiComputerUseTool(client)
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
    tools: Optional[list[BaseTool]] = None,
) -> AnyChatMessage:
    match type(client):
        case CommandAGIClient:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )
        case OpenAIClient:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )
        case AnthropicClient:
            return client.messages.create(
                model="claude-3-5-sonnet-20240620",
                messages=messages,
                tools=tools,
            )
        case ScrappybaraClient:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )
        case GeminiClient:
            return client.generate_content(
                model="gemini-pro",
                messages=messages,
                tools=tools,
            )
        case _:
            raise ValueError(f"Unsupported client type: {type(client)}")
