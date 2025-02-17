import time
from typing import Optional, Union
from commandagi_j2.utils.gym2.collector_base import BaseCollector, BaseEpisode
from commandagi_j2.utils.gym2.env_base import Env
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.driver_base import BaseDriver
from commandagi_j2.utils.gym2.in_memory_collector import (
    InMemoryEpisode,
    InMemoryDataCollector,
)


class BasicDriver(BaseDriver):
    """Basic implementation of the BaseDriver for running agent-environment interactions.
    
    >>> from commandagi_j2.utils.gym2.basic_driver import BasicDriver
    >>> driver = BasicDriver(None, None)
    >>> isinstance(driver, BaseDriver)
    True
    """

    def __init__(
        self,
        env: Optional[Env],
        agent: Optional[BaseAgent],
        collector: Optional[BaseCollector] = None,
    ):
        """Initialize the basic driver.

        Args:
            env (Optional[Env]): The environment to use
            agent (Optional[BaseAgent]): The agent to use
            collector (Optional[BaseCollector]): The data collector to use, defaults to InMemoryDataCollector
            
        >>> from commandagi_j2.utils.gym2.in_memory_collector import InMemoryDataCollector
        >>> driver = BasicDriver(None, None)
        >>> isinstance(driver.collector, InMemoryDataCollector)
        True
        """
        self.env = env
        self.agent = agent
        self.collector = collector or InMemoryDataCollector()

    def reset(self) -> None:
        """Reset the driver's state including environment, agent and collector.
        
        >>> from commandagi_j2.utils.gym2.env_base import Env
        >>> from commandagi_j2.utils.gym2.base_agent import BaseAgent
        >>> class MockEnv(Env):
        ...     def reset(self): return "obs"
        ...     def step(self, action): pass
        ...     def close(self): pass
        >>> class MockAgent(BaseAgent):
        ...     def reset(self): pass
        ...     def act(self, observation): return "action"
        ...     def update(self, reward): pass
        >>> driver = BasicDriver(MockEnv(), MockAgent())
        >>> driver.reset()
        """
        self.env.reset()
        self.agent.reset()
        self.collector.reset()

    def run_episode(
        self,
        max_steps=100,
        episode_num: Optional[int] = None,
        return_episode: bool = False,
    ) -> Union[float, BaseEpisode]:
        """Run a single episode.

        Args:
            max_steps (int): Maximum number of steps to run
            episode_num (Optional[int]): Episode identifier for data collection
            return_episode (bool): Whether to return the full episode data

        Returns:
            Union[float, BaseEpisode]: Either the total reward or full episode data
            
        >>> from commandagi_j2.utils.gym2.env_base import Env
        >>> from commandagi_j2.utils.gym2.base_agent import BaseAgent
        >>> class MockEnv(Env):
        ...     def reset(self): return "obs"
        ...     def step(self, action): return "next_obs", 1.0, True, {}
        ...     def close(self): pass
        >>> class MockAgent(BaseAgent):
        ...     def reset(self): pass
        ...     def act(self, observation): return "action"
        ...     def update(self, reward): pass
        >>> driver = BasicDriver(MockEnv(), MockAgent())
        >>> reward = driver.run_episode(max_steps=1)
        >>> isinstance(reward, float)
        True
        """
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
