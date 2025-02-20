from abc import ABC
from typing import Any, Dict, Generic, Optional, TypeVar

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")


class Callback(Generic[ObsType, ActType], ABC):
    """Base class for callbacks that can be registered with the driver."""

    def on_episode_start(self) -> None:
        """Called when an episode starts."""
        pass

    def on_step(
        self,
        observation: ObsType,
        action: ActType,
        reward: float,
        info: Dict[str, Any],
        done: bool,
        step_num: int,
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
