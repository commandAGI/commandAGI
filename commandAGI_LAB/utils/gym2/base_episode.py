from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Iterator, TypeVar

from pydantic import BaseModel

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")


class BaseStep(BaseModel, Generic[ObsType, ActType]):
    observation: ObsType
    action: ActType
    reward: float
    info: Dict[str, Any]


class BaseEpisode(Generic[ObsType, ActType], ABC):
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
    def get_step(self, index: int) -> BaseStep[ObsType, ActType]:
        """Get a step from the current episode."""
        pass

    @abstractmethod
    def append_step(
        self,
        observation: ObsType,
        action: ActType,
        reward: float | None,
        info: Dict[str, Any],
    ) -> None:
        """Add a step to the current episode."""
        pass

    @abstractmethod
    def update_step(self, index: int, step: BaseStep[ObsType, ActType]) -> None:
        """Update a step in the current episode."""
        pass

    @abstractmethod
    def remove_step(self, index: int) -> None:
        """Remove a step from the current episode."""
        pass

    @abstractmethod
    def iter_steps(self) -> Iterator[BaseStep[ObsType, ActType]]:
        """Get an iterator over the steps in the episode."""
        pass

    @abstractmethod
    def save(self, episode_name: str) -> None:
        """Save the current episode data."""
        pass

    def __len__(self) -> int:
        return self.num_steps

    def __getitem__(self, index: int) -> BaseStep[ObsType, ActType]:
        return self.get_step(index)

    def __iter__(self) -> Iterator[BaseStep[ObsType, ActType]]:
        return iter(self.iter_steps())
