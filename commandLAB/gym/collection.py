from abc import ABC, abstractmethod
import json
import os
import pickle
from typing import Any, Dict, Generic, Iterator, Literal, Tuple, TypeVar

from pydantic import BaseModel

# Define generic type variables
ObsType = TypeVar("ObsType")
ActionType = TypeVar("ActType")


class Step(Generic[ObsType, ActionType], BaseModel):
    observation: ObsType
    action: ActionType
    reward: float
    info: Dict[str, Any]


class Episode(Generic[ObsType, ActionType], ABC):
    """Abstract base class for episodes."""

    @property
    @abstractmethod
    def num_steps(self) -> int:
        """Get the number of steps in the episode."""

    @abstractmethod
    def iter_steps(self) -> Iterator[Step[ObsType, ActionType]]:
        """Iterate over the steps of the episode."""

    @abstractmethod
    def get(self, index: int) -> Step[ObsType, ActionType]:
        """Get a step from the episode at a specific index."""

    @abstractmethod
    def push(self, step: Step[ObsType, ActionType]) -> None:
        """Push a step onto the episode."""

    @abstractmethod
    def insert(self, step: Step[ObsType, ActionType], index: int) -> None:
        """Insert a step into the episode at a specific index."""

    @abstractmethod
    def pop(self) -> Step[ObsType, ActionType]:
        """Pop a step from the episode."""

    @abstractmethod
    def clear(self) -> None:
        """Clear the episode."""

    def __getitem__(self, index: int) -> Step[ObsType, ActionType]:
        """Get a step at the specified index."""
        return self.get(index)

    def __setitem__(self, index: int, step: Step[ObsType, ActionType]) -> None:
        """Set a step at the specified index."""
        if index < 0 or index >= self.num_steps:
            raise IndexError("Episode index out of range")
        self.insert(step, index)
    
    def __iter__(self) -> Iterator[Step[ObsType, ActionType]]:
        """Iterate over the steps of the episode."""
        return self.iter_steps()

    def __len__(self) -> int:
        """Get the number of steps in the episode."""
        return self.num_steps


class InMemoryEpisode(Episode[ObsType, ActionType]):
    """In-memory implementation of an episode."""

    def __init__(self):
        self.steps = []

    @property
    def num_steps(self) -> int:
        """Get the number of steps in the episode."""
        return len(self.steps)

    def iter_steps(self) -> Iterator[Step[ObsType, ActionType]]:
        """Iterate over the steps of the episode."""
        return iter(self.steps)

    def get(self, index: int) -> Step[ObsType, ActionType]:
        """Get a step from the episode at a specific index."""
        return self.steps[index]

    def push(self, step: Step[ObsType, ActionType]) -> None:
        """Push a step onto the episode."""
        self.steps.append(step)

    def insert(self, step: Step[ObsType, ActionType], index: int) -> None:
        """Insert a step into the episode at a specific index."""
        self.steps.insert(index, step)

    def pop(self) -> Step[ObsType, ActionType]:
        """Pop a step from the episode."""
        return self.steps.pop()

    def clear(self) -> None:
        """Clear the episode."""
        self.steps.clear()


class FilesystemSavedEpisode(Episode[ObsType, ActionType]):
    """Filesystem-based implementation of an episode that saves steps to disk."""

    def __init__(self, save_dir: str, mode: Literal["pickle", "json"] = "pickle"):
        """Initialize with directory to save episode data.

        Args:
            save_dir (str): Directory path where episode steps will be saved
            mode (str): Serialization mode - either "pickle" or "json"
        """
        self.save_dir = save_dir
        self.steps = []
        self.mode = mode
        self.extension = ".json" if mode == "json" else ".pkl"
        os.makedirs(save_dir, exist_ok=True)

    @property
    def num_steps(self) -> int:
        """Get the number of steps in the episode."""
        return len(self.steps)

    def iter_steps(self) -> Iterator[Step[ObsType, ActionType]]:
        """Iterate over the steps of the episode."""
        for i in range(len(self.steps)):
            step_path = os.path.join(self.save_dir, f"step_{i+1}{self.extension}")
            yield self.get(i)

    def get(self, index: int) -> Step[ObsType, ActionType]:
        """Get a step from the episode at a specific index."""
        step_path = os.path.join(self.save_dir, f"step_{index+1}{self.extension}")
        match self.mode:
            case "json":
                with open(step_path, "r") as f:
                    content = f.read()
                    return Step.model_validate_json(content)
            case "pickle":
                with open(step_path, "rb") as f:
                    return pickle.load(f)

    def push(self, step: Step[ObsType, ActionType]) -> None:
        """Push a step onto the episode and save to disk."""
        self.insert(step, len(self.steps))

    def insert(self, step: Step[ObsType, ActionType], index: int) -> None:
        """Insert a step into the episode at a specific index."""
        self.steps.insert(index, step)
        # Rename and resave all subsequent steps
        for i in range(index, len(self.steps)):
            step_path = os.path.join(self.save_dir, f"step_{i+1}{self.extension}")
            match self.mode:
                case "json":
                    with open(step_path, "w") as f:
                        json = self.steps[i].model_dump_json()
                        f.write(json)
                case "pickle":
                    with open(step_path, "wb") as f:
                        pickle.dump(self.steps[i], f)
                case _:
                    raise ValueError(f"Invalid mode: {self.mode}")

    def pop(self) -> Step[ObsType, ActionType]:
        """Pop a step from the episode and remove from disk."""
        step = self.steps.pop()
        # Remove last step file
        step_path = os.path.join(
            self.save_dir, f"step_{len(self.steps)+1}{self.extension}"
        )
        if os.path.exists(step_path):
            os.remove(step_path)
        return step

    def clear(self) -> None:
        """Clear the episode and remove all saved files."""
        self.steps.clear()
        # Remove all step files
        for f in os.listdir(self.save_dir):
            if f.startswith("step_") and f.endswith(self.extension):
                os.remove(os.path.join(self.save_dir, f))
