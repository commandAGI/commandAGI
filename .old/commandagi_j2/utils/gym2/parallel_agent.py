from typing import Dict, List, Callable, Any, TypeVar, Generic
from .base_agent import BaseAgent
from .base_env import Observation

ObsType = TypeVar('ObsType')
ActType = TypeVar('ActType')

class ParallelAgent(BaseAgent[Dict[str, ObsType], Dict[str, ActType]], Generic[ObsType, ActType]):
    """Manages multiple agents in parallel, with each agent identified by a string key."""
    
    def __init__(self, agent_factory: Callable[[], BaseAgent[ObsType, ActType]], agent_ids: List[str]):
        """Initialize parallel agents.
        
        Args:
            agent_factory: Function that creates a new agent instance
            agent_ids: List of string identifiers for the agents
        """
        self.agent_factory = agent_factory  # Store the factory for later use
        self.agents: Dict[str, BaseAgent[ObsType, ActType]] = {
            agent_id: agent_factory() 
            for agent_id in agent_ids
        }
        self.next_agent_id = max(map(int, agent_ids)) + 1 if agent_ids else 0
    
    def add_agent(self) -> str:
        """Add a new agent and return its ID."""
        new_id = str(self.next_agent_id)
        self.agents[new_id] = self.agent_factory()
        self.next_agent_id += 1
        return new_id
    
    def reset(self) -> None:
        """Reset all agents."""
        for agent in self.agents.values():
            agent.reset()
    
    def act(self, observations: Dict[str, ObsType]) -> Dict[str, ActType]:
        """Get actions from all agents based on their observations.
        
        Args:
            observations: Dictionary of observations, keyed by agent ID
            
        Returns:
            Dictionary of actions chosen by each agent
        """
        if set(observations.keys()) != set(self.agents.keys()):
            raise ValueError(f"Observation keys {observations.keys()} don't match agent keys {self.agents.keys()}")
            
        return {
            agent_id: self.agents[agent_id].act(obs)
            for agent_id, obs in observations.items()
        }
    
    def update(self, rewards: Dict[str, float]) -> None:
        """Update all agents with their respective rewards.
        
        Args:
            rewards: Dictionary of rewards, keyed by agent ID
        """
        if set(rewards.keys()) != set(self.agents.keys()):
            raise ValueError(f"Reward keys {rewards.keys()} don't match agent keys {self.agents.keys()}")
            
        for agent_id, reward in rewards.items():
            self.agents[agent_id].update(reward)
    
    def get_agent(self, agent_id: str) -> BaseAgent[ObsType, ActType]:
        """Get a specific agent by ID.
        
        Args:
            agent_id: The identifier of the agent to retrieve
            
        Returns:
            The requested agent instance
        """
        if agent_id not in self.agents:
            raise KeyError(f"No agent found with ID: {agent_id}")
        return self.agents[agent_id] 