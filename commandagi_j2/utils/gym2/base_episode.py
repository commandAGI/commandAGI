from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Generic, TypeVar
from pydantic import BaseModel

ObsType = TypeVar('ObsType')
ActType = TypeVar('ActType')
InfoType = TypeVar('InfoType', bound=Dict[str, Any])

class BaseStep(BaseModel, Generic[ObsType, ActType, InfoType]):
    observation: ObsType
    action: ActType
    reward: float
    info: InfoType

class BaseEpisode(Generic[ObsType, ActType, InfoType], ABC):
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
    def get_step(self, index: int) -> BaseStep[ObsType, ActType, InfoType]:
        """Get a step from the current episode."""
        pass

    @abstractmethod
    def append_step(
        self,
        observation: ObsType,
        action: ActType,
        reward: float|None,
        info: InfoType,
    ) -> None:
        """Add a step to the current episode."""
        pass

    @abstractmethod
    def update_step(self, index: int, step: BaseStep[ObsType, ActType, InfoType]) -> None:
        """Update a step in the current episode."""
        pass

    @abstractmethod
    def remove_step(self, index: int) -> None:
        """Remove a step from the current episode."""
        pass

    @abstractmethod
    def iter_steps(self) -> Iterator[BaseStep[ObsType, ActType, InfoType]]:
        """Get an iterator over the steps in the episode."""
        pass

    @abstractmethod
    def save(self, episode_name: str) -> None:
        """Save the current episode data."""
        pass

    def __len__(self) -> int:
        return self.num_steps

    def __getitem__(self, index: int) -> BaseStep[ObsType, ActType, InfoType]:
        return self.get_step(index)

    def __iter__(self) -> Iterator[BaseStep[ObsType, ActType, InfoType]]:
        return iter(self.iter_steps())
