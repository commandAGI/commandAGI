from abc import ABC, abstractmethod
from typing import Any, Optional, List
from commandagi_j2.utils.gym2.collector_base import BaseEpisode
from commandagi_j2.utils.gym2.base_env import Mandate
from commandagi_j2.utils.gym2.callbacks import Callback


class BaseEvaluator(ABC):
    """Abstract base class for evaluating agent episodes."""

    def __init__(self, callbacks: Optional[List[Callback]] = None):
        """Initialize the evaluator.
        
        Args:
            callbacks (Optional[List[Callback]]): List of callbacks to register
        """
        self._callbacks = callbacks or []

    @abstractmethod
    def evaluate_episode(self, episode: BaseEpisode, mandate: Mandate) -> Any:
        """Evaluate an episode against a given mandate.

        Args:
            episode (Episode): The episode to evaluate
            mandate (Mandate): The criteria/goals the episode should satisfy

        Returns:
            Any: The evaluation result, format determined by implementation
        """

    @abstractmethod
    def get_metrics(self) -> dict:
        """Get evaluation metrics.

        Returns:
            dict: A dictionary of evaluation metrics
        """

    @property
    def callbacks(self):
        if not hasattr(self, "_callbacks"):
            self._callbacks = []
        return self._callbacks

    def register_callback(self, callback: Callback) -> None:
        """Register a callback for evaluator-specific events."""
        self.callbacks.append(callback)
