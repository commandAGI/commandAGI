from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Dict, Any
import numpy as np

from commandAGI.gym.agents.base_agent import BaseAgent
from commandAGI.gym.schema import Episode, ObsType, ActionType
from commandAGI.gym.drivers import BaseDriver


class BaseTrainer(Generic[ObsType, ActionType], ABC):
    """Base class for trainers."""

    def __init__(
        self,
        driver: BaseDriver[ObsType, ActionType],
        agent: BaseAgent[ObsType, ActionType],
    ):
        self.driver = driver
        self.agent = agent
        self.training_history: List[Dict[str, Any]] = []

    @abstractmethod
    def train(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        """Train the agent."""
        pass

    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        if not self.training_history:
            return {}

        stats = {}
        for key in self.training_history[0].keys():
            values = [h[key] for h in self.training_history]
            stats[f"{key}_mean"] = np.mean(values)
            stats[f"{key}_std"] = np.std(values)
        return stats


class OnlineTrainer(BaseTrainer[ObsType, ActionType]):
    """Trainer that trains after each episode."""

    def train(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        episodes = []
        for _ in range(num_episodes):
            episode = self.driver.collect_episode()
            self.agent.train(episode)
            episodes.append(episode)

            # Record training stats
            episode_stats = {
                "episode_length": episode.num_steps,
                "total_reward": sum(step.reward for step in episode),
            }
            self.training_history.append(episode_stats)

        return episodes


class OfflineTrainer(BaseTrainer[ObsType, ActionType]):
    """Trainer that trains after collecting all episodes."""

    def train(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        episodes = self.driver.collect_episodes(num_episodes)

        # Train on all episodes
        for episode in episodes:
            self.agent.train(episode)

            # Record training stats
            episode_stats = {
                "episode_length": episode.num_steps,
                "total_reward": sum(step.reward for step in episode),
            }
            self.training_history.append(episode_stats)

        return episodes


class BatchTrainer(BaseTrainer[ObsType, ActionType]):
    """Trainer that trains in batches of episodes."""

    def __init__(self, *args, batch_size: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size

    def train(self, num_episodes: int) -> List[Episode[ObsType, ActionType]]:
        episodes = []
        for i in range(0, num_episodes, self.batch_size):
            # Collect batch of episodes
            batch_size = min(self.batch_size, num_episodes - i)
            batch = self.driver.collect_episodes(batch_size)
            episodes.extend(batch)

            # Train on batch
            for episode in batch:
                self.agent.train(episode)

                # Record training stats
                episode_stats = {
                    "episode_length": episode.num_steps,
                    "total_reward": sum(step.reward for step in episode),
                }
                self.training_history.append(episode_stats)

        return episodes
