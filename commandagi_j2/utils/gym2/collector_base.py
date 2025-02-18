from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, List, Type, Optional

from pydantic import BaseModel
from commandagi_j2.utils.gym2.base_env import Observation, Action


class BaseStep(BaseModel):
    observation: Observation
    action: Action
    reward: float
    info: Dict[str, Any]


class BaseEpisode(ABC):
    """Abstract base class for an episode of interaction."""

    @property
    @abstractmethod
    def num_steps(self) -> int:
        """Get the number of steps in the episode."""
        pass

    @property
    @abstractmethod
    def total_reward(self) -> float:
        """Get the total reward for the episode."""
        pass

    @abstractmethod
    def get_step(self, index: int) -> BaseStep:
        """Get a step from the current episode."""
        pass

    @abstractmethod
    def append_step(
        self,
        observation: Observation,
        action: Action,
        reward: float|None,
        info: Dict[str, Any],
    ) -> None:
        """Add a step to the current episode.

        Args:
            observation (Observation): The environment observation
            action (Action): The action taken
            reward (float): The reward received
            info (Dict[str, Any]): Additional information from the environment
        """
        pass

    @abstractmethod
    def update_step(self, index: int, step: BaseStep) -> None:
        """Update a step in the current episode.

        Args:
            index (int): The index of the step to update
            step (BaseStep): The new step data
        """
        pass

    @abstractmethod
    def remove_step(self, index: int) -> None:
        """Remove a step from the current episode.

        Args:
            index (int): The index of the step to remove
        """
        pass

    @abstractmethod
    def iter_steps(self) -> Iterator[BaseStep]:
        """Get an iterator over the steps in the episode.

        Returns:
            Iterator[BaseStep]: Iterator over episode steps
        """
        pass

    @abstractmethod
    def save(self, episode_name: str) -> None:
        """Save the current episode data.

        Args:
            episode_name (str): The episode name/identifier
        """

    def __len__(self) -> int:
        """Get the number of steps in the episode."""
        return self.num_steps

    def __getitem__(self, index: int) -> BaseStep:
        """Get a step from the episode."""
        return self.get_step(index)

    def __iter__(self) -> Iterator[BaseStep]:
        """Iterate over the steps in the episode."""
        return iter(self.iter_steps())
