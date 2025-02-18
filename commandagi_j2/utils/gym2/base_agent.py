from abc import ABC, abstractmethod
from commandagi_j2.utils.gym2.base_env import Observation


class BaseAgent(ABC):
    """Base class for all agents in the environment."""

    @abstractmethod
    def reset(self) -> None:
        """Reset the agent's internal state."""

    @abstractmethod
    def act(self, observation: Observation) -> str:
        """Given an observation, determine the next action.

        Args:
            observation (Observation): The current environment observation.

        Returns:
            str: The chosen action as a string.
        """

    @abstractmethod
    def update(self, reward: float) -> None:  # TODO: move reward to `act``
        """Update the agent's internal state based on the received reward.

        Args:
            reward (float): The reward obtained from the last action.
        """
