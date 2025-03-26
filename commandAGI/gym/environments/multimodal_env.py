from abc import ABC
from typing import Any, Callable, ClassVar, Dict, Generic, TypeVar

from rich.console import Console

from commandAGI.gym.environments.base_env import BaseEnv

console = Console()

ObsT = TypeVar("ObsT")
ActT = TypeVar("ActT")


class MultiModalEnv(BaseEnv[ObsT, ActT], Generic[ObsT, ActT], ABC):
    """Base class for environments with multiple modalities for observations and actions"""

    _LOG_MODALITY_ERRORS: ClassVar[bool] = False

    def __init__(
        self,
        observation_fns: Dict[str, Callable[[], Any]],
        action_fns: Dict[str, Callable[[Any], bool]],
        observation_type: type,
    ):
        self.observation_fns = observation_fns
        self.action_fns = action_fns
        self.observation_type = observation_type

    def get_observation(self) -> ObsT:
        """Get observations from all modalities"""
        observations = {}

        for modality, obs_fn in self.observation_fns.items():
            try:
                observations[modality] = obs_fn()
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"[red]Error getting {modality}:[/] {e}")
                observations[modality] = None

        return self.observation_type(**observations)

    def execute_action(self, action: ActT) -> bool:
        """Execute actions for each modality"""
        success = True

        for modality, action_data in action.items():
            if action_data and modality in self.action_fns:
                try:
                    success = self.action_fns[modality](action_data) and success
                except Exception as e:
                    if self._LOG_MODALITY_ERRORS:
                        console.print(f"[red]Error executing {modality}:[/] {e}")
                    success = False

        return success
