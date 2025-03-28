import multiprocessing as mp
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Generic, List

from commandAGI.gym.agents.base_agent import BaseAgent
from commandAGI.gym.environments.base_env import BaseEnv
from commandAGI.gym.schema import ActionType, Episode, InMemoryEpisode, ObsType, Step


class BaseDriver(Generic[ObsType, ActionType], ABC):
    """Abstract base class for drivers."""

    def __init__(
        self,
        env: BaseEnv[ObsType, ActionType],
        agent: BaseAgent[ObsType, ActionType],
        episode_cls: type[Episode[ObsType, ActionType]] = InMemoryEpisode,
    ):
        self.env = env
        self.agent = agent
        self.episode_cls = episode_cls

    @abstractmethod
    def collect_episodes(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        """Collect multiple episodes."""

    @abstractmethod
    def collect_episode(self) -> Episode[ObsType, ActionType]:
        """Collect a single episode."""

    def close(self):
        """Clean up resources."""
        self.env.close()


class SimpleDriver(BaseDriver[ObsType, ActionType]):
    """Single-threaded sequential driver implementation."""

    def collect_episodes(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        return [self.collect_episode() for _ in range(num_episodes)]

    def collect_episode(self) -> Episode[ObsType, ActionType]:
        observation = self.env.reset()
        self.agent.reset()
        episode = self.episode_cls()

        done = False
        while not done:
            action = self.agent.act(observation)
            next_obs, reward, done, info = self.env.step(action)
            step = Step(
                observation=observation, action=action, reward=reward, info=info
            )
            episode.push(step)
            observation = next_obs

        return episode


class ThreadedDriver(BaseDriver[ObsType, ActionType]):
    """Multi-threaded driver for environments that support threading."""

    def __init__(self, *args, max_workers: int = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_workers = max_workers or mp.cpu_count()

    def collect_episodes(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            episodes = list(
                executor.map(lambda _: self.collect_episode(), range(num_episodes))
            )
        return episodes

    def collect_episode(self) -> Episode[ObsType, ActionType]:
        return super().collect_episode()


class MultiprocessDriver(BaseDriver[ObsType, ActionType]):
    """Multi-process driver for CPU-bound environments."""

    def __init__(self, *args, max_workers: int = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_workers = max_workers or mp.cpu_count()

    def collect_episodes(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            episodes = list(
                executor.map(lambda _: self.collect_episode(), range(num_episodes))
            )
        return episodes

    def collect_episode(self) -> Episode[ObsType, ActionType]:
        return super().collect_episode()
