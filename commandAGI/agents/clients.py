from enum import Enum
from typing import Dict, Type, Optional
from commandAGI.agents.base_agent import AgentEvent
from langchain_core.tools import BaseTool

from openai import Client as OpenAIClient
from anthropic import Client as AnthropicClient
from scrappybara import Client as ScrappybaraClient
from google.generativeai import GenerativeAI
from commandAGI.client import Client as CommandAGIClient

class AIClientType(Enum):
    COMMANDAGI = "commandagi"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SCRAPPYBARA = "scrappybara"
    GEMINI = "gemini"

AIClient = Union[CommandAGIClient, OpenAIClient, AnthropicClient, ScrappybaraClient, GenerativeAI]

class MultiBackendTool(BaseTool):
    def __init__(
        self,
        backend_mappings: Dict[AIClientType, str],
        default_tool: Optional[Type[BaseTool]] = None
    ):
        self.backend_mappings = backend_mappings
        self.default_tool = default_tool

def _replace_computer_tools_with_agent_provider_specific_tools(
    cls, tools: list[BaseTool], client: AIClient
) -> list[BaseTool]:
    def _replace_tool_if_needed(tool: BaseTool) -> BaseTool:
        if isinstance(tool, MultiBackendTool):
            provider = _get_provider_for_client(client)
            if provider in tool.backend_mappings:
                # For backend-hosted tools, we just need to return the tool name
                # as the backend already knows how to handle it
                return tool.backend_mappings[provider]
            elif tool.default_tool:
                return tool.default_tool(client)
            return tool
        return tool

    def _get_provider_for_client(client: AIClient) -> AIClientType:
        client_type = type(client)
        match client_type:
            case CommandAGIClient: return AIClientType.COMMANDAGI
            case OpenAIClient: return AIClientType.OPENAI
            case AnthropicClient: return AIClientType.ANTHROPIC
            case ScrappybaraClient: return AIClientType.SCRAPPYBARA
            case GenerativeAI: return AIClientType.GEMINI
            case _: raise ValueError(f"Unsupported client type: {client_type}")

    return [_replace_tool_if_needed(tool) for tool in tools]


def _chat_completion_from_events(
    events: list[AgentEvent],
    client: AIClient,
    output_schema: Optional[type[TSchema]] = None,
    tools: Optional[list[BaseTool]] = None,
) -> ChatMessage:
    messsages = []
    # TODO: convert events to messages. many events will become assistant messages, but some will become system messages or tool calls


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
