from abc import ABC, abstractmethod
from typing import Optional, Union
from commandagi_j2.utils.gym2.env_base import Env
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.collector_base import BaseCollector, BaseEpisode


class BaseDriver(ABC):
    """Abstract base class for driving agent-environment interactions.

    >>> from commandagi_j2.utils.gym2.driver_base import BaseDriver
    >>> issubclass(BaseDriver, ABC)
    True
    """

    @abstractmethod
    def __init__(
        self,
        env: Optional[Env] = None,
        agent: Optional[BaseAgent] = None,
        collector: Optional[BaseCollector] = None,
    ):
        """Initialize the driver.

        Args:
            env (Optional[Env]): The environment to use
            agent (Optional[BaseAgent]): The agent to use
            collector (Optional[BaseCollector]): The data collector to use

        >>> class MockDriver(BaseDriver):
        ...     def __init__(self, env=None, agent=None, collector=None): pass
        ...     def run_episode(self, max_steps=100, episode_num=None, return_episode=False): pass
        ...     def reset(self): pass
        >>> driver = MockDriver()
        """

    @abstractmethod
    def run_episode(
        self,
        max_steps: int = 100,
        episode_num: Optional[int] = None,
        return_episode: bool = False,
    ) -> Union[float, BaseEpisode]:
        """Run a single episode.

        Args:
            max_steps (int): Maximum number of steps to run
            episode_num (Optional[int]): Episode identifier for data collection
            return_episode (bool): Whether to return the full episode data

        Returns:
            Union[float, Episode]: Either the total reward or full episode data

        >>> class MockDriver(BaseDriver):
        ...     def __init__(self, env=None, agent=None, collector=None): pass
        ...     def run_episode(self, max_steps=100, episode_num=None, return_episode=False): return 1.0
        ...     def reset(self): pass
        >>> driver = MockDriver()
        >>> driver.run_episode(max_steps=10)
        1.0
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the driver's state.

        >>> class MockDriver(BaseDriver):
        ...     def __init__(self, env=None, agent=None, collector=None): pass
        ...     def run_episode(self, max_steps=100, episode_num=None, return_episode=False): pass
        ...     def reset(self): pass
        >>> driver = MockDriver()
        >>> driver.reset()
        """
