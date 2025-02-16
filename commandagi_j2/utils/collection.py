from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json
from commandagi_j2.utils.gym2.env_base import Observation, Action
from commandagi_j2.utils.gym2.collector_base import BaseCollector

@dataclass
class Episode:
    observations: List[Observation]
    actions: List[Action]
    rewards: List[float]
    infos: List[Dict[str, Any]]
    total_reward: float

class DataCollector(BaseCollector):
    def __init__(self, save_dir: str = "collected_data"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.current_episode = None
        self.reset()
    
    def reset(self) -> None:
        """Start a new episode"""
        self.current_episode = Episode(
            observations=[],
            actions=[],
            rewards=[],
            infos=[],
            total_reward=0.0
        )
    
    def add_step(self, observation: Observation, action: Action, reward: float, info: Dict[str, Any]) -> None:
        """Add a step to the current episode"""
        self.current_episode.observations.append(observation)
        self.current_episode.actions.append(action)
        self.current_episode.rewards.append(reward)
        self.current_episode.infos.append(info)
        self.current_episode.total_reward += reward
    
    def save_episode(self, episode_num: int) -> None:
        """Save the current episode to disk"""
        episode_data = {
            'observations': self.current_episode.observations,
            'actions': self.current_episode.actions,
            'rewards': self.current_episode.rewards,
            'infos': self.current_episode.infos,
            'total_reward': self.current_episode.total_reward
        }
        
        filepath = self.save_dir / f"episode_{episode_num}.json"
        with open(filepath, 'w') as f:
            json.dump(episode_data, f, indent=2) 