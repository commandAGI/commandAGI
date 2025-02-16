from typing import List, Optional
from commandagi_j2.utils.basic_driver import BasicDriver
from commandagi_j2.utils.gym2.trainer_base import BaseTrainer
from commandagi_j2.utils.gym2.evaluator_base import BaseEvaluator


class Trainer(BaseTrainer):
    def __init__(
        self,
        driver: Optional[BasicDriver],
        train_evaluators: Optional[List[BaseEvaluator]] = None,
        test_evaluators: Optional[List[BaseEvaluator]] = None,
    ):
        super().__init__(
            driver=driver,
            train_evaluators=train_evaluators,
            test_evaluators=test_evaluators,
        )

    def train(self, num_episodes: int = 10, max_steps: int = 100) -> List[float]:
        """Train the agent for multiple episodes"""
        episode_rewards = []

        for episode in range(num_episodes):
            print(f"Starting episode {episode + 1}/{num_episodes}")
            reward = self.driver.run_episode(max_steps=max_steps, episode_num=episode)
            episode_rewards.append(reward)
            print(f"Episode {episode + 1} finished with reward: {reward}")

            # Run training evaluators if any
            if self.train_evaluators:
                self.evaluate(
                    num_episodes=1,
                    max_steps=max_steps,
                    evaluators=self.train_evaluators,
                )

        return episode_rewards

    def evaluate(self, num_episodes: int = 5, max_steps: int = 100) -> List[float]:
        """Evaluate the agent's performance"""
        episode_rewards = []

        for episode in range(num_episodes):
            print(f"Starting evaluation episode {episode + 1}/{num_episodes}")
            reward = self.driver.run_episode(
                max_steps=max_steps, episode_num=f"eval_{episode}"
            )
            episode_rewards.append(reward)
            print(f"Evaluation episode {episode + 1} finished with reward: {reward}")

        avg_reward = sum(episode_rewards) / len(episode_rewards)
        print(f"Average evaluation reward: {avg_reward}")
        return episode_rewards
