from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, NewType
from commandagi_j2.utils.gym2.spaces import Space

# Define common type aliases for the environment and related modules
Observation = NewType("Observation", str)
Action = NewType("Action", str)
Step = Tuple[Observation, Action]
Trajectory = List[Step]
Mandate = NewType("Mandate", str)


class Env(ABC):
    """Abstract base class for environments."""

    @property
    @abstractmethod
    def observation_space(self) -> Space:
        """Get the observation space of the environment.

        Returns:
            Space: The observation space
        """

    @property
    @abstractmethod
    def action_space(self) -> Space:
        """Get the action space of the environment.

        Returns:
            Space: The action space
        """

    def reset(self) -> Observation:
        """Reset the environment and return initial observation."""
        observation = self.get_observation()
        return observation

    def close(self):
        """Clean up environment resources."""

    @abstractmethod
    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict]:
        """Execute action and return (observation, reward, done, info).

        Args:
            action (Action): Action to execute

        Returns:
            observation (Observation): Environment observation
            reward (float): Reward from the action
            done (bool): Whether episode has ended
            info (Dict): Additional information
        """
        """Execute an action and return the next observation, reward, done, and info."""
        success = self._execute_action(action)
        observation = self.get_observation()
        reward = self.get_reward(observation, action)
        done = self.get_done(observation, action)
        info = self.get_info(observation, action)
        return observation, reward, done, info

    @abstractmethod
    def get_observation(self) -> Observation:
        """Get the current observation from the environment.

        This method should be implemented by subclasses to return the current state observation.
        """

    @abstractmethod
    def execute_action(self, action: Action) -> Observation:
        """Execute an action and return the observation.

        Args:
            action (Action): The action to execute

        """

    @abstractmethod
    def get_reward(self, action: Action) -> float:
        """Get the reward for an action.

        Args:
            action (Action): The action that was executed

        Returns:
            float: The reward for the action
        """

    @abstractmethod
    def get_done(self, action: Action) -> bool:
        """Get the done flag for an action.

        Returns:
            bool: Whether the episode is done
        """

    def get_info(self) -> Dict:
        """Get the info for an action.

        Returns:
            Dict: Additional information
        """
        return {}

    @abstractmethod
    def close(self):
        """Clean up environment resources."""
