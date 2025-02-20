from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

from commandAGI_LAB.utils.gym2.base_episode import BaseEpisode
from commandAGI_LAB.utils.gym2.callbacks import Callback

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")


class BaseEvaluator(Generic[ObsType, ActType], ABC):
    """Abstract base class for evaluating agent episodes."""

    callbacks: List[Callback]

    def __init__(self, callbacks: Optional[List[Callback]] = None):
        """Initialize the evaluator.

        Args:
            callbacks (Optional[List[Callback]]): List of callbacks to register
        """
        self.callbacks = callbacks or []

    @abstractmethod
    def evaluate_episode(
        self, episode: BaseEpisode[ObsType, ActType], mandate: str
    ) -> Any:
        """Evaluate an episode against a given mandate.

        Args:
            episode (Episode): The episode to evaluate
            mandate (str): The criteria/goals the episode should satisfy

        Returns:
            Any: The evaluation result, format determined by implementation
        """

    @abstractmethod
    def get_metrics(self) -> dict:
        """Get evaluation metrics.

        Returns:
            dict: A dictionary of evaluation metrics
        """

    def register_callback(self, callback: Callback) -> None:
        """Register a callback for evaluator-specific events."""
        self.callbacks.append(callback)
