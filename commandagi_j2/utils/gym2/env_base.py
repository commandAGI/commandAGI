from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, List, NewType

# Define common type aliases for the environment and related modules
Observation = NewType("Observation", str)
Action = NewType("Action", str)
Step = Tuple[Observation, Action]
Trajectory = List[Step]
Mandate = NewType("Mandate", str)


class Env(ABC):
    """Abstract base class for environments.

    >>> from commandagi_j2.utils.gym2.env_base import Env
    >>> issubclass(Env, ABC)
    True
    """

    def reset(self) -> Any:
        """Reset the environment and return initial observation.

        >>> class MockEnv(Env):
        ...     def _get_observation(self): return "initial_obs"
        ...     def step(self, action): pass
        ...     def close(self): pass
        >>> env = MockEnv()
        >>> env.reset()
        'initial_obs'
        """
        return self._get_observation()

    def close(self):
        """Clean up environment resources.

        >>> class MockEnv(Env):
        ...     def _get_observation(self): return "obs"
        ...     def step(self, action): pass
        ...     def close(self): pass
        >>> env = MockEnv()
        >>> env.close()
        """
        pass

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

        >>> class MockEnv(Env):
        ...     def _get_observation(self): return "obs"
        ...     def step(self, action): return ("next_obs", 1.0, False, {})
        ...     def close(self): pass
        >>> env = MockEnv()
        >>> obs, reward, done, info = env.step("test_action")
        >>> obs
        'next_obs'
        >>> reward
        1.0
        >>> done
        False
        >>> info
        {}
        """
        pass

    @abstractmethod
    def close(self):
        """Clean up environment resources.

        >>> class MockEnv(Env):
        ...     def _get_observation(self): return "obs"
        ...     def step(self, action): pass
        ...     def close(self): pass
        >>> env = MockEnv()
        >>> env.close()
        """
        pass
