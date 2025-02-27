#!/usr/bin/env python3
"""
CommandLAB CLI

A command-line interface for interacting with CommandLAB functionality.

Subcommands:
  run-example     Run one of the example scripts
  run-gym         Run a gym environment with a specified agent
  screenshot      Take a screenshot using a specified computer
  daemon          Start a daemon server for remote control
  grid-overlay    Create a grid overlay on a screenshot to help with positioning
  ocr             Extract text from a screenshot using OCR
  version         Display version information
"""

import os
import sys
import time
from typing import Optional, List
import typer
from enum import Enum

from commandLAB.version import __version__, get_package_version, get_container_version

# Import available computers
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
try:
    from commandLAB.computers.e2b_desktop_computer import E2BDesktopComputer
    e2b_available = True
except ImportError:
    e2b_available = False

# Import gym components if available
try:
    from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
    from commandLAB.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent
    from commandLAB.gym.agents.react_vision_language_computer_agent import ReactComputerAgent
    from commandLAB.gym.drivers import SimpleDriver
    gym_available = True
except ImportError:
    gym_available = False

# Import processors if available
try:
    from commandLAB.processors.grid_overlay import overlay_grid
    from commandLAB.processors.screen_parser.pytesseract_screen_parser import parse_screenshot
    processors_available = True
except ImportError:
    processors_available = False

# Import types
from commandLAB.types import (
    ShellCommandAction,
    TypeAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    ClickAction,
    MouseButton,
)

# Create the CLI app
cli = typer.Typer(help="CommandLAB CLI")

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
    """Display version information for CommandLAB."""
    typer.echo(f"CommandLAB Version: {__version__}")
    typer.echo(f"Package Version: {get_package_version()}")
    typer.echo(f"Container Version: {get_container_version()}")

@cli.command()
def screenshot(
    computer: ComputerType = typer.Option(ComputerType.LOCAL_PYNPUT, help="Type of computer to use"),
    output: str = typer.Option("screenshot.png", help="Output file path"),
    delay: float = typer.Option(3.0, help="Delay in seconds before taking screenshot"),
):
    """Take a screenshot using the specified computer."""
    import base64
    from PIL import Image
    import io
    
    typer.echo(f"Taking screenshot in {delay} seconds...")
    time.sleep(delay)
    
    try:
        # Create the computer instance
        if computer == ComputerType.LOCAL_PYNPUT:
            computer_instance = LocalPynputComputer()
        elif computer == ComputerType.LOCAL_PYAUTOGUI:
            computer_instance = LocalPyAutoGUIComputer()
        elif computer == ComputerType.DAEMON:
            computer_instance = DaemonClientComputer(provisioning_method=ProvisioningMethod.MANUAL)
        elif computer == ComputerType.E2B and e2b_available:
            computer_instance = E2BDesktopComputer()
        else:
            typer.echo(f"Error: Computer type {computer} is not available")
            return
        
        # Take the screenshot
        screenshot = computer_instance.get_screenshot()
        
        # Convert base64 to image
        img_data = base64.b64decode(screenshot.screenshot)
        img = Image.open(io.BytesIO(img_data))
        
        # Save the image
        img.save(output)
        typer.echo(f"Screenshot saved to {output}")
        typer.echo(f"Image size: {img.width}x{img.height} pixels")
        
    except Exception as e:
        typer.echo(f"Error: {e}")
    finally:
        if 'computer_instance' in locals():
            computer_instance.close()
            typer.echo("Computer resources cleaned up.")

@cli.command()
def grid_overlay(
    input_file: str = typer.Argument(..., help="Input screenshot file"),
    output_file: str = typer.Option(None, help="Output file path (defaults to input_grid.png)"),
    grid_size: int = typer.Option(100, help="Grid cell size in pixels"),
):
    """Create a grid overlay on a screenshot to help with positioning."""
    if not processors_available:
        typer.echo("Error: Processors module not available. Install with: pip install commandlab[processors]")
        return
    
    try:
        from PIL import Image
        
        # Set default output file if not provided
        if output_file is None:
            name, ext = os.path.splitext(input_file)
            output_file = f"{name}_grid{ext}"
        
        # Open the image
        img = Image.open(input_file)
        
        # Apply grid overlay
        grid_img = overlay_grid(img, grid_px_size=grid_size)
        
        # Save the grid image
        grid_img.save(output_file)
        
        typer.echo(f"Grid overlay image saved to {output_file}")
        typer.echo(f"Image size: {grid_img.width}x{grid_img.height} pixels")
        
    except Exception as e:
        typer.echo(f"Error: {e}")

@cli.command()
def ocr(
    input_file: str = typer.Argument(..., help="Input screenshot file"),
    output_file: str = typer.Option(None, help="Output text file path (defaults to input.txt)"),
):
    """Extract text from a screenshot using OCR."""
    if not processors_available:
        typer.echo("Error: Processors module not available. Install with: pip install commandlab[processors,pytesseract]")
        return
    
    try:
        import base64
        from PIL import Image
        
        # Set default output file if not provided
        if output_file is None:
            name, ext = os.path.splitext(input_file)
            output_file = f"{name}.txt"
        
        # Open the image
        img = Image.open(input_file)
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Parse the screenshot
        parsed_screenshot = parse_screenshot(b64_screenshot)
        
        # Save the extracted text
        with open(output_file, "w") as f:
            for element in parsed_screenshot.elements:
                f.write(f"{element.text}\n")
        
        typer.echo(f"Extracted {len(parsed_screenshot.elements)} text elements")
        typer.echo(f"Text saved to {output_file}")
        
    except Exception as e:
        typer.echo(f"Error: {e}")

@cli.command()
def daemon(
    port: int = typer.Option(8000, help="Port to run the daemon on"),
    backend: str = typer.Option("pynput", help="Backend to use (pynput or pyautogui)"),
):
    """Start a daemon server for remote control."""
    try:
        from commandLAB.daemon.cli import start
        typer.echo(f"Starting daemon on port {port} with backend {backend}...")
        start(port=port, backend=backend)
    except ImportError:
        typer.echo("Error: Daemon module not available. Install with: pip install commandlab[daemon]")
    except Exception as e:
        typer.echo(f"Error: {e}")

@cli.command()
def run_example(
    example: str = typer.Argument(..., help="Example file to run (e.g., 1_getting_started.py)"),
):
    """Run one of the example scripts."""
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
    example_path = os.path.join(examples_dir, example)
    
    if not os.path.exists(example_path):
        typer.echo(f"Error: Example file {example} not found in {examples_dir}")
        return
    
    typer.echo(f"Running example: {example}")
    try:
        # Use subprocess to run the example
        import subprocess
        result = subprocess.run([sys.executable, example_path], check=True)
        typer.echo(f"Example completed with exit code {result.returncode}")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Example failed with exit code {e.returncode}")
    except Exception as e:
        typer.echo(f"Error: {e}")

@cli.command()
def run_gym(
    computer: ComputerType = typer.Option(ComputerType.LOCAL_PYNPUT, help="Type of computer to use"),
    agent: AgentType = typer.Option(AgentType.NAIVE, help="Type of agent to use"),
    model: str = typer.Option("gpt-4-vision-preview", help="Model to use for the agent"),
    steps: int = typer.Option(10, help="Maximum number of steps to run"),
):
    """Run a gym environment with a specified agent."""
    if not gym_available:
        typer.echo("Error: Gym module not available. Install with: pip install commandlab[gym]")
        return
    
    typer.echo(f"Running gym with {computer} computer and {agent} agent")
    typer.echo(f"Using model: {model}")
    typer.echo(f"Maximum steps: {steps}")
    typer.echo("Starting in 3 seconds...")
    time.sleep(3)
    
    try:
        # Configure the environment
        config = ComputerEnvConfig(
            computer_cls_name=f"Local{computer.value.split('-')[1].capitalize()}Computer" 
                if computer.value.startswith("local") else "DaemonClientComputer",
            computer_cls_kwargs={},
        )
        
        # Create the environment
        env = ComputerEnv(config)
        
        # Create the agent
        if agent == AgentType.NAIVE:
            agent_instance = NaiveComputerAgent(chat_model_options={
                "model_provider": "openai",
                "model": model,
            })
        elif agent == AgentType.REACT:
            agent_instance = ReactComputerAgent(
                model=model,
                device="cpu"
            )
        
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
            typer.echo(f"Step {i+1}: {step.action}")
            typer.echo(f"  Reward: {step.reward}")
        
    except KeyboardInterrupt:
        typer.echo("\nEpisode collection interrupted by user.")
    except Exception as e:
        typer.echo(f"\nError: {e}")
    finally:
        if 'driver' in locals():
            driver.close()
            typer.echo("Resources cleaned up.")

@cli.command()
def list_examples():
    """List all available example scripts."""
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
    
    if not os.path.exists(examples_dir):
        typer.echo(f"Error: Examples directory not found at {examples_dir}")
        return
    
    examples = [f for f in os.listdir(examples_dir) if f.endswith(".py")]
    examples.sort()
    
    typer.echo("Available examples:")
    for example in examples:
        # Try to extract the description from the file
        try:
            with open(os.path.join(examples_dir, example), "r") as f:
                content = f.read()
                import re
                match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if match:
                    description = match.group(1).strip().split("\n")[0]
                else:
                    description = "No description available"
        except:
            description = "Could not read file"
        
        typer.echo(f"  {example}: {description}")

if __name__ == "__main__":
    cli()
