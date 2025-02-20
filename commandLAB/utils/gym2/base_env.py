from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Tuple, TypeVar

from commandagi_j2.utils.gym2.spaces import Space

# Define generic type variables
ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")


class Env(Generic[ObsType, ActType], ABC):
    """Abstract base class for environments."""

    @property
    @abstractmethod
    def observation_space(self) -> Space:
        """The observation space of the environment."""
        pass

    @property
    @abstractmethod
    def action_space(self) -> Space:
        """The action space of the environment."""
        pass

    def reset(self) -> ObsType:
        """Reset the environment and return initial observation."""
        observation = self.get_observation()
        return observation

    @abstractmethod
    def close(self):
        """Clean up environment resources.

        This method should be implemented by subclasses to properly clean up any resources
        like network connections, file handles, or external processes that need to be
        explicitly closed or terminated.
        """
        pass

    def step(self, action: ActType) -> Tuple[ObsType, float, bool, Dict[str, Any]]:
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
    def execute_action(self, action: ActType) -> bool:
        """Execute an action and return success flag."""

    @abstractmethod
    def get_reward(self, action: ActType) -> float:
        """Get the reward for an action.

        Args:
            action (ActType): The action that was executed

        Returns:
            float: The reward for the action
        """

    @abstractmethod
    def get_done(self, action: ActType) -> bool:
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
