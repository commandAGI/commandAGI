from enum import Enum
from typing import Dict, Type, Optional, List, TypeVar, Union, Any
import json
import uuid

from pydantic import BaseModel
from commandAGI.agents.base_agent import AgentEvent
from commandAGI.agents.events import (
    AgentResponseEvent,
    SystemInputEvent,
    UserInputEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from openai import Client as OpenAIClient
from anthropic import Anthropic as AnthropicClient
from scrapybara.client import BaseClient as ScrappybaraClient
from google.genai import Client as GeminiClient
from commandAGI.client import Client as CommandAGIClient

TSchema = TypeVar("TSchema", bound=BaseModel)

class AIClientType(Enum):
    COMMANDAGI = "commandagi"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SCRAPPYBARA = "scrappybara"
    GEMINI = "gemini"
    LANGCHAIN = "langchain"


AIClient = Union[
    CommandAGIClient, 
    OpenAIClient, 
    AnthropicClient, 
    ScrappybaraClient, 
    GeminiClient,
    BaseChatModel
]


def _get_api_provider_type_for_client(client: AIClient) -> AIClientType:
    if isinstance(client, CommandAGIClient):
        return AIClientType.COMMANDAGI
    elif isinstance(client, OpenAIClient):
        return AIClientType.OPENAI
    elif isinstance(client, AnthropicClient):
        return AIClientType.ANTHROPIC
    elif isinstance(client, ScrappybaraClient):
        return AIClientType.SCRAPPYBARA
    elif isinstance(client, GeminiClient):
        return AIClientType.GEMINI
    elif isinstance(client, BaseChatModel):
        return AIClientType.LANGCHAIN
    else:
        raise ValueError(f"Unsupported client type: {type(client)}")


class MultiBackendTool(BaseTool):
    backend_mappings: Dict[AIClientType, BaseTool]


def _format_tools_for_api_provider(
    cls, tools: list[BaseTool], provider_type: AIClientType
) -> list[BaseTool]:
    def _replace_tool_if_needed(tool: BaseTool) -> BaseTool:
        if isinstance(tool, MultiBackendTool) and provider_type in tool.backend_mappings:
            # For backend-hosted tools, we just need to return the tool name
            # as the backend already knows how to handle it
            return tool.backend_mappings[provider_type]
        return tool

    return [_replace_tool_if_needed(tool) for tool in tools]


def _format_events_for_api_provider(
    events: list[AgentEvent], provider: AIClientType
) -> List[Dict[str, Any]]:
    """Convert agent events to provider-specific chat messages format."""
    messages = []

    for event in events:
        if isinstance(event, AgentResponseEvent):
            message = {"role": event.role, "content": event.content}
            if event.name:
                message["name"] = event.name
            if event.tool_calls:
                message["tool_calls"] = event.tool_calls
            messages.append(message)

        elif isinstance(event, SystemInputEvent):
            messages.append({"role": "system", "content": event.content})

        elif isinstance(event, UserInputEvent):
            messages.append({"role": "user", "content": event.content})

        elif isinstance(event, ToolCallEvent):
            # Find most recent assistant message to attach tool calls to
            last_assistant_idx = next(
                (
                    i
                    for i in range(len(messages) - 1, -1, -1)
                    if messages[i]["role"] == "assistant"
                ),
                None,
            )

            tool_call = None
            if provider in [
                AIClientType.OPENAI,
                AIClientType.COMMANDAGI,
                AIClientType.SCRAPPYBARA,
            ]:
                tool_call = {
                    "id": event.call_id,
                    "type": "function",
                    "function": {
                        "name": event.tool_name,
                        "arguments": json.dumps(event.arguments),
                    },
                }
            elif provider == AIClientType.ANTHROPIC:
                tool_call = {
                    "tool": event.tool_name,
                    "tool_call_id": event.call_id,
                    "parameters": event.arguments,
                }

            if tool_call:
                if last_assistant_idx is not None:
                    # Attach to existing message
                    if "tool_calls" not in messages[last_assistant_idx]:
                        messages[last_assistant_idx]["tool_calls"] = []
                    messages[last_assistant_idx]["tool_calls"].append(tool_call)
                else:
                    # Create new message if no assistant message exists
                    messages.append(
                        {
                            "role": "assistant",
                            "content": "",  # Empty string instead of None for better compatibility
                            "tool_calls": [tool_call],
                        }
                    )
            # Gemini has its own format handled in the client

        elif isinstance(event, ToolResultEvent):
            if provider in [
                AIClientType.OPENAI,
                AIClientType.COMMANDAGI,
                AIClientType.SCRAPPYBARA,
            ]:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": event.call_id,
                        "content": (
                            str(event.result) if event.success else str(event.error)
                        ),
                    }
                )
            elif provider == AIClientType.ANTHROPIC:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": event.call_id,
                        "content": (
                            str(event.result) if event.success else str(event.error)
                        ),
                    }
                )

    return messages


