#!/usr/bin/env python3
import random
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.env_base import Action, Observation


class RandomAgent(BaseAgent):
    def __init__(self):
        self.total_reward = 0.0

    def reset(self):
        self.total_reward = 0.0

    def act(self, observation: Observation) -> Action:
        # Randomly choose to click at a random position or type random text
        if random.random() < 0.5:
            x = random.randint(0, 800)
            y = random.randint(0, 600)
            return f"click {x},{y}"
        else:
            random_text = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
            return f"type {random_text}"

    def update(self, reward: float):
        self.total_reward += reward 