from abc import abstractmethod
import asyncio
from contextlib import contextmanager
from enum import Enum
from typing import AsyncGenerator, Optional, TypeVar, Union, List
from pydantic import BaseModel
from commandAGI._utils.mcp_schema import MCPServerTransport, mcp_server_connections
from commandAGI.agents.base_agent import ComputerUseAgent, TSchema
from langchain.tools import BaseTool

from agents import Agent, Runner

from commandAGI.computers.base_computer import BaseComputer


AgentProviderClient = Union[
    CommandAGIClient, OpenAIClient, AnthropicClient, ScrappybaraClient, GeminiClient
]


class SimpleAgentRunState(BaseModel):
    """Schema for managing state during agent run."""
    step_count: int = 0
    history: List[dict] = []
    mcp_server_connections: List[MCPServerTransport] = []
    tools: List[BaseTool] = []


class SimpleComputerUseAgent(ComputerUseAgent):
    client: AgentProviderClient
    is_complete_prompt: str
    min_steps: Optional[int]
    max_steps: Optional[int]
    rules: list[str]
    max_retries: int = 3

    def __init__(
        self,
        system_prompt: str,
        tools: list[BaseTool],
        client: AgentProviderClient,
        mcp_servers: list[MCPServerTransport] = [],
        min_steps: Optional[int] = None,
        max_steps: Optional[int] = None,
        rules: list[str] = [],
        max_retries: int = 3,
    ):
        if min_steps is not None and max_steps is not None and min_steps > max_steps:
            raise ValueError("min_steps cannot be greater than max_steps")

        super().__init__(
            system_prompt=system_prompt, tools=tools, mcp_servers=mcp_servers
        )
        self.client = client
        self.min_steps = min_steps
        self.max_steps = max_steps
        self.tools = _replace_computer_tools_with_agent_provider_specific_tools(
            tools, client
        )
        self.rules = rules
        self.max_retries = max_retries

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

    async def _enforce_rules(self, history: list[ChatMessage]) -> None:
        """Enforce all rules in a single chat completion."""
        from dataclasses import dataclass
        from typing import Literal, Optional

        @dataclass
        class RuleState:
            rule: str
            rule_id: str
            status: Literal["indeterminate", "passed", "feedback", "fail"]
            feedback: Optional[str] = None

        response_index = len(history) - 1
        original_response = history[response_index]

        # Initialize rule states with IDs
        rule_states = [
            RuleState(rule=rule, rule_id=str(i), status="indeterminate")
            for i, rule in enumerate(self.rules)
        ]

        def pass_rule(rule_id: str) -> str:
            rule_state = next(rs for rs in rule_states if rs.rule_id == rule_id)
            rule_state.status = "passed"
            return "pass"

        def pass_all() -> str:
            for rs in rule_states:
                rs.status = "passed"
            return "pass"

        def retry_rule(rule_id: str, feedback: str) -> str:
            rule_state = next(rs for rs in rule_states if rs.rule_id == rule_id)
            rule_state.status = "feedback"
            rule_state.feedback = feedback
            return feedback

        def fail_rule(rule_id: str, reason: Optional[str] = None) -> str:
            rule_state = next(rs for rs in rule_states if rs.rule_id == rule_id)
            rule_state.status = "fail"
            rule_state.feedback = reason
            return reason or "Rule violation"

        rule_tools = [
            BaseTool(
                name="pass_rule",
                description="Pass if a specific rule is followed",
                func=pass_rule,
                args_schema=lambda: {"rule_id": str},
            ),
            BaseTool(
                name="pass_all",
                description="Pass if all rules are followed",
                func=pass_all,
            ),
            BaseTool(
                name="retry_rule",
                description="Request a retry with feedback for a specific rule",
                func=retry_rule,
                args_schema=lambda: {"rule_id": str, "feedback": str},
            ),
            BaseTool(
                name="fail_rule",
                description="Fail with an optional reason for a specific rule",
                func=fail_rule,
                args_schema=lambda: {"rule_id": str, "reason": (str, None)},
            ),
        ]

        for attempt in range(self.max_retries):
            # Get rules that need checking
            rules_to_check = [
                rs for rs in rule_states if rs.status in ("indeterminate", "feedback")
            ]

            if not rules_to_check:
                return

            # Create a single prompt with all rules that need checking
            rules_prompt = "\n".join(
                f"Rule {rs.rule_id}: {rs.rule}" for rs in rules_to_check
            )
            prompt = (
                "Review the conversation history and check if it follows these rules:\n"
                f"{rules_prompt}\n\n"
                "You can:\n"
                "1. Use pass_all if ALL rules are followed\n"
                "2. Use pass_rule for each rule that passes\n"
                "3. Use retry_rule with feedback for rules that need changes\n"
                "4. Use fail_rule if any rule is violated beyond repair\n"
                "\nCheck all rules and respond with appropriate tool calls."
            )

            result = await _chat_completion(
                history + [{"role": "user", "content": prompt}],
                client=self.client,
                tools=rule_tools,
            )

            if not result.tool_calls:
                continue

            # Execute all tool calls - they'll modify rule_states directly
            for tool_call in result.tool_calls:
                tool = next(t for t in rule_tools if t.name == tool_call.function.name)
                tool.run(tool_call.function.arguments)

            # Check if any rule failed
            failed_rule = next((rs for rs in rule_states if rs.status == "fail"), None)
            if failed_rule:
                del history[response_index + 1 :]
                history[response_index] = original_response
                raise ValueError(
                    f"Rule {failed_rule.rule_id} violation: {failed_rule.feedback or 'Rule violation'}"
                )

            # Check if we need to retry
            rules_with_feedback = [rs for rs in rule_states if rs.status == "feedback"]
            if rules_with_feedback:
                feedbacks = [
                    f"Rule {rs.rule_id} '{rs.rule}': {rs.feedback}"
                    for rs in rules_with_feedback
                ]
                feedback_message = "\n".join(feedbacks)

                history.append(
                    {
                        "role": "system",
                        "content": f"Previous response violated rules. Please revise based on the following feedback:\n{feedback_message}",
                    }
                )
                new_response = await _chat_completion(history, client=self.client)
                history[response_index] = new_response

                # Reset feedback states to indeterminate
                for rs in rules_with_feedback:
                    rs.status = "indeterminate"
                    rs.feedback = None

            elif all(rs.status == "passed" for rs in rule_states):
                # All rules passed, clean up and return
                final_response = history[response_index]
                del history[response_index + 1 :]
                history[response_index] = final_response
                return

        # If we hit max retries, clean up and raise error
        raise ValueError("Max retries exceeded while trying to enforce rules")

    async def run(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> TSchema | None:
        with mcp_server_connections(self.mcp_servers) as mcp_server_connections:
            state = SimpleAgentRunState(
                step_count=0,
                history=[{"role": "user", "content": prompt}],
                mcp_server_connections=mcp_server_connections,
                tools=self.tools + [
                    *[
                        mcp_server_connection.get_tool()
                        for mcp_server_connection in mcp_server_connections
                    ]
                ]
            )

            while True:
                # Generate action based on history
                response = _chat_completion(state.history, client=self.client, tools=state.tools)
                state.history.append(response)

                # Enforce rules before executing tool calls
                if self.rules:
                    await self._enforce_rules(state.history)

                state.step_count += 1

                # Execute any tool calls
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool = next(
                            t for t in state.tools if t.name == tool_call.function.name
                        )
                        result = tool.run(tool_call.function.arguments)
                        state.history.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": str(result),
                            }
                        )

                # If we've hit max_steps, finish
                if self.max_steps is not None and state.step_count >= self.max_steps:
                    return self._format_output(state.history, output_schema)

                # Only check completion if we're past min_steps
                if self.min_steps is None or state.step_count >= self.min_steps:
                    is_complete = _chat_completion(
                        state.history
                        + [{"role": "user", "content": self.is_complete_prompt}],
                        client=self.client,
                        output_schema=bool,
                    )

                    if is_complete:
                        return self._format_output(state.history, output_schema)


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
