"""
Gym framework for commandAGI2.

This package contains the gym framework for training and evaluating agents that control computers.
"""

# Import core components
from commandAGI2.gym.environments.base_env import BaseEnv
from commandAGI2.gym.agents.base_agent import BaseAgent
from commandAGI2.gym.drivers import (
    BaseDriver,
    SimpleDriver,
    ThreadedDriver,
    MultiprocessDriver,
)
from commandAGI2.gym.trainer import (
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
