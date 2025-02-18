from typing import List, Dict, Any, Iterator
from dataclasses import dataclass
from pathlib import Path
import json

from pydantic import BaseModel
from commandagi_j2.utils.gym2.base_env import Observation, Action
from commandagi_j2.utils.gym2.base_episode import BaseEpisode, BaseStep


class InMemoryEpisode(BaseEpisode, BaseModel):
    """In-memory storage for episode data."""
    steps: List[BaseStep] = []

    @property
    def num_steps(self) -> int:
        return len(self.steps)

    @property 
    def total_reward(self) -> float:
        return sum(step.reward if step.reward is not None else 0 for step in self.steps)

    def get_step(self, index: int) -> BaseStep:
        return self.steps[index]

    def append_step(
        self,
        observation: Observation,
        action: Action, 
        reward: float|None,
        info: Dict[str, Any]
    ) -> None:
        step = BaseStep(
            observation=observation,
            action=action,
            reward=reward,
            info=info
        )
        self.steps.append(step)

    def update_step(self, index: int, step: BaseStep) -> None:
        self.steps[index] = step

    def remove_step(self, index: int) -> None:
        self.steps.pop(index)

    def iter_steps(self) -> Iterator[BaseStep]:
        return iter(self.steps)

    def save(self, episode_name: str) -> None:
        # Convert episode data to JSON-serializable format
        episode_data = {
            "steps": [step.model_dump_json(indent=2) for step in self.steps]
        }
        
        # Save to file
        path = Path(f"{episode_name}.json")
        parent_dir = path.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True)
        with path.open("w") as f:
            json.dump(episode_data, f, indent=2)
