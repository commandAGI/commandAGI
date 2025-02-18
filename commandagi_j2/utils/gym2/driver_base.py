from abc import ABC, abstractmethod
from typing import Optional, Union, List, Type, TypeVar, Generic, Dict, Any
from commandagi_j2.utils.gym2.base_env import Env
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.base_episode import BaseEpisode
from commandagi_j2.utils.gym2.callbacks import Callback

ObsType = TypeVar('ObsType')
ActType = TypeVar('ActType')
InfoType = TypeVar('InfoType', bound=Dict[str, Any])

class BaseDriver(Generic[ObsType, ActType, InfoType], ABC):
    """Abstract base class for driving agent-environment interactions."""

    episode_cls: Type[BaseEpisode[ObsType, ActType, InfoType]]
    callbacks: List[Callback]

    @abstractmethod
    def __init__(
        self,
        env: Optional[Env[ObsType, ActType, InfoType]] = None,
        agent: Optional[BaseAgent[ObsType, ActType]] = None,
        episode_cls: Type[BaseEpisode[ObsType, ActType, InfoType]] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        """Initialize the driver.

        Args:
            env (Optional[Env]): The environment to use
            agent (Optional[BaseAgent]): The agent to use
            episode_cls (Type[BaseEpisode]): The episode class to use
            callbacks (Optional[List[Callback]]): List of callbacks to register
        """

    @abstractmethod
    def run_episode(
        self,
        max_steps: int = 100,
        episode_name: Optional[str] = None,
        return_episode: bool = False,
    ) -> Union[float, BaseEpisode[ObsType, ActType, InfoType]]:
        """Run a single episode.

        Args:
            max_steps (int): Maximum number of steps to run
            episode_name (Optional[str]): Episode identifier for data collection
            return_episode (bool): Whether to return the full episode data

        Returns:
            Union[float, Episode]: Either the total reward or full episode data
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the driver's state."""

    def register_callback(self, callback: Callback) -> None:
        """Register a callback to be used during episode execution."""
        self.callbacks.append(callback)
