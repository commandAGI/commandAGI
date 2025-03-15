# Quick Start Guide

This guide will help you get up and running with commandAGI quickly. We'll cover the basics of local computer control, remote control via daemon, and using Docker provisioning.

## Installation

First, install commandAGI with the components you need:

```bash
# For local computer control
pip install "commandagi[local]"

# For remote control via daemon
pip install "commandagi[daemon]"

# For Docker provisioning
pip install "commandagi[docker]"

# For all features
pip install "commandagi[all]"
```

## Basic Usage: Local Computer Control

The simplest way to use commandAGI is to control your local computer:

```python
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.types import ClickAction, TypeAction, KeyboardHotkeyAction, KeyboardKey

# Create a computer instance
computer = LocalPynputComputer()

# Take a screenshot
screenshot = computer.get_screenshot()

# Click at coordinates (100, 100)
computer.click(ClickAction(x=100, y=100))

# Type text
computer.type(TypeAction(text="Hello, commandAGI!"))

# Press keyboard shortcut (Ctrl+S)
computer.hotkey(KeyboardHotkeyAction(
    keys=[KeyboardKey.CTRL, KeyboardKey.S]
))
```

### Available Actions

commandAGI provides a rich set of actions for controlling computers:

| Action | Description | Example |
|--------|-------------|---------|
| `ClickAction` | Click at specific coordinates | `ClickAction(x=100, y=200)` |
| `DoubleClickAction` | Double-click at coordinates | `DoubleClickAction(x=100, y=200)` |
| `TypeAction` | Type text | `TypeAction(text="Hello")` |
| `KeyboardKeyPressAction` | Press a key | `KeyboardKeyPressAction(key=KeyboardKey.ENTER)` |
| `KeyboardHotkeyAction` | Press a keyboard shortcut | `KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.C])` |
| `MouseMoveAction` | Move the mouse | `MouseMoveAction(x=100, y=200)` |
| `DragAction` | Drag from one point to another | `DragAction(start_x=100, start_y=100, end_x=200, end_y=200)` |
| `CommandAction` | Execute a system command | `CommandAction(command="ls -la", timeout=5)` |

### Getting Observations

You can also get observations about the computer's state:

```python
# Get a screenshot
screenshot = computer.get_screenshot()
print(f"Screenshot size: {len(screenshot.screenshot)} bytes")

# Get mouse state
mouse_state = computer.get_mouse_state()
print(f"Mouse position: {mouse_state.position}")
print(f"Mouse buttons: {mouse_state.buttons}")

# Get keyboard state
keyboard_state = computer.get_keyboard_state()
print(f"Shift key pressed: {keyboard_state.keys.get(KeyboardKey.SHIFT, False)}")
```

## Remote Control via Daemon

commandAGI allows you to control remote computers using a daemon server:

### Starting the Daemon

First, start the daemon on the target computer:

```bash
# Start the daemon on port 8000 using the pynput backend
python -m commandAGI.daemon.cli start --port 8000 --backend pynput
```

The daemon will print an API token that you'll need to connect to it.

### Connecting to the Daemon

Then, control it from another machine:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.types import TypeAction, ClickAction

# Connect to the daemon manually
computer = DaemonClientComputer(
    daemon_base_url="http://target-machine-ip",
    daemon_port=8000,
    provisioning_method=ProvisioningMethod.MANUAL
)

# Take a screenshot of the remote computer
screenshot = computer.get_screenshot()

# Click at coordinates (100, 100) on the remote computer
computer.click(ClickAction(x=100, y=100))

# Type text on the remote computer
computer.type(TypeAction(text="Hello from another machine!"))

# Clean up when done
computer.close()
```

## Using Docker Provisioning

commandAGI can automatically provision and manage Docker containers:

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandAGI.types import CommandAction, TypeAction
from commandAGI.computers.provisioners.docker_provisioner import DockerPlatform

# Create a computer with Docker provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.LOCAL  # Use local Docker
)

# Execute a command in the container
computer.execute_command(CommandAction(command="ls -la", timeout=5))

# Type text in the container
computer.type(TypeAction(text="Hello from Docker!"))

# Clean up (stops and removes the container)
computer.close()
```

## Using Cloud Provisioning

commandAGI supports provisioning computers in various cloud environments:

### AWS EC2

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer in AWS EC2
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.AWS,
    region="us-west-2",
    instance_type="t2.micro"
)

# Use the computer
# ...

# Clean up (terminates the EC2 instance)
computer.close()
```

### Azure VM

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer in Azure
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.AZURE,
    resource_group="my-resource-group",
    location="eastus"
)

# Use the computer
# ...

# Clean up (deletes the Azure VM)
computer.close()
```

### Google Cloud Platform

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer in GCP
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.GCP,
    project="my-project-id",
    zone="us-central1-a"
)

# Use the computer
# ...

# Clean up (deletes the GCP VM)
computer.close()
```

## Using the Gym Framework

commandAGI includes a reinforcement learning framework for training agents:

```python
from commandAGI.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
from commandAGI.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent
from commandAGI.gym.drivers import SimpleDriver

# Configure the environment
config = ComputerEnvConfig(
    computer_cls_name="LocalPynputComputer"
)

# Create the environment
env = ComputerEnv(config)

# Create an agent
agent = NaiveComputerAgent(chat_model_options={
    "model_provider": "openai",
    "model": "gpt-4-vision-preview"
})

# Create a driver
driver = SimpleDriver(env=env, agent=agent)

# Collect an episode
episode = driver.collect_episode()

# Print episode statistics
print(f"Episode length: {episode.num_steps}")
print(f"Total reward: {sum(step.reward for step in episode)}")
```

## Complete Example: Automating a Web Search

Here's a complete example that automates opening a browser and performing a web search:

```python
import time
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.types import (
    CommandAction,
    TypeAction,
    ClickAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyPressAction
)

# Create a computer instance
computer = LocalPynputComputer()

# Open a browser (Chrome in this example)
computer.execute_command(CommandAction(command="chrome"))
time.sleep(2)  # Wait for the browser to open

# Type a URL
computer.type(TypeAction(text="https://www.google.com"))
computer.keypress(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
time.sleep(2)  # Wait for the page to load

# Type a search query
computer.type(TypeAction(text="commandAGI python automation"))
computer.keypress(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
time.sleep(2)  # Wait for search results

# Take a screenshot of the results
screenshot = computer.get_screenshot()
print("Took screenshot of search results")

# Close the browser
computer.hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.ALT, KeyboardKey.F4]))
```

## Next Steps

Now that you've learned the basics of commandAGI, you can:

- Learn about [Core Concepts](concepts/index.md)
- Explore [Computer Types](concepts/computers.md)
- Understand [Provisioners](concepts/provisioners.md)
- Try the [Gym Framework](concepts/gym.md)
- Follow the [Basic Automation Tutorial](tutorials/basic_automation.md)
- Check out the [API Reference](api/index.md)
