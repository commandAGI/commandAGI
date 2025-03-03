from abc import ABC

from commandAGI2.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
from commandAGI2.gym.schema import Episode
from commandAGI2.gym.tasks.base import BaseTask
from commandAGI2.types import ComputerObservation, ComputerAction


class ComputerTaskMixin(BaseTask[ComputerObservation, ComputerAction], ABC):
    env_config: ComputerEnvConfig

    def evaluate(
        self, env: ComputerEnv, episode: Episode[ComputerObservation, ComputerAction]
    ):
        raise NotImplementedError("ComputerTaskMixin does not implement evaluate")
