#!/usr/bin/env python3
"""
commandAGI CLI

A command-line interface for interacting with commandAGI functionality.

Subcommands:
  run-example     Run one of the example scripts
  run-gym         Run a gym environment with a specified agent
  screenshot      Take a screenshot using a specified computer
  daemon          Start a daemon server for remote control
  grid-overlay    Create a grid overlay on a screenshot to help with positioning
  ocr             Extract text from a screenshot using OCR
  version         Display version information
  hub             Manage agents on the CommandAGI Hub
"""

import os
import sys
import time
from enum import Enum
from typing import List, Optional

import typer

# Import available computers
from commandAGI.computers.base_computer import BaseComputer
from commandAGI.computers.daemon_client_computer import (
    DaemonClientComputer,
    ProvisioningMethod,
)
from commandAGI.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.version import __version__, get_container_version, get_package_version

# Import hub CLI
from commandAGI.agents.hub_cli import app as hub_cli

try:
    from commandAGI.computers.e2b_desktop_computer import E2BDesktopComputer

    e2b_available = True
except ImportError:
    e2b_available = False

# Import gym components if available
try:
    from commandAGI.gym.agents.naive_vision_language_computer_agent import (
        NaiveComputerAgent,
    )
    from commandAGI.gym.agents.react_vision_language_computer_agent import (
        ReactComputerAgent,
    )
    from commandAGI.gym.drivers import SimpleDriver
    from commandAGI.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig

    gym_available = True
except ImportError:
    gym_available = False

# Import processors if available
try:
    from commandAGI.processors.grid_overlay import overlay_grid
    from commandAGI.processors.screen_parser.pytesseract_screen_parser import (
        parse_screenshot,
    )

    processors_available = True
except ImportError:
    processors_available = False

# Import types
from commandAGI.types import (
    ClickAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    MouseButton,
    ShellCommandAction,
    TypeAction,
)

# Create the CLI app
cli = typer.Typer(help="commandAGI CLI")

# Add hub CLI as a subcommand
cli.add_typer(hub_cli, name="hub", help="Manage agents on the CommandAGI Hub")


# Define enums for CLI options
class ComputerType(str, Enum):
    LOCAL_PYNPUT = "local-pynput"
    LOCAL_PYAUTOGUI = "local-pyautogui"
    DAEMON = "daemon"
    E2B = "e2b"


class AgentType(str, Enum):
    NAIVE = "naive"
    REACT = "react"


class ProvisionerType(str, Enum):
    MANUAL = "manual"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


@cli.command()
def version():
    """Display version information for commandAGI."""
    typer.echo(f"commandAGI Version: {__version__}")
    typer.echo(f"Package Version: {get_package_version()}")
    typer.echo(f"Container Version: {get_container_version()}")


@cli.command()
def start_computer(
    computer_type: ComputerType = typer.Option(
        ComputerType.LOCAL_PYNPUT, help="Type of computer to use"
    ),
    computer_args: list[str] = typer.Option([], help="Arguments for the computer"),
):
    """Start a daemon server for remote control."""
    pass


@cli.command()
def start_agent(
    agent_type: AgentType = typer.Option(AgentType.NAIVE, help="Type of agent to use"),
    agent_args: list[str] = typer.Option([], help="Arguments for the agent"),
):
    """Start an agent for remote control."""
    pass


@cli.coommand()
def run_example(
    example_name: str = typer.Option(..., help="Name of the example to run")
):
    """Run an example script."""
    # this is good for testing
    pass


computer_subcli = typer.Typer(help="commandAGI CLI")


@computer_subcli.command()
def start(
    computer_type: ComputerType = typer.Option(
        ComputerType.LOCAL_PYNPUT, help="Type of computer to use"
    ),
    computer_args: list[str] = typer.Option([], help="Arguments for the computer"),
    daemon: bool = typer.Option(False, help="Start a daemon server for remote control"),
):
    """Start a daemon server for remote control."""
    # if in daemon mode, just ensure the daemon is running on the localhost and then dispatch to the computer
    if daemon:
        ...
    else:
        ...


agent_subcli = typer.Typer(help="commandAGI CLI")


@agent_subcli.command()
def start(
    agent_type: AgentType = typer.Option(AgentType.NAIVE, help="Type of agent to use"),
    agent_args: list[str] = typer.Option([], help="Arguments for the agent"),
):
    """Start an agent for remote control."""
    pass


def run_gym(
    computer: ComputerType = typer.Option(
        ComputerType.LOCAL_PYNPUT, help="Type of computer to use"
    ),
    agent: AgentType = typer.Option(AgentType.NAIVE, help="Type of agent to use"),
    model: str = typer.Option(
        "gpt-4-vision-preview", help="Model to use for the agent"
    ),
    steps: int = typer.Option(10, help="Maximum number of steps to run"),
):
    """Run a gym environment with a specified agent."""
    if not gym_available:
        typer.echo(
            "Error: Gym module not available. Install with: pip install commandagi[gym]"
        )
        return

    typer.echo(f"Running gym with {computer} computer and {agent} agent")
    typer.echo(f"Using model: {model}")
    typer.echo(f"Maximum steps: {steps}")
    typer.echo("Starting in 3 seconds...")
    time.sleep(3)

    try:
        # Configure the environment
        config = ComputerEnvConfig(
            computer_cls_name=(
                f"Local{computer.value.split('-')[1].capitalize()}Computer"
                if computer.value.startswith("local")
                else "DaemonClientComputer"
            ),
            computer_cls_kwargs={},
        )

        # Create the environment
        env = ComputerEnv(config)

        # Create the agent
        if agent == AgentType.NAIVE:
            agent_instance = NaiveComputerAgent(
                chat_model_options={
                    "model_provider": "openai",
                    "model": model,
                }
            )
        elif agent == AgentType.REACT:
            agent_instance = ReactComputerAgent(model=model, device="cpu")

        # Create a driver
        driver = SimpleDriver(env=env, agent=agent_instance)

        # Collect an episode
        episode = driver.collect_episode()

        # Print episode statistics
        typer.echo("\nEpisode collection complete!")
        typer.echo(f"Episode length: {episode.num_steps} steps")
        typer.echo(f"Total reward: {sum(step.reward for step in episode)}")

        # Print the actions taken
        typer.echo("\nActions taken:")
        for i, step in enumerate(episode):
            typer.echo(f"Step {i + 1}: {step.action}")
            typer.echo(f"  Reward: {step.reward}")

    except KeyboardInterrupt:
        typer.echo("\nEpisode collection interrupted by user.")
    except Exception as e:
        typer.echo(f"\nError: {e}")
    finally:
        if "driver" in locals():
            driver.close()
            typer.echo("Resources cleaned up.")


if __name__ == "__main__":
    cli()
