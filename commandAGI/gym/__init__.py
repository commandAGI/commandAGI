"""
Gym framework for commandAGI.

This package contains the gym framework for training and evaluating agents that control computers.
"""

# Import core components
from commandAGI.gym.environments.base_env import BaseEnv
from commandAGI.gym.agents.base_agent import BaseAgent
from commandAGI.gym.drivers import (
    BaseDriver,
    SimpleDriver,
    ThreadedDriver,
    MultiprocessDriver,
)
from commandAGI.gym.trainer import (
    BaseTrainer,
    OnlineTrainer,
    OfflineTrainer,
    BatchTrainer,
)

__all__ = [
    "BaseEnv",
    "BaseAgent",
    "BaseDriver",
    "SimpleDriver",
    "ThreadedDriver",
    "MultiprocessDriver",
    "BaseTrainer",
    "OnlineTrainer",
    "OfflineTrainer",
    "BatchTrainer",
]
