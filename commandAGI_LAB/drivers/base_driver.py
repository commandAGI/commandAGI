from abc import ABC, abstractmethod
import time
from typing import Optional

from pydantic import BaseModel
from commandAGI_LAB.computers.base_computer import BaseComputer
from commandAGI_LAB.environments.computer_env import ComputerAction, ComputerObservation
from commandAGI_LAB.agents.base_agent import BaseAgent

class BaseDriver(BaseModel, ABC):
    """Base class for drivers"""

    @abstractmethod
    def run(self, computer: BaseComputer, agent: BaseAgent):
        pass
