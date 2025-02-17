from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, List, NewType

# Define common type aliases for the environment and related modules
Observation = NewType("Observation", str)
Action = NewType("Action", str)
Step = Tuple[Observation, Action]
Trajectory = List[Step]
Mandate = NewType("Mandate", str)


class Env(ABC):
    """Abstract base class for environments"""

    def reset(self) -> Any:
        """Reset the environment and return initial observation"""
        return self._get_observation()

    def close(self):
        """Clean up environment resources"""
        pass

    @abstractmethod
    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict]:
        """
        Execute action and return (observation, reward, done, info)

        Args:
            action (Action): Action to execute

        Returns:
            observation (Observation): Environment observation
            reward (float): Reward from the action
            done (bool): Whether episode has ended
            info (Dict): Additional information
        """
        pass

    @abstractmethod
    def close(self):
        """Clean up environment resources"""
        pass