def _convert_to_events(response, provider_type: AIClientType) -> List[AgentEvent]:
    events = []
    
    if provider_type in [AIClientType.OPENAI, AIClientType.COMMANDAGI, AIClientType.SCRAPPYBARA]:
        message = response.choices[0].message
        events.append(AgentResponseEvent(
            role=message.role,
            content=message.content or "",
            name=getattr(message, 'name', None),
            tool_calls=[{
                'id': tc.id,
                'type': tc.type,
                'function': {
                    'name': tc.function.name,
                    'arguments': tc.function.arguments
                }
            } for tc in (message.tool_calls or [])]
        ))
        
    elif provider_type == AIClientType.ANTHROPIC:
        message = response.content[0]
        events.append(AgentResponseEvent(
            role="assistant",
            content=message.text,
            tool_calls=[{
                'id': tc.tool_call_id,
                'type': 'function',
                'function': {
                    'name': tc.tool,
                    'arguments': json.dumps(tc.parameters)
                }
            } for tc in (message.tool_calls or [])]
        ))
        
    elif provider_type == AIClientType.GEMINI:
        message = response.candidates[0].content
        events.append(AgentResponseEvent(
            role="assistant",
            content=message.parts[0].text,
            tool_calls=[{
                'id': str(uuid.uuid4()),  # Gemini doesn't provide IDs
                'type': 'function',
                'function': {
                    'name': tc.function_call.name,
                    'arguments': json.dumps(tc.function_call.args)
                }
            } for tc in (message.tool_calls or [])]
        ))
        
    elif provider_type == AIClientType.LANGCHAIN:
        events.append(AgentResponseEvent(
            role="assistant",
            content=response.content,
            name=None,
            tool_calls=None
        ))
        
    return events


def _generate_response_commandagi(
    client: CommandAGIClient,
    messages: List[Dict[str, Any]],
    tools: Optional[list[BaseTool]] = None,
) -> List[AgentEvent]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        events=messages,
        tools=tools,
    )
    return _convert_to_events(response, AIClientType.COMMANDAGI)


def _generate_response_openai(
    client: OpenAIClient,
    messages: List[Dict[str, Any]],
    tools: Optional[list[BaseTool]] = None,
) -> List[AgentEvent]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
    )
    return _convert_to_events(response, AIClientType.OPENAI)


def _generate_response_anthropic(
    client: AnthropicClient,
    messages: List[Dict[str, Any]],
    tools: Optional[list[BaseTool]] = None,
) -> List[AgentEvent]:
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        messages=messages,
        tools=tools,
    )
    return _convert_to_events(response, AIClientType.ANTHROPIC)


def _generate_response_gemini(
    client: GeminiClient,
    messages: List[Dict[str, Any]],
    tools: Optional[list[BaseTool]] = None,
) -> List[AgentEvent]:
    response = client.generate_content(
        model="gemini-pro",
        messages=messages,
        tools=tools,
    )
    return _convert_to_events(response, AIClientType.GEMINI)


def _generate_response_scrappybara(
    client: ScrappybaraClient,
    messages: List[Dict[str, Any]],
    tools: Optional[list[BaseTool]] = None,
) -> List[AgentEvent]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
    )
    return _convert_to_events(response, AIClientType.SCRAPPYBARA)


def _generate_response_langchain(
    client: BaseChatModel,
    messages: List[Dict[str, Any]],
    tools: Optional[list[BaseTool]] = None,
) -> List[AgentEvent]:
    # Convert messages to Langchain message format
    lc_messages = []
    for msg in messages:
        if msg["role"] == "system":
            lc_messages.append(SystemMessage(content=msg["content"]))
        elif msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "tool":
            lc_messages.append(ToolMessage(content=msg["content"], tool_call_id=msg.get("tool_call_id")))
    
    response = client.generate(lc_messages)
    return _convert_to_events(response, AIClientType.LANGCHAIN)


def generate_response(
    events: list[AgentEvent],
    /,
    client: AIClient,
    output_schema: Optional[type[TSchema]] = None,
    tools: Optional[list[BaseTool]] = None,
) -> List[AgentEvent]:
    """Handle chat completion for different providers with their specific parameters."""
    provider_type = _get_api_provider_type_for_client(client)
    messages = _format_events_for_api_provider(events, provider_type)
    tools = _format_tools_for_api_provider(tools, provider_type)
    
    provider_handlers = {
        AIClientType.COMMANDAGI: _generate_response_commandagi,
        AIClientType.OPENAI: _generate_response_openai,
        AIClientType.ANTHROPIC: _generate_response_anthropic,
        AIClientType.GEMINI: _generate_response_gemini,
        AIClientType.SCRAPPYBARA: _generate_response_scrappybara,
        AIClientType.LANGCHAIN: _generate_response_langchain,
    }
    
    if provider_type not in provider_handlers:
        raise ValueError(f"Unsupported client type: {type(client)}")
        
    return provider_handlers[provider_type](client, messages, tools)
