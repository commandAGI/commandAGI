from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from commandagi_j2.utils.gym2.base_env import Observation, Action


class Callback(ABC):
    """Base class for callbacks that can be registered with the driver."""
    
    def on_episode_start(self) -> None:
        """Called when an episode starts."""
        pass
        
    def on_step(
        self,
        observation: Observation,
        action: Action,
        reward: float,
        info: Dict[str, Any],
        done: bool,
        step_num: int
    ) -> None:
        """Called after each step in the environment.
        
        Args:
            observation: The current observation
            action: The action that was taken
            reward: The reward received
            info: Additional info from the environment
            done: Whether the episode is complete
            step_num: The current step number
        """
        pass
        
    def on_episode_end(self, episode_name: Optional[str] = None) -> None:
        """Called when an episode ends.
        
        Args:
            episode_name: Optional episode identifier
        """
        pass 