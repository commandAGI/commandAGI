from typing import Generic

from commandAGI_LAB.environments.base_env import BaseEnv
from commandAGI_LAB.environments.computer_env import BaseComputerEnv
from commandAGI_LAB.types import ComputerAction
from commandAGI_LAB.processors.base_processor import ObservationProcessor, ActionProcessor, ModifiedObsType, ModifiedActionType


class ProcessedEnvWrapper(BaseEnv[ModifiedObsType, ModifiedActionType]):
    """
    Wrapper that applies a list of observation and action processors to an environment.
    """
    _env: BaseEnv
    _obs_processors: list[ObservationProcessor]
    _action_processors: list[ActionProcessor]

    def __init__(self, env: BaseEnv, obs_processors: list[ObservationProcessor], action_processors: list[ActionProcessor]):
        self._env = env
        self._obs_processors = obs_processors
        self._action_processors = action_processors

    def get_observation(self) -> ModifiedObsType:
        obs  = self._env.get_observation()
        for obs_processor in self._obs_processors:
            obs = obs_processor.process(obs)
        return obs

    def execute_action(self, action: ModifiedActionType) -> bool:
        for action_processor in self._action_processors:
            action = action_processor.process(action)
        return self._env.execute_action(action)

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            return getattr(self._env, item)

    def __setattr__(self, item, value):
        return setattr(self._env, item, value)

    def __delattr__(self, item):
        return delattr(self._env, item)
