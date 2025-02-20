#!/usr/bin/env python3
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.env_base import Action, Env, Observation


class RandomAgent(BaseAgent):
    """A random agent that takes actions sampled from the environment's action space."""

    def __init__(self, env: Env):
        """
        Initialize the agent with the environment.

        Args:
            env (Env): An environment instance.
                It is expected that the environment has an `action_space` attribute
                that implements the Space interface (with a `sample` method).
        """
        self.env = env
        # Ensure that the environment provides an action space.
        self.action_space = getattr(env, "action_space", None)
        if self.action_space is None:
            raise ValueError(
                "The provided environment has no attribute 'action_space'."
            )

    def reset(self):
        """Reset internal states (if any)."""
        pass

    def act(self, observation: Observation) -> Action:
        """
        Choose an action by sampling from the environment's action space.

        Args:
            observation (Observation): The current observation from the environment.

        Returns:
            Action: An action sampled from the environment's action space.
        """
        return self.action_space.sample()

    def update(self, reward: float):
        """Update the agent's state based on the received reward."""
        pass
