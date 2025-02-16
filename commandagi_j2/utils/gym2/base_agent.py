from abc import ABC, abstractmethod
from commandagi_j2.utils.gym2.env_base import Observation

class BaseAgent(ABC):
    @abstractmethod
    def reset(self) -> None:
        """Reset the agent's internal state."""
        pass

    @abstractmethod
    def act(self, observation: Observation) -> str:
        """
        Given an observation, determine the next action.

        Args:
            observation (Observation): The current environment observation.
        
        Returns:
            str: The chosen action as a string.
        """
        pass

    @abstractmethod
    def update(self, reward: float) -> None:
        """
        Update the agent's internal state based on the received reward.

        Args:
            reward (float): The reward obtained from the last action.
        """
        pass 