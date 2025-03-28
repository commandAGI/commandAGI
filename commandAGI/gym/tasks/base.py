from typing import Generic

from pydantic import BaseModel

from commandAGI.gym.drivers import ActionType, Episode, ObsType
from commandAGI.gym.environments.base_env import BaseEnv


class BaseTask(Generic[ObsType, ActionType], BaseModel):
    """A task is a description of the goal of the agent."""

    description: str

    def evaluate(self, env: BaseEnv, episode: Episode[ObsType, ActionType]):
        """This function is called when the task is activated."""
