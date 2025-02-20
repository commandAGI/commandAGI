from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from commandLAB.utils.gym2.callbacks import Callback
from commandLAB.utils.gym2.driver_base import BaseDriver
from commandLAB.utils.gym2.evaluator_base import BaseEvaluator


class BaseTrainer(ABC):
    """Abstract base class for training agents."""

    def __init__(
        self,
        driver: Optional[BaseDriver] = None,
        train_evaluators: Optional[List[BaseEvaluator]] = None,
        test_evaluators: Optional[List[BaseEvaluator]] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        """Initialize the trainer.

        Args:
            driver (Optional[BaseDriver]): The driver to use for training
            train_evaluators (Optional[List[BaseEvaluator]]): Evaluators to use during training
            test_evaluators (Optional[List[BaseEvaluator]]): Evaluators to use during final testing
            callbacks (Optional[List[Callback]]): List of callbacks to register
        """
        self.driver = driver
        self.train_evaluators = train_evaluators or []
        self.test_evaluators = test_evaluators or []
        self.metrics: Dict[str, Any] = {}
        self.callbacks = callbacks or []

    @abstractmethod
    def train(self, num_episodes: int = 10, max_steps: int = 100) -> List[float]:
        """Train the agent for multiple episodes.

        Args:
            num_episodes (int): Number of episodes to train for
            max_steps (int): Maximum steps per episode

        Returns:
            List[float]: List of episode rewards
        """

    def evaluate(
        self,
        num_episodes: int = 5,
        max_steps: int = 100,
        evaluators: Optional[List[BaseEvaluator]] = None,
    ) -> Dict[str, Any]:
        """Evaluate the agent's performance using the specified evaluators.

        Args:
            num_episodes (int): Number of episodes to evaluate on
            max_steps (int): Maximum steps per episode
            evaluators (Optional[List[BaseEvaluator]]): Evaluators to use, defaults to test_evaluators

        Returns:
            Dict[str, Any]: Evaluation metrics from all evaluators
        """
        evaluators = evaluators or self.test_evaluators
        episode_rewards = []
        evaluation_results = {}

        for i in range(num_episodes):
            print(f"Starting evaluation episode {i + 1}/{num_episodes}")
            episode = self.driver.run_episode(
                max_steps=max_steps, episode_name=f"eval_{i}", return_episode=True
            )
            episode_rewards.append(episode.total_reward)

            # Run each evaluator on the episode
            for evaluator in evaluators:
                result = evaluator.evaluate_episode(
                    episode, mandate="TODO: Add mandate"
                )  # TODO: Add mandate handling
                metrics = evaluator.get_metrics()
                evaluation_results[f"{evaluator.__class__.__name__}_eval_{i}"] = {
                    "result": result,
                    "metrics": metrics,
                }

            print(
                f"Evaluation episode {i + 1} finished with reward: {episode.total_reward}"
            )

        avg_reward = sum(episode_rewards) / len(episode_rewards)
        print(f"Average evaluation reward: {avg_reward}")

        evaluation_results["episode_rewards"] = episode_rewards
        evaluation_results["average_reward"] = avg_reward

        self.metrics.update(evaluation_results)
        return evaluation_results

    def get_metrics(self) -> Dict[str, Any]:
        """Get all training and evaluation metrics.

        Returns:
            Dict[str, Any]: A dictionary containing all metrics
        """
        return self.metrics

    def register_callback(self, callback: Callback) -> None:
        """Register a callback for trainer-specific events."""
        self.callbacks.append(callback)
