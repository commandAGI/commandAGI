from abc import ABC, abstractmethod
from typing import Any
from commandagi_j2.utils.gym2.env_base import Mandate
from commandagi_j2.utils.collection import Episode


class BaseEvaluator(ABC):
    """Abstract base class for evaluating agent episodes."""

    @abstractmethod
    def evaluate_episode(self, episode: Episode, mandate: Mandate) -> Any:
        """
        Evaluate an episode against a given mandate.

        Args:
            episode (Episode): The episode to evaluate
            mandate (Mandate): The criteria/goals the episode should satisfy

        Returns:
            Any: The evaluation result, format determined by implementation
        """
        pass

    @abstractmethod
    def get_metrics(self) -> dict:
        """
        Get evaluation metrics.

        Returns:
            dict: A dictionary of evaluation metrics
        """
        pass
