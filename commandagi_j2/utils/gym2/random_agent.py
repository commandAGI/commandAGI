#!/usr/bin/env python3
import random
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.base_env import Action, Observation


class RandomAgent(BaseAgent):
    """A simple agent that takes random actions."""

    def __init__(self, possible_actions):
        """Initialize with a list of possible actions.
        
        Args:
            possible_actions: List of valid actions the agent can take
        """
        self.possible_actions = possible_actions

    def reset(self):
        pass

    def act(self, observation: Observation) -> Action:
        return random.choice(self.possible_actions)

    def update(self, reward: float):
        pass
