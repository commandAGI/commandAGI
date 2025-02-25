from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from commandLAB.gym.schema import Episode
from commandLAB.types import ComputerAction, ComputerObservation

ObsType = TypeVar('ObsType')
ActionType = TypeVar('ActionType')

class BaseAgent(BaseModel, Generic[ObsType, ActionType], ABC):
    """Base class for agents"""

    @abstractmethod
    def reset(self) -> None:
        """Reset the agent's internal state."""

    @abstractmethod
    def act(self, observation: ObsType) -> ActionType:
        """Given an observation, determine the next action.

        Args:
            observation (ObsType): The current environment observation.

        Returns:
            ActionType: The chosen action.
        """

    @abstractmethod
    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the reward."""

    @abstractmethod
    def train(self, episodes: list[Episode]) -> None:
        """Train the agent on an episode."""
