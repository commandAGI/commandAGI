from __future__ import annotations

import asyncio
import traceback
from contextlib import contextmanager
from dataclasses import Field
from typing import (
    AsyncGenerator,
    List,
    Literal,
    Optional,
    Protocol,
    Union,
)

from langchain.tools import BaseTool
from pydantic import BaseModel

from commandAGI._utils.mcp_schema import (
    MCPServerConnection,
    MCPServerTransport,
    mcp_server_connections,
)
from commandAGI._utils.resource_schema import BaseResource
from commandAGI._utils.rfc6902 import JsonPatchOperation
from commandAGI.agents._api_provider_utils import (
    AIClient,
    generate_response,
)
from commandAGI.agents.base_agent import (
    AgentResponseEvent,
    BaseAgent,
    BaseAgentHooks,
    BaseAgentRunSession,
    SystemInputEvent,
    TSchema,
    UserInputEvent,
)
from commandAGI.agents.events import (
    AgentEvent,
    ErrorEvent,
    ResourceCalloutEvent,
    ThoughtEvent,
    ToolCallEvent,
    ToolResultEvent,
)


class RuleState(BaseModel):
    rule: str
    rule_id: str
    status: Literal["indeterminate", "passed", "feedback", "fail"]
    feedback: Optional[str] = None


class OnStepDraftHook(Protocol):
    def __call__(self, response: AgentResponseEvent) -> None: ...


class OnRuleCheckHook(Protocol):
    def __call__(self, rule_states: list[RuleState]) -> None: ...


class OnStepHook(Protocol):
    def __call__(self, response: AgentResponseEvent) -> None: ...


class OnMessageInsertHook(Protocol):
    def __call__(
        self,
        message_index: int,
        message: Union[
            AgentResponseEvent,
            UserInputEvent,
            SystemInputEvent,
            ThoughtEvent,
            ToolCallEvent,
            ToolResultEvent,
            ErrorEvent,
        ],
    ) -> None: ...


class OnMessageDeleteHook(Protocol):
    def __call__(self, message_index: int) -> None: ...


class OnMessageStartUpdateHook(Protocol):
    def __call__(self, message_index: int) -> None: ...


class OnMessageUpdateOperationHook(Protocol):
    def __call__(self, message_index: int, operation: JsonPatchOperation) -> None: ...


class OnMessageEndUpdateHook(Protocol):
    def __call__(self, message_index: int) -> None: ...


class OnToolExecutionStartHook(Protocol):
    def __call__(self, message_index: int, tool_call_index: int) -> None: ...


class OnToolExecutionEndHook(Protocol):
    def __call__(self, message_index: int, tool_call_index: int) -> None: ...


class OnToolExecutionErrorHook(Protocol):
    def __call__(
        self, message_index: int, tool_call_index: int, error: Exception
    ) -> None: ...


class OnFinishHook(Protocol):
    def __call__(
        self,
        finish_message_index: int,
        reason: Literal["max_steps", "is_complete", "manual"],
    ) -> None: ...


class OnErrorHook(Protocol):
    def __call__(self, error: Exception) -> None: ...


class AgentHooks(BaseAgentHooks):
    on_step_draft_hooks: list[OnStepDraftHook] = Field(default_factory=list)
    on_rule_check_hooks: list[OnRuleCheckHook] = Field(default_factory=list)
    on_step_hooks: list[OnStepHook] = Field(default_factory=list)
    on_message_insert_hooks: list[OnMessageInsertHook] = Field(default_factory=list)
    on_message_delete_hooks: list[OnMessageDeleteHook] = Field(default_factory=list)
    on_message_start_update_hooks: list[OnMessageStartUpdateHook] = Field(
        default_factory=list
    )
    on_message_update_operation_hooks: list[OnMessageUpdateOperationHook] = Field(
        default_factory=list
    )
    on_message_end_update_hooks: list[OnMessageEndUpdateHook] = Field(
        default_factory=list
    )
    on_tool_execution_start_hooks: list[OnToolExecutionStartHook] = Field(
        default_factory=list
    )
    on_tool_execution_end_hooks: list[OnToolExecutionEndHook] = Field(
        default_factory=list
    )
    on_tool_execution_error_hooks: list[OnToolExecutionErrorHook] = Field(
        default_factory=list
    )
    on_finish_hooks: list[OnFinishHook] = Field(default_factory=list)
    on_error_hooks: list[OnErrorHook] = Field(default_factory=list)


