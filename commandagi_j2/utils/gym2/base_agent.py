from abc import ABC, abstractmethod
from commandagi_j2.utils.gym2.env_base import Observation


class BaseAgent(ABC):
    """Base class for all agents in the environment.

    >>> from commandagi_j2.utils.gym2.base_agent import BaseAgent
    >>> issubclass(BaseAgent, ABC)
    True
    """

    @abstractmethod
    def reset(self) -> None:
        """Reset the agent's internal state.

        >>> class MockAgent(BaseAgent):
        ...     def reset(self): pass
        ...     def act(self, observation): pass
        ...     def update(self, reward): pass
        >>> agent = MockAgent()
        >>> agent.reset()
        """
        pass

    @abstractmethod
    def act(self, observation: Observation) -> str:
        """Given an observation, determine the next action.

        Args:
            observation (Observation): The current environment observation.

        Returns:
            str: The chosen action as a string.

        >>> class MockAgent(BaseAgent):
        ...     def reset(self): pass
        ...     def act(self, observation): return "test_action"
        ...     def update(self, reward): pass
        >>> agent = MockAgent()
        >>> agent.act("test_observation")
        'test_action'
        """
        pass

    @abstractmethod
    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the received reward.

        Args:
            reward (float): The reward obtained from the last action.

        >>> class MockAgent(BaseAgent):
        ...     def reset(self): pass
        ...     def act(self, observation): pass
        ...     def update(self, reward): pass
        >>> agent = MockAgent()
        >>> agent.update(1.0)
        """
        pass
