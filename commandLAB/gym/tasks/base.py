from typing import Generic
from pydantic import BaseModel

from commandLAB.gym.environments.base_env import BaseEnv
from commandLAB.gym.drivers import ObsType, ActionType, Step, Episode


class BaseTask(Generic[ObsType, ActionType], BaseModel):
    """A task is a description of the goal of the agent."""

    description: str

    def evaluate(self, env: BaseEnv, episode: Episode[ObsType, ActionType]):
        """This function is called when the task is activated."""
        pass