class AgentRunSession(BaseAgentRunSession):
    agent: Agent
    directly_supplied_tools: list[BaseTool] = []
    directly_supplied_resources: list[BaseResource] = []
    mcp_server_connections: list[MCPServerConnection] = []

    @property
    def tools(self) -> list[BaseTool]:
        all_tools = self.directly_supplied_tools.copy()
        for connection in self.mcp_server_connections:
            all_tools.extend(connection.tools())
        return all_tools

    @property
    def resources(self) -> list[BaseResource]:
        all_resources = self.directly_supplied_resources.copy()
        for connection in self.mcp_server_connections:
            all_resources.extend(connection.resources())
        return all_resources

    _hooks: AgentHooks = Field(default_factory=AgentHooks)

    state: Literal["running", "paused", "stopped"] = "running"

    def __init__(
        self,
        objective: str,
        agent: Agent,
        events: list[AgentEvent] = [],
        tools: list[BaseTool] = [],
        resources: list[BaseResource] = [],
        mcp_server_connections: list[MCPServerConnection] = [],
    ):
        super().__init__(
            objective=objective,
            agent=agent,
            events=events,
            directly_supplied_tools=tools,
            directly_supplied_resources=resources,
            mcp_server_connections=mcp_server_connections,
        )

    def pause(self):
        self.state = "paused"

    def resume(self):
        self.state = "running"

    def stop(self):
        self.state = "stopped"

    def on_step_draft(self, func: OnStepDraftHook):
        self._hooks.on_step_draft_hooks.append(func)

    def on_rule_check(self, func: OnRuleCheckHook):
        self._hooks.on_rule_check_hooks.append(func)

    def on_step(self, func: OnStepHook):
        self._hooks.on_step_hooks.append(func)

    def on_message_insert(self, func: OnMessageInsertHook):
        self._hooks.on_message_insert_hooks.append(func)

    def on_message_delete(self, func: OnMessageDeleteHook):
        self._hooks.on_message_delete_hooks.append(func)

    def on_message_start_update(self, func: OnMessageStartUpdateHook):
        self._hooks.on_message_start_update_hooks.append(func)

    def on_message_update_operation(self, func: OnMessageUpdateOperationHook):
        self._hooks.on_message_update_operation_hooks.append(func)

    def on_message_end_update(self, func: OnMessageEndUpdateHook):
        self._hooks.on_message_end_update_hooks.append(func)

    def on_tool_execution_start(self, func: OnToolExecutionStartHook):
        self._hooks.on_tool_execution_start_hooks.append(func)

    def on_tool_execution_end(self, func: OnToolExecutionEndHook):
        self._hooks.on_tool_execution_end_hooks.append(func)

    def on_tool_execution_error(self, func: OnToolExecutionErrorHook):
        self._hooks.on_tool_execution_error_hooks.append(func)

    def on_finish(self, func: OnFinishHook):
        self._hooks.on_finish_hooks.append(func)

    def on_error(self, func: OnErrorHook):
        self._hooks.on_error_hooks.append(func)


