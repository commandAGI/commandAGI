from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")


class BaseAgent(Generic[ObsType, ActType], ABC):
    """Base class for all agents in the environment."""

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
    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the received reward.

        Args:
            reward (float): The reward obtained from the last action.
        """
