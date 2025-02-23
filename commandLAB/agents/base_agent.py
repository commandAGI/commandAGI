from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from commandLAB.utils.gym2.structures import Episode, Step, ObsType, ActType


class BaseAgent(Generic[ObsType, ActType], ABC):
    """Base class for agents"""

    @abstractmethod
    def reset(self) -> None:
        """Reset the agent's internal state."""

    @abstractmethod
    def act(self, observation: ObsType) -> ActType:
        """Given an observation, determine the next action.

        Args:
            observation (ObsType): The current environment observation.

        Returns:
            ActType: The chosen action.
        """

    @abstractmethod
    def train(self, episode: Episode) -> None:
        """Train the agent on an episode."""
