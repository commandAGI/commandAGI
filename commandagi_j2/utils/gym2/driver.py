import time
from typing import Optional
import pyautogui
from commandagi_j2.compute_env import ComputeEnv
from commandagi_j2.simple_computer_agent import SimpleComputerAgent
from commandagi_j2.utils.collection import DataCollector

class Driver:
    def __init__(self, 
                 env: Optional[ComputeEnv] = None, 
                 agent: Optional[SimpleComputerAgent] = None,
                 collector: Optional[DataCollector] = None):
        self.env = env or ComputeEnv()
        self.agent = agent or SimpleComputerAgent()
        self.collector = collector or DataCollector()
    
    def _reset_desktop(self):
        """Minimize all windows using Windows+D"""
        pyautogui.hotkey('win', 'd')
        time.sleep(1)  # Give windows time to minimize
    
    def run_episode(self, max_steps=100, episode_num: Optional[int] = None, return_episode: bool = False):
        """Run a single episode"""
        # Reset desktop state
        self._reset_desktop()
        
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