from abc import ABC, abstractmethod
import time
from typing import Optional

from pydantic import BaseModel
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.environments.computer_env import ComputerAction, ComputerObservation
from commandLAB.agents.base_agent import BaseAgent

class BaseDriver(BaseModel, ABC):
    """Base class for drivers"""

    @abstractmethod
    def run(self, computer: BaseComputer, agent: BaseAgent):
        pass
