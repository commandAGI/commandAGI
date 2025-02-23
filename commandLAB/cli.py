#!/usr/bin/env python3
"""
CLI for testing, evaluating, and re-watching evaluation episodes
with various agent/environment combinations.

Subcommands:
  test     Run one or more test episodes with a chosen agent and environment.
  evaluate Run evaluation episodes using an evaluator (e.g. InstructionFollowingEvaluator).
  replay   Replay a saved episode by cycling through its observation screenshots.
"""

import argparse
import json
import os
import time

import typer

from commandLAB.agents.simple_vision_language_computer_agent import (
    SimpleComputerAgent,
)

# Mapping from string names to classes so that we can dynamically select them.
AGENTS = {
    "simple": SimpleComputerAgent,
    # add more agents if you implement them
}

COMPUTERS = {
    "docker": VNCDockerComputerEnv,
    "e2b": E2BDesktopEnv,
    "local": LocalPynputComputeEnv,
    # add other computers as needed
}

EVALUATORS = {
    "instruction_following": InstructionFollowingEvaluator,
    # add other evaluators as needed
}

TASKS = {
    "generate_text": GenerateTextTask,
}

app = typer.Typer()


@app.command()
def test(
    computer: str,
    # more computer args
    agent: str,
    # more agent args
    task: str,
    # more task args
    num_episodes: int = 1,
    max_steps: int = 100,
    # more driver args
    train_epochs: int = 1,
    # more train args
):
    """
    Test an agent in a given environment.
    """
    print(f"Testing {agent} in {computer} for {num_episodes} episodes")


if __name__ == "__main__":
    main()
