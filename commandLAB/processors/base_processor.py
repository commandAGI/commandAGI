from abc import ABC, abstractmethod
import functools
from typing import Generic, TypeVar
from commandLAB.environments.base_env import BaseEnv
from commandLAB.types import ComputerObservation, ComputerAction
from commandLAB.utils.collection import ObsType, ActionType


ModifiedObsType = TypeVar("ModifiedObsType", bound=ObsType)
ModifiedActionType = TypeVar("ModifiedActionType", bound=ActionType)


class ObservationProcessor(Generic[ObsType, ModifiedObsType], ABC):
    @abstractmethod
    def process_observation(self, observation: ObsType) -> ModifiedObsType:
        pass

    def wrap_env(self, env: BaseEnv) -> BaseEnv:
        old_get_observation = env.get_observation

        @functools.wraps(old_get_observation)
        def get_observation(self) -> ModifiedObsType:
            obs = old_get_observation()
            return self.process_observation(obs)

        setattr(env, "get_observation", get_observation)
        return env


class ActionProcessor(Generic[ActionType, ModifiedActionType], ABC):
    @abstractmethod
    def process_action(self, action: ModifiedActionType) -> ActionType:
        pass

    def wrap_env(self, env: BaseEnv) -> BaseEnv:
        old_execute_action = env.execute_action

        @functools.wraps(old_execute_action)
        def execute_action(self, action: ModifiedActionType) -> bool:
            action = self.process_action(action)
            return old_execute_action(action)

        setattr(env, "execute_action", execute_action)
        return env
