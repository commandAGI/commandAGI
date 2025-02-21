from abc import ABC, abstractmethod

from pydantic import BaseModel

from commandAGI_LAB.processors.base_processor import ObservationProcessor
from commandAGI_LAB.types import ComputerObservation
from commandAGI_LAB.environments.computer_env import ComputerEnv

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
