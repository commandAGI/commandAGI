from abc import ABC, abstractmethod
from typing import Callable, Generic, List, Optional, TypeVar, Union

from commandLAB.utils.gym2.base_agent import BaseAgent
from commandLAB.utils.gym2.base_env import Env
from commandLAB.utils.gym2.base_episode import BaseEpisode
from commandLAB.utils.gym2.callbacks import Callback

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")


class BaseDriver(Generic[ObsType, ActType], ABC):
    """Abstract base class for driving agent-environment interactions."""

    episode_constructor: Callable[[], BaseEpisode[ObsType, ActType]]
    callbacks: List[Callback]

    @abstractmethod
    def __init__(
        self,
        env: Optional[Env[ObsType, ActType]] = None,
        agent: Optional[BaseAgent[ObsType, ActType]] = None,
        episode_constructor: Optional[
            Callable[[], BaseEpisode[ObsType, ActType]]
        ] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        """Initialize the driver.

        Args:
            env (Optional[Env]): The environment to use
            agent (Optional[BaseAgent]): The agent to use
            episode_constructor (Optional[Callable[[], BaseEpisode]]): Function to create new episodes
            callbacks (Optional[List[Callback]]): List of callbacks to register
        """

    @abstractmethod
    def run_episode(
        self,
        max_steps: int = 100,
        episode_name: Optional[str] = None,
        return_episode: bool = False,
    ) -> Union[float, BaseEpisode[ObsType, ActType]]:
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
