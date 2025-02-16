import time
from typing import Optional, Union
from commandagi_j2.utils.collection import DataCollector, Episode
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.driver_base import BaseDriver
from commandagi_j2.utils.gym2.env_base import Env

class BasicDriver(BaseDriver):
    def __init__(self, 
                 env: Optional[Env], 
                 agent: Optional[BaseAgent],
                 collector: Optional[DataCollector] = None):
        self.env = env
        self.agent = agent
        self.collector = collector or DataCollector()
    
    
    def reset(self) -> None:
        """Reset the driver's state."""
        self.env.reset()
        self.agent.reset()
        self.collector.reset()
    
    def run_episode(self, max_steps=100, episode_num: Optional[int] = None, return_episode: bool = False) -> Union[float, Episode]:
        """Run a single episode"""
        # Reset environment, agent, and collector
        observation = self.env.reset()
        self.agent.reset()
        self.collector.reset()
        
        try:
            for step in range(max_steps):
                # Agent selects action
                action = self.agent.act(observation)
                
                # Environment step
                observation, reward, done, info = self.env.step(action)
                
                # Update agent with reward
                self.agent.update(reward)
                
                # Collect data
                self.collector.add_step(observation, action, reward, info)
                
                # Optional delay
                time.sleep(2)
                
                if done:
                    break
                    
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            # Save episode data if episode number provided
            if episode_num is not None:
                self.collector.save_episode(episode_num)
            self.env.close()
        
        if return_episode:
            return self.collector.current_episode
        else:
            return self.collector.current_episode.total_reward 