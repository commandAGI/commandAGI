from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Iterator, Tuple, TypeVar

from pydantic import BaseModel

from commandLAB.gym.collection import Episode, Step, ObsType, ActionType


class BaseEnv(Generic[ObsType, ActionType], ABC):
    """Abstract base class for environments."""

    _active: bool = True

    def __del__(self):
        if self._active:
            self.close()

    def reset(self) -> ObsType:
        """Reset the environment and return initial observation."""
        self._active = True
        observation = self.get_observation()
        return observation

    def close(self):
        """Clean up environment resources.

        This method should be implemented by subclasses to properly clean up any resources
        like network connections, file handles, or external processes that need to be
        explicitly closed or terminated.
        """
        self._active = False

    def step(self, action: ActionType) -> Tuple[ObsType, float, bool, Dict[str, Any]]:
        """Execute action and return (observation, reward, done, info).

        Args:
            action (ActType): Action to execute

        Returns:
            observation (ObsType): Environment observation
            reward (float): Reward from the action
            done (bool): Whether episode has ended
            info (Dict[str, Any]): Additional information
        """
        """Execute an action and return the next observation, reward, done, and info."""
        success = self.execute_action(action)
        if not success:
            raise ValueError(f"Action {action} failed to execute")
        observation = self.get_observation()
        reward = self.get_reward(action)
        done = self.get_done(action)
        info = self.get_info()
        return observation, reward, done, info

    @abstractmethod
    def get_observation(self) -> ObsType:
        """Get the current observation from the environment.

        This method should be implemented by subclasses to return the current state observation.
        """

    @abstractmethod
    def execute_action(self, action: ActionType) -> bool:
        """Execute an action and return success flag."""

    @abstractmethod
    def get_reward(self, action: ActionType) -> float:
        """Get the reward for an action.

        Args:
            action (ActType): The action that was executed

        Returns:
            float: The reward for the action
        """

    @abstractmethod
    def get_done(self, action: ActionType) -> bool:
        """Get the done flag for an action.

        Returns:
            bool: Whether the episode is done
        """

    def get_info(self) -> Dict[str, Any]:
        """Get the info for an action.

        Returns:
            Dict[str, Any]: Additional information
        """
        return {}
