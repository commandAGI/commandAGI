from abc import ABC, abstractmethod
from typing import Dict, Any
from commandagi_j2.utils.gym2.base_env import Observation, Action


class BaseEpisode(ABC):
    """Abstract base class for an episode of interaction."""


class BaseCollector(ABC):
    """Abstract base class for data collection during environment interaction."""

    @abstractmethod
    def reset(self) -> None:
        """Reset the collector's state for a new episode."""

    @abstractmethod
    def add_step(
        self, 
        observation: Observation,
        action: Action,
        reward: float,
        info: Dict[str, Any],
    ) -> None:
        """Add a step to the current episode.

        Args:
            observation (Observation): The environment observation
            action (Action): The action taken
            reward (float): The reward received
            info (Dict[str, Any]): Additional information from the environment
        """

    @abstractmethod
    def save_episode(self, episode_num: int) -> None:
        """Save the current episode data.

        Args:
            episode_num (int): The episode number/identifier
        """
