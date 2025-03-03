from abc import ABC, abstractmethod
from typing import Generic
from pydantic import BaseModel, Field

from langchain.output_parsers.boolean import BooleanOutputParser

from commandAGI2.gym.environments.base_env import BaseEnv
from commandAGI2.gym.drivers import ObsType, ActionType, Step, Episode
from commandAGI2.gym.tasks.base import BaseTask
from commandAGI2.gym._utils.llms import get_chat_model


class BaseEvaluator(Generic[ObsType, ActionType], BaseModel, ABC):
    """A base class for evaluators that use LLMs to evaluate tasks."""

    @abstractmethod
    def evaluate(self, env: BaseEnv, episode: Episode[ObsType, ActionType]): ...


class GoalStateEvaluator(BaseEvaluator[ObsType, ActionType]):
    """A task is a description of the goal of the agent."""

    description: str
    goal: str
    boolean_output_parser: BooleanOutputParser = Field(
        default_factory=BooleanOutputParser
    )

    def evaluate(self, env: BaseEnv, episode: Episode[ObsType, ActionType]):
        """This function is called when the task is activated."""
        return self.llm_evaluate_final_state(env, episode)

    def llm_evaluate_final_state(
        self, env: BaseEnv, episode: Episode[ObsType, ActionType]
    ):
        """This function is called when the task is activated."""
        message = [
            {
                "type": "text",
                "text": "Compare these final state from the env against the goal state.",
            },
            {"type": "text", "text": f"Goal state: {self.goal}"},
            {"type": "text", "text": f"Final state: {episode[-1].observation}"},
            {
                "type": "text",
                "text": "Did the agent satisfy the goal state?"
                + self.boolean_output_parser.get_format_instructions(),
            },
        ]
        model = get_chat_model()
        response = model.invoke(message)
        return self.boolean_output_parser.parse(response.content)


class ObjectiveSeekingEvaluator(BaseEvaluator[ObsType, ActionType]):
    """A task that evaluates the entire trajectory by sampling steps."""

    description: str
    mission: str
    step_sample_modulus: int = Field(
        default=5, description="Sample every n steps for evaluation"
    )

    def evaluate(self, env: BaseEnv, episode: Episode[ObsType, ActionType]):
        """Evaluate the trajectory by sampling steps and checking against goal state."""
        return self.llm_evaluate_trajectory(env, episode)

    def llm_evaluate_trajectory(
        self, env: BaseEnv, episode: Episode[ObsType, ActionType]
    ):
        """Sample steps from trajectory and evaluate progress toward goal."""
        sampled_steps = episode[:: self.step_sample_modulus]

        message = [
            {
                "type": "text",
                "text": "Evaluate if this trajectory of states achieves its mission.",
            },
            {"type": "text", "text": f"Mission: {self.mission}"},
            {"type": "text", "text": "Trajectory of states:"},
        ]

        for i, step in enumerate(sampled_steps):
            message.append(
                {
                    "type": "text",
                    "text": f"Step {i * self.step_sample_modulus}: {step.observation}",
                }
            )

        message.append(
            {
                "type": "text",
                "text": "Did the agent achieve its mission?"
                + self.boolean_output_parser.get_format_instructions(),
            }
        )

        model = get_chat_model()
        response = model.invoke(message)
        return self.boolean_output_parser.parse(response.content)
