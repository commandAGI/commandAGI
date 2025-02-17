from abc import ABC, abstractmethod
from typing import Dict, Any
from commandagi_j2.utils.gym2.env_base import Observation, Action


class BaseEpisode(ABC):
    """Abstract base class for an episode of interaction.

    >>> from commandagi_j2.utils.gym2.collector_base import BaseEpisode
    >>> issubclass(BaseEpisode, ABC)
    True
    """

    pass


class BaseCollector(ABC):
    """Abstract base class for data collection during environment interaction.

    >>> from commandagi_j2.utils.gym2.collector_base import BaseCollector
    >>> issubclass(BaseCollector, ABC)
    True
    """

    @abstractmethod
    def reset(self) -> None:
        """Reset the collector's state for a new episode.

        >>> class MockCollector(BaseCollector):
        ...     def reset(self): pass
        ...     def add_step(self, observation, action, reward, info): pass
        ...     def save_episode(self, episode_num): pass
        >>> collector = MockCollector()
        >>> collector.reset()
        """
        pass

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

        >>> class MockCollector(BaseCollector):
        ...     def reset(self): pass
        ...     def add_step(self, observation, action, reward, info): pass
        ...     def save_episode(self, episode_num): pass
        >>> collector = MockCollector()
        >>> collector.add_step("obs", "action", 1.0, {"info": "test"})
        """
        pass

    @abstractmethod
    def save_episode(self, episode_num: int) -> None:
        """Save the current episode data.

        Args:
            episode_num (int): The episode number/identifier

        >>> class MockCollector(BaseCollector):
        ...     def reset(self): pass
        ...     def add_step(self, observation, action, reward, info): pass
        ...     def save_episode(self, episode_num): pass
        >>> collector = MockCollector()
        >>> collector.save_episode(1)
        """
        pass
