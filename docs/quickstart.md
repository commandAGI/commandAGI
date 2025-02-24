# Quick Start Guide

This guide will help you get up and running with CommandLAB quickly.

## Basic Usage: Local Computer Control

```python
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.types import ClickAction, TypeAction

# Create a computer instance
computer = LocalPynputComputer()

# Take a screenshot
screenshot = computer.get_screenshot()

# Click at coordinates (100, 100)
computer.execute_click(ClickAction(x=100, y=100))

# Type text
computer.execute_type(TypeAction(text="Hello, CommandLAB!"))
```

## Remote Control via Daemon

First, start the daemon on the target computer:

```bash
python -m commandLAB.daemon.cli start --port 8000 --backend pynput
```

Then, control it from another machine:

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandLAB.types import TypeAction

# Connect to the daemon
computer = DaemonClientComputer(
    daemon_base_url="http://target-machine-ip",
    daemon_port=8000,
    provisioning_method=ProvisioningMethod.MANUAL
)

# Type text on the remote computer
computer.execute_type(TypeAction(text="Hello from another machine!"))

# Clean up when done
computer.close()
```

## Using Docker Provisioning

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandLAB.types import CommandAction

# Create a computer with Docker provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER
)

# Execute a command in the container
computer.execute_command(CommandAction(command="ls -la", timeout=5))

# Clean up (stops and removes the container)
computer.close()
```

## Next Steps

- Learn about [Core Concepts](concepts/index.md)
- Explore [Computer Types](concepts/computers.md)
- Understand [Provisioners](concepts/provisioners.md)
- Try the [Gym Framework](concepts/gym.md)