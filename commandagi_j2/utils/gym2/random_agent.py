#!/usr/bin/env python3
import random
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.base_env import Action, Env, Observation


class RandomAgent(BaseAgent):

    env: Env

    def reset(self):
        pass

    def act(self, observation: Observation) -> Action:
        return self.env.action_space.sample()

    def update(self, reward: float):
        pass
