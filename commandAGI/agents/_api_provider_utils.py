import json
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

import instructor
from anthropic import Anthropic as AnthropicClient
from google.genai import Client as GeminiClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from openai import Client as OpenAIClient
from pydantic import BaseModel

from commandAGI.agents.base_agent import AgentEvent
from commandAGI.agents.events import (
    AgentResponseEvent,
    SystemInputEvent,
    ToolCallEvent,
    ToolResultEvent,
    UserInputEvent,
)
from commandAGI.client import Client as CommandAGIClient

TSchema = TypeVar("TSchema", bound=BaseModel)


class AIClientType(Enum):
    COMMANDAGI = "commandagi"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LANGCHAIN = "langchain"


AIClient = Union[
    CommandAGIClient, OpenAIClient, AnthropicClient, GeminiClient, BaseChatModel
]


def _get_api_provider_type_for_client(client: AIClient) -> AIClientType:
    if isinstance(client, CommandAGIClient):
        return AIClientType.COMMANDAGI
    elif isinstance(client, OpenAIClient):
        return AIClientType.OPENAI
    elif isinstance(client, AnthropicClient):
        return AIClientType.ANTHROPIC
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
        if (
            isinstance(tool, MultiBackendTool)
            and provider_type in tool.backend_mappings
        ):
            # For backend-hosted tools, we just need to return the tool name
            # as the backend already knows how to handle it
            return tool.backend_mappings[provider_type]
        return tool

    return [_replace_tool_if_needed(tool) for tool in tools]


def _generate_response_commandagi(
    client: CommandAGIClient,
    inputs: list[Union[ChatMessage, AgentEvent]],
    tools: Optional[list[BaseTool]] = None,
    output_schema: Optional[type[TSchema]] = None,
    **additional_kwargs,
) -> List[AgentEvent]:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        events=inputs,
        tools=tools,
        output_schema=output_schema,
        **additional_kwargs,
    )


def _generate_response_openai(
    client: OpenAIClient,
    inputs: list[Union[ChatMessage, AgentEvent]],
    tools: Optional[list[BaseTool]] = None,
    output_schema: Optional[type[TSchema]] = None,
    **additional_kwargs,
) -> List[AgentEvent]:
    if output_schema:
        client = instructor.patch(client)

    messages = []
    for input in inputs:
        if isinstance(input, ChatMessage):
            messages.append(
                {
                    "role": (
                        input.type
                        if hasattr(input, "type")
                        else input.__class__.__name__.lower().replace("message", "")
                    ),
                    "content": input.content,
                    **(
                        {"function_call": input.additional_kwargs["function_call"]}
                        if hasattr(input, "additional_kwargs")
                        and "function_call" in input.additional_kwargs
                        else {}
                    ),
                }
            )
        elif isinstance(input, AgentResponseEvent):
            message = {"role": input.role, "content": input.content}
            if input.name:
                message["name"] = input.name
            if input.tool_calls:
                message["tool_calls"] = input.tool_calls
            messages.append(message)
        elif isinstance(input, SystemInputEvent):
            messages.append({"role": "system", "content": input.content})
        elif isinstance(input, UserInputEvent):
            messages.append({"role": "user", "content": input.content})
        elif isinstance(input, ToolCallEvent):
            last_assistant_idx = next(
                (
                    i
                    for i in range(len(messages) - 1, -1, -1)
                    if messages[i]["role"] == "assistant"
                ),
                None,
            )
            tool_call = {
                "id": input.call_id,
                "type": "function",
                "function": {
                    "name": input.tool_name,
                    "arguments": json.dumps(input.arguments),
                },
            }
            if last_assistant_idx is not None:
                if "tool_calls" not in messages[last_assistant_idx]:
                    messages[last_assistant_idx]["tool_calls"] = []
                messages[last_assistant_idx]["tool_calls"].append(tool_call)
            else:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [tool_call],
                    }
                )
        elif isinstance(input, ToolResultEvent):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": input.call_id,
                    "content": str(input.result) if input.success else str(input.error),
                }
            )

    if output_schema:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            response_model=output_schema,
            **additional_kwargs,
        )
        return [
            AgentResponseEvent.from_structured(
                role="assistant",
                structured=response,
            )
        ]
    else:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            **additional_kwargs,
        )
        message = response.choices[0].message
        return [
            AgentResponseEvent(
                role="assistant",
                content=message.content or "",
                name=getattr(message, "name", None),
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (message.tool_calls or [])
                ],
            )
        ]


def _generate_response_anthropic(
    client: AnthropicClient,
    inputs: list[Union[ChatMessage, AgentEvent]],
    tools: Optional[list[BaseTool]] = None,
    output_schema: Optional[type[TSchema]] = None,
    **additional_kwargs,
) -> List[AgentEvent]:
    if output_schema:
        client = instructor.from_anthropic(create=client)

    messages = []
    for input in inputs:
        if isinstance(input, ChatMessage):
            messages.append(
                {
                    "role": (
                        input.type
                        if hasattr(input, "type")
                        else input.__class__.__name__.lower().replace("message", "")
                    ),
                    "content": input.content,
                    **(
                        {
                            "tool_calls": [
                                {
                                    "tool": fc["name"],
                                    "tool_call_id": str(uuid.uuid4()),
                                    "parameters": json.loads(fc["arguments"]),
                                }
                            ]
                            for fc in [input.additional_kwargs["function_call"]]
                            if hasattr(input, "additional_kwargs")
                            and "function_call" in input.additional_kwargs
                        }
                    ),
                }
            )
        elif isinstance(input, AgentResponseEvent):
            message = {"role": input.role, "content": input.content}
            if input.name:
                message["name"] = input.name
            if input.tool_calls:
                message["tool_calls"] = [
                    {
                        "tool": tc["function"]["name"],
                        "tool_call_id": tc["id"],
                        "parameters": json.loads(tc["function"]["arguments"]),
                    }
                    for tc in input.tool_calls
                ]
            messages.append(message)
        elif isinstance(input, SystemInputEvent):
            messages.append({"role": "system", "content": input.content})
        elif isinstance(input, UserInputEvent):
            messages.append({"role": "user", "content": input.content})
        elif isinstance(input, ToolCallEvent):
            last_assistant_idx = next(
                (
                    i
                    for i in range(len(messages) - 1, -1, -1)
                    if messages[i]["role"] == "assistant"
                ),
                None,
            )
            tool_call = {
                "tool": input.tool_name,
                "tool_call_id": input.call_id,
                "parameters": input.arguments,
            }
            if last_assistant_idx is not None:
                if "tool_calls" not in messages[last_assistant_idx]:
                    messages[last_assistant_idx]["tool_calls"] = []
                messages[last_assistant_idx]["tool_calls"].append(tool_call)
            else:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [tool_call],
                    }
                )
        elif isinstance(input, ToolResultEvent):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": input.call_id,
                    "content": str(input.result) if input.success else str(input.error),
                }
            )

    if output_schema:
        response = client(
            model="claude-3-5-sonnet-20240620",
            messages=messages,
            tools=tools,
            response_model=output_schema,
            **additional_kwargs,
        )
        return [
            AgentResponseEvent.from_structured(
                role="assistant",
                structured=response,
            )
        ]
    else:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            messages=messages,
            tools=tools,
            **additional_kwargs,
        )
        message = response.content[0]
        return [
            AgentResponseEvent(
                role="assistant",
                content=message.text,
                tool_calls=[
                    {
                        "id": tc.tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tc.tool,
                            "arguments": json.dumps(tc.parameters),
                        },
                    }
                    for tc in (message.tool_calls or [])
                ],
            )
        ]


def _generate_response_gemini(
    client: GeminiClient,
    inputs: list[Union[ChatMessage, AgentEvent]],
    tools: Optional[list[BaseTool]] = None,
    output_schema: Optional[type[TSchema]] = None,
    **additional_kwargs,
) -> List[AgentEvent]:
    messages = []
    for input in inputs:
        if isinstance(input, ChatMessage):
            message = {
                "role": (
                    input.type
                    if hasattr(input, "type")
                    else input.__class__.__name__.lower().replace("message", "")
                ),
                "content": input.content,
            }
            if (
                hasattr(input, "additional_kwargs")
                and "function_call" in input.additional_kwargs
            ):
                message["tool_calls"] = [
                    {
                        "function_call": {
                            "name": input.additional_kwargs["function_call"]["name"],
                            "args": json.loads(
                                input.additional_kwargs["function_call"]["arguments"]
                            ),
                        }
                    }
                ]
            messages.append(message)
        elif isinstance(input, AgentResponseEvent):
            message = {"role": input.role, "content": input.content}
            if input.name:
                message["name"] = input.name
            if input.tool_calls:
                message["tool_calls"] = [
                    {
                        "function_call": {
                            "name": tc["function"]["name"],
                            "args": json.loads(tc["function"]["arguments"]),
                        }
                    }
                    for tc in input.tool_calls
                ]
            messages.append(message)
        elif isinstance(input, SystemInputEvent):
            messages.append({"role": "system", "content": input.content})
        elif isinstance(input, UserInputEvent):
            messages.append({"role": "user", "content": input.content})
        elif isinstance(input, ToolCallEvent):
            # Gemini handles tool calls differently - they are processed in the client
            pass
        elif isinstance(input, ToolResultEvent):
            # Gemini handles tool results differently - they are processed in the client
            pass

    if output_schema:
        response = client.generate_content(
            model="gemini-pro",
            messages=messages,
            tools=tools,
            config={
                "response_mime_type": "application/json",
                "response_schema": output_schema,
                **additional_kwargs,
            },
        )
        structured = output_schema.model_validate_json(response.parsed)
        return [
            AgentResponseEvent.from_structured(
                role="assistant",
                structured=structured,
            )
        ]
    else:
        response = client.generate_content(
            model="gemini-pro",
            messages=messages,
            tools=tools,
            **additional_kwargs,
        )
        message = response.candidates[0].content
        return [
            AgentResponseEvent(
                role="assistant",
                content=message.parts[0].text,
                tool_calls=[
                    {
                        "id": str(uuid.uuid4()),
                        "type": "function",
                        "function": {
                            "name": tc.function_call.name,
                            "arguments": json.dumps(tc.function_call.args),
                        },
                    }
                    for tc in (message.tool_calls or [])
                ],
            )
        ]


