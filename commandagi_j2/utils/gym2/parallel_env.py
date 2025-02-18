from typing import Dict, Callable, Optional, Tuple, TypeVar, Generic, Any
from .base_env import Env
from .spaces import Space, DictSpace

ObsType = TypeVar('ObsType')
ActType = TypeVar('ActType')
InfoType = TypeVar('InfoType', bound=Dict[str, Any])

class ParallelEnv(Env[Dict[str, ObsType], Dict[str, ActType], Dict[str, InfoType]], Generic[ObsType, ActType, InfoType]):
    """Runs multiple environments in parallel using dictionaries."""
    
    def __init__(self, env_factory: Callable[[], Env[ObsType, ActType, InfoType]], num_envs: int, reset_when_done: bool = True):
        """Initialize parallel environments.
        
        Args:
            env_factory: Function that creates a new environment instance
            num_envs: Number of parallel environments to create
            reset_when_done: Whether to automatically reset done environments
        """
        self.env_factory = env_factory  # Store the factory for later use
        self.envs: Dict[str, Env[ObsType, ActType, InfoType]] = {
            str(i): env_factory() for i in range(num_envs)
        }
        self.reset_when_done = reset_when_done
        self.active_envs = list(self.envs.keys())
        self.next_env_id = num_envs

        # Get base spaces from first env
        self._base_obs_space = next(iter(self.envs.values())).observation_space
        self._base_act_space = next(iter(self.envs.values())).action_space
    
    def add_env(self) -> str:
        """Add a new environment and return its ID."""
        new_id = str(self.next_env_id)
        self.envs[new_id] = self.env_factory()
        self.next_env_id += 1
        self.active_envs.append(new_id)
        return new_id
    
    def reset(self) -> Dict[str, ObsType]:
        """Reset all environments.
        
        Returns:
            Dictionary of initial observations from all environments
        """
        self.active_envs = list(self.envs.keys())
        return {env_id: env.reset() for env_id, env in self.envs.items()}
    
    def step(self, action: Dict[str, ActType]) -> Tuple[Dict[str, ObsType] | float | bool | Dict[str, InfoType]]:
        return super().step(action)

    @property
    def observation_space(self) -> Space[Dict[str, ObsType]]:
        """Get the observation space for currently active environments."""
        return DictSpace(spaces={
            env_id: self._base_obs_space 
            for env_id in self.active_envs
        })

    @property 
    def action_space(self) -> Space[Dict[str, ActType]]:
        """Get the action space for currently active environments."""
        return DictSpace(spaces={
            env_id: self._base_act_space 
            for env_id in self.active_envs
        })

    def get_observation(self) -> Dict[str, ObsType]:
        """Get observations from active environments only."""
        return {env_id: self.envs[env_id].get_observation() 
                for env_id in self.active_envs}

    def execute_action(self, action: Dict[str, ActType]) -> bool:
        """Execute actions in active environments only."""
        if set(action.keys()) != set(self.active_envs):
            raise ValueError(f"Action keys {action.keys()} don't match active envs {self.active_envs}")
        return all(self.envs[env_id].execute_action(action[env_id]) 
                  for env_id in self.active_envs)

    def get_reward(self, action: Dict[str, ActType]) -> float:
        """Get rewards from active environments only."""
        if set(action.keys()) != set(self.active_envs):
            raise ValueError(f"Action keys {action.keys()} don't match active envs {self.active_envs}")
        return sum(self.envs[env_id].get_reward(action[env_id]) 
                  for env_id in self.active_envs)

    def get_done(self, action: Dict[str, ActType]) -> bool:
        """Get done flags from active environments only."""
        if set(action.keys()) != set(self.active_envs):
            raise ValueError(f"Action keys {action.keys()} don't match active envs {self.active_envs}")
        return all(self.envs[env_id].get_done(action[env_id]) 
                  for env_id in self.active_envs)

    def get_info(self) -> Dict[str, InfoType]:
        """Get info from active environments only."""
        return {env_id: self.envs[env_id].get_info() 
                for env_id in self.active_envs}
    
    def close(self):
        """Close all environments."""
        for env in self.envs.values():
            env.close()
