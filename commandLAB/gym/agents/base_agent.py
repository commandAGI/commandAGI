from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from commandLAB.types import ComputerAction, ComputerObservation


class BaseComputerAgent(BaseModel, ABC):
    """Base class for agents"""

    @abstractmethod
    def reset(self) -> None:
        """Reset the agent's internal state."""

    @abstractmethod
    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Given an observation, determine the next action.

        Args:
            observation (ComputerObservation): The current environment observation.

        Returns:
            ComputerAction: The chosen action.
        """

    @abstractmethod
    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the reward."""

    @abstractmethod
    def train(self, episodes: List[Episode]) -> None:
        """Train the agent on an episode."""
