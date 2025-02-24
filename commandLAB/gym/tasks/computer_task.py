from abc import ABC

from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
from commandLAB.gym.schema import Episode
from commandLAB.gym.tasks.base import BaseTask
from commandLAB.types import ComputerObservation, ComputerAction


class ComputerTaskMixin(BaseTask[ComputerObservation, ComputerAction], ABC):
    env_config: ComputerEnvConfig

    def evaluate(
        self, env: ComputerEnv, episode: Episode[ComputerObservation, ComputerAction]
    ):
        raise NotImplementedError("ComputerTaskMixin does not implement evaluate")
