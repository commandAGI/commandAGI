from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from commandagi_j2.utils.gym2.driver_base import BaseDriver
from commandagi_j2.utils.gym2.evaluator_base import BaseEvaluator


class BaseTrainer(ABC):
    """Abstract base class for training agents.
    
    >>> from commandagi_j2.utils.gym2.trainer_base import BaseTrainer
    >>> issubclass(BaseTrainer, ABC)
    True
    """

    def __init__(
        self,
        driver: Optional[BaseDriver] = None,
        train_evaluators: Optional[List[BaseEvaluator]] = None,
        test_evaluators: Optional[List[BaseEvaluator]] = None,
    ):
        """Initialize the trainer.

        Args:
            driver (Optional[BaseDriver]): The driver to use for training
            train_evaluators (Optional[List[BaseEvaluator]]): Evaluators to use during training
            test_evaluators (Optional[List[BaseEvaluator]]): Evaluators to use during final testing
            
        >>> class MockTrainer(BaseTrainer):
        ...     def train(self, num_episodes=10, max_steps=100): return [1.0]
        >>> trainer = MockTrainer()
        >>> trainer.metrics
        {}
        """
        self.driver = driver
        self.train_evaluators = train_evaluators or []
        self.test_evaluators = test_evaluators or []
        self.metrics: Dict[str, Any] = {}

    @abstractmethod
    def train(self, num_episodes: int = 10, max_steps: int = 100) -> List[float]:
        """Train the agent for multiple episodes.

        Args:
            num_episodes (int): Number of episodes to train for
            max_steps (int): Maximum steps per episode

        Returns:
            List[float]: List of episode rewards
            
        >>> class MockTrainer(BaseTrainer):
        ...     def train(self, num_episodes=10, max_steps=100): return [1.0, 2.0]
        >>> trainer = MockTrainer()
        >>> rewards = trainer.train(num_episodes=2)
        >>> len(rewards)
        2
        >>> rewards[1]
        2.0
        """
        pass

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
            
        >>> from commandagi_j2.utils.gym2.driver_base import BaseDriver
        >>> from commandagi_j2.utils.gym2.collector_base import BaseEpisode
        >>> class MockDriver(BaseDriver):
        ...     def __init__(self): pass
        ...     def reset(self): pass
        ...     def run_episode(self, max_steps=100, episode_num=None, return_episode=False):
        ...         return type('MockEpisode', (BaseEpisode,), {'total_reward': 1.0})()
        >>> class MockEvaluator(BaseEvaluator):
        ...     def evaluate_episode(self, episode, mandate): return {"score": 1.0}
        ...     def get_metrics(self): return {"avg_score": 1.0}
        >>> trainer = BaseTrainer(driver=MockDriver(), test_evaluators=[MockEvaluator()])
        >>> results = trainer.evaluate(num_episodes=1)
        >>> results["average_reward"]
        1.0
        """
        evaluators = evaluators or self.test_evaluators
        episode_rewards = []
        evaluation_results = {}

        for episode in range(num_episodes):
            print(f"Starting evaluation episode {episode + 1}/{num_episodes}")
            episode = self.driver.run_episode(
                max_steps=max_steps, episode_num=f"eval_{episode}", return_episode=True
            )
            episode_rewards.append(episode.total_reward)

            # Run each evaluator on the episode
            for evaluator in evaluators:
                result = evaluator.evaluate_episode(
                    episode, mandate="TODO: Add mandate"
                )  # TODO: Add mandate handling
                metrics = evaluator.get_metrics()
                evaluation_results[f"{evaluator.__class__.__name__}_{episode}"] = {
                    "result": result,
                    "metrics": metrics,
                }

            print(
                f"Evaluation episode {episode + 1} finished with reward: {episode.total_reward}"
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
            
        >>> class MockTrainer(BaseTrainer):
        ...     def train(self, num_episodes=10, max_steps=100): return [1.0]
        >>> trainer = MockTrainer()
        >>> trainer.metrics = {"test_metric": 1.0}
        >>> metrics = trainer.get_metrics()
        >>> metrics["test_metric"]
        1.0
        """
        return self.metrics
