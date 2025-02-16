from typing import Optional
from commandagi_j2.utils.gym2.driver import Driver

class Trainer:
    def __init__(self, driver: Optional[Driver] = None):
        self.driver = driver or Driver()
        
    def train(self, num_episodes: int = 10, max_steps: int = 100):
        """Train the agent for multiple episodes"""
        episode_rewards = []
        
        for episode in range(num_episodes):
            print(f"Starting episode {episode + 1}/{num_episodes}")
            reward = self.driver.run_episode(
                max_steps=max_steps,
                episode_num=episode
            )
            episode_rewards.append(reward)
            print(f"Episode {episode + 1} finished with reward: {reward}")
            
        return episode_rewards
    
    def evaluate(self, num_episodes: int = 5, max_steps: int = 100):
        """Evaluate the agent's performance"""
        episode_rewards = []
        
        for episode in range(num_episodes):
            print(f"Starting evaluation episode {episode + 1}/{num_episodes}")
            reward = self.driver.run_episode(
                max_steps=max_steps,
                episode_num=f"eval_{episode}"
            )
            episode_rewards.append(reward)
            print(f"Evaluation episode {episode + 1} finished with reward: {reward}")
            
        avg_reward = sum(episode_rewards) / len(episode_rewards)
        print(f"Average evaluation reward: {avg_reward}")
        return episode_rewards 