class Agent(BaseAgent):
    client: AIClient
    is_complete_prompt: str
    min_steps: Optional[int]
    max_steps: Optional[int]
    rules: list[str]
    max_retries: int = 3
    directly_supplied_tools: list[BaseTool]
    directly_supplied_resources: List[Resource]
    """
    NOTE: tools are not necesarily the tools that the agnet's LLM kernel will have access to for the following reasons:
    1. the mcp_servers may supply additional tools
    2. the agent architecture may dynamicly select a subset of tools to offer to the LLM kernel based on the context at hand
    """
    mcp_servers: list[MCPServerTransport] = Field(default_factory=list)
    """
    config info for conecting to mcp servers
    """

    def __init__(
        self,
        system_prompt: str,
        tools: list[BaseTool],
        resources: list[BaseResource],
        client: AIClient,
        mcp_servers: list[MCPServerTransport] = [],
        min_steps: Optional[int] = None,
        max_steps: Optional[int] = None,
        rules: list[str] = [],
        max_retries: int = 3,
    ):
        if min_steps is not None and max_steps is not None and min_steps > max_steps:
            raise ValueError("min_steps cannot be greater than max_steps")

        super().__init__(system_prompt=system_prompt)
        self.directly_supplied_tools = tools
        self.directly_supplied_resources = resources
        self.client = client
        self.mcp_servers = mcp_servers
        self.min_steps = min_steps
        self.max_steps = max_steps
        self.rules = rules
        self.max_retries = max_retries

    def _format_output(
        self,
        history: list,
        output_schema: Optional[type[TSchema]] = None,
    ) -> TSchema | None:
        if output_schema:
            return generate_response(
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

    async def _enforce_rules(self, history: list[AgentResponseEvent]) -> None:
        """Enforce all rules in a single chat completion."""
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

            result = await generate_response(
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

            # Call hooks again after rules are updated
            for hook in self._hooks.on_rule_check_hooks:
                hook(rule_states)

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
                new_response = await generate_response(history, client=self.client)
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

    @contextmanager
    async def session(
        self, prompt: str, *, output_schema: Optional[type[TSchema]] = None
    ) -> AsyncGenerator["AgentRunSession", None]:
        with mcp_server_connections(self.mcp_servers) as mcp_server_connections:
            state = AgentRunSession(
                agent=self,
                step_count=0,
                mcp_server_connections=mcp_server_connections,
                directly_supplied_tools=self.directly_supplied_tools,
                directly_supplied_resources=self.directly_supplied_resources,
                objective=prompt,
            )
            # Initialize with user input
            state.add_event(UserInputEvent(content=prompt))
            yield state

    async def _check_running_state(self, state: AgentRunSession) -> bool:
        """Check if agent should continue running. Returns False if stopped, handles pause with sleep loop."""
        if state.state == "stopped":
            return False
        while state.state == "paused":
            await asyncio.sleep(0.1)
            if state.state == "stopped":
                return False
        return True

    async def _run(self, state: AgentRunSession) -> TSchema | None:
        try:
            while True:
                # Check running state
                if not await self._check_running_state(state):
                    return None

                # Process any resource callouts since last agent response
                last_agent_response_idx = next(
                    (
                        i
                        for i in range(len(state.events) - 1, -1, -1)
                        if isinstance(state.events[i], AgentResponseEvent)
                    ),
                    -1,
                )

                if not await self._check_running_state(state):
                    return None

                resource_callouts = [
                    event
                    for event in state.events[last_agent_response_idx + 1 :]
                    if isinstance(event, ResourceCalloutEvent)
                ]

                for callout in resource_callouts:
                    if not await self._check_running_state(state):
                        return None

                    resource = next(
                        (
                            r
                            for r in state.resources
                            if r.resource_id == callout.resource_id
                        ),
                        None,
                    )
                    if resource:
                        relevant_items = resource.get_relevant_items(callout.query)
                        # Add the retrieval event
                        state.add_resource_retrieval(
                            resource_id=callout.resource_id,
                            query=callout.query,
                            results=relevant_items,
                        )

                if not await self._check_running_state(state):
                    return None

                # Generate action based on history
                response = generate_response(
                    state.events, client=self.client, tools=state.tools
                )

                if not await self._check_running_state(state):
                    return None

                # Add the response as an agent response event
                state.add_agent_response(
                    role="assistant",
                    content=response.content,
                    tool_calls=(
                        response.tool_calls if hasattr(response, "tool_calls") else None
                    ),
                )

                for hook in state._hooks.on_step_draft_hooks:
                    hook(response)

                if not await self._check_running_state(state):
                    return None

                # Enforce rules before executing tool calls
                if self.rules:
                    await self._enforce_rules(state)

                state.step_count += 1
                for hook in state._hooks.on_step_hooks:
                    hook(response)

                # Execute any tool calls
                if response.tool_calls:
                    for tool_call_index, tool_call in enumerate(response.tool_calls):
                        if not await self._check_running_state(state):
                            return None

                        try:
                            for hook in state._hooks.on_tool_execution_start_hooks:
                                hook(len(state.events) - 1, tool_call_index)

                            tool = next(
                                t
                                for t in state.tools
                                if t.name == tool_call.function.name
                            )

                            # Add tool call event
                            call_id = state.add_tool_call(
                                tool_name=tool_call.function.name,
                                arguments=tool_call.function.arguments,
                            )

                            try:
                                result = tool.run(tool_call.function.arguments)
                                # Add successful tool result
                                state.add_tool_result(call_id=call_id, result=result)
                            except Exception as e:
                                # Add failed tool result
                                state.add_tool_result(
                                    call_id=call_id,
                                    result=None,
                                    error=str(e),
                                    success=False,
                                )
                                raise

                            for hook in state._hooks.on_tool_execution_end_hooks:
                                hook(len(state.events) - 1, tool_call_index)
                        except Exception as e:
                            for hook in state._hooks.on_tool_execution_error_hooks:
                                hook(len(state.events) - 1, tool_call_index, e)
                            state.add_error(
                                error_type="tool_execution_error",
                                message=str(e),
                                traceback=traceback.format_exc(),
                            )
                            raise

                if not await self._check_running_state(state):
                    return None

                # If we've hit max_steps, finish
                if self.max_steps is not None and state.step_count >= self.max_steps:
                    for hook in state._hooks.on_finish_hooks:
                        hook(len(state.events) - 1, "max_steps")
                    return self._format_output(state.events, self.output_schema)

                # Only check completion if we're past min_steps
                if self.min_steps is None or state.step_count >= self.min_steps:
                    # Create a copy of events and add completion check message only to the copy
                    events_copy = state.events.copy()
                    events_copy.append(
                        SystemInputEvent(content=self.is_complete_prompt)
                    )
                    is_complete = generate_response(
                        events_copy,
                        client=self.client,
                        output_schema=bool,
                    )

                    if is_complete:
                        for hook in state._hooks.on_finish_hooks:
                            hook(len(state.events) - 1, "is_complete")
                        return self._format_output(state.events, self.output_schema)

        except Exception as e:
            state.add_error(
                error_type="run_error", message=str(e), traceback=traceback.format_exc()
            )
            for hook in state._hooks.on_error_hooks:
                hook(e)
            raise