def _generate_response_langchain(
    client: BaseChatModel,
    inputs: list[Union[ChatMessage, AgentEvent]],
    tools: Optional[list[BaseTool]] = None,
    output_schema: Optional[type[TSchema]] = None,
    **additional_kwargs,
) -> List[AgentEvent]:
    if output_schema:
        client = instructor.patch(client)

    lc_messages = []
    for input in inputs:
        if isinstance(input, ChatMessage):
            lc_messages.append(input)  # Use ChatMessage directly
        elif isinstance(input, SystemInputEvent):
            lc_messages.append(SystemMessage(content=input.content))
        elif isinstance(input, UserInputEvent):
            lc_messages.append(HumanMessage(content=input.content))
        elif isinstance(input, AgentResponseEvent):
            if input.tool_calls:
                tool_calls_str = "\n".join(
                    [
                        f"Tool Call {tc['id']}: {tc['function']['name']}({tc['function']['arguments']})"
                        for tc in input.tool_calls
                    ]
                )
                content = (
                    f"{input.content}\n\nTool Calls:\n{tool_calls_str}"
                    if input.content
                    else tool_calls_str
                )
            else:
                content = input.content
            lc_messages.append(AIMessage(content=content))
        elif isinstance(input, ToolCallEvent):
            lc_messages.append(
                AIMessage(
                    content="",
                    additional_kwargs={
                        "function_call": {
                            "name": input.tool_name,
                            "arguments": json.dumps(input.arguments),
                        }
                    },
                )
            )
        elif isinstance(input, ToolResultEvent):
            lc_messages.append(
                ToolMessage(
                    content=str(input.result) if input.success else str(input.error),
                    tool_call_id=input.call_id,
                )
            )

    # Configure tools if provided
    if tools:
        client.callbacks = [
            tool for tool in tools
        ]  # Set tools as callbacks for LangChain

    if output_schema:
        response = client.generate(
            lc_messages,
            response_model=output_schema,
            **additional_kwargs,
        )
        return [
            AgentResponseEvent.from_structured(
                role="assistant",
                structured=response,
            )
        ]
    else:
        response = client.generate(lc_messages, **additional_kwargs)
        content = response.content or ""

        # Extract tool calls if present in the response
        tool_calls = []
        if (
            hasattr(response, "additional_kwargs")
            and "function_call" in response.additional_kwargs
        ):
            function_call = response.additional_kwargs["function_call"]
            tool_calls.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "function",
                    "function": {
                        "name": function_call["name"],
                        "arguments": function_call["arguments"],
                    },
                }
            )

        return [
            AgentResponseEvent(
                role="assistant",
                content=content,
                name=None,
                tool_calls=tool_calls if tool_calls else None,
            )
        ]


def generate_response(
    inputs: list[Union[ChatMessage, AgentEvent]],
    /,
    client: AIClient,
    output_schema: Optional[type[TSchema]] = None,
    tools: Optional[list[BaseTool]] = None,
    **additional_kwargs,
) -> List[AgentEvent]:
    """Handle chat completion for different providers with their specific parameters."""
    provider_type = _get_api_provider_type_for_client(client)
    tools = _format_tools_for_api_provider(tools, provider_type)

    match provider_type:
        case AIClientType.COMMANDAGI:
            return _generate_response_commandagi(
                client, inputs, tools, output_schema, **additional_kwargs
            )
        case AIClientType.OPENAI:
            return _generate_response_openai(
                client, inputs, tools, output_schema, **additional_kwargs
            )
        case AIClientType.ANTHROPIC:
            return _generate_response_anthropic(
                client, inputs, tools, output_schema, **additional_kwargs
            )
        case AIClientType.GEMINI:
            return _generate_response_gemini(
                client, inputs, tools, output_schema, **additional_kwargs
            )
        case AIClientType.LANGCHAIN:
            return _generate_response_langchain(
                client, inputs, tools, output_schema, **additional_kwargs
            )
        case _:
            raise ValueError(f"Unsupported client type: {type(client)}")
