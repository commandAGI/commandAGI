from abc import ABC, abstractmethod

from pydantic import BaseModel

from commandLAB.processors.base_processor import ObservationProcessor
from commandLAB.types import ComputerObservation
from commandLAB.environments.computer_env import ComputerEnv

class ParsedElement(BaseModel):
    text: str
    bounding_box: list[int]

class ParsedScreenshot(BaseModel):
    elements: list[ParsedElement]

class ComputerObservationWithParsedScreenshot(ComputerObservation):
    parsed_screenshot: ParsedScreenshot

class BaseScreenParser(ObservationProcessor[ComputerObservation, ComputerObservationWithParsedScreenshot], ABC):
    @abstractmethod
    def process_observation(self, observation: ComputerObservation) -> ComputerObservationWithParsedScreenshot:
        return ComputerObservationWithParsedScreenshot(
            parsed_screenshot=self.parse(observation.screenshot),
            **observation.model_dump()
        )
