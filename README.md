<div align="center">
  <img src="assets/commandLAB-art.svg" alt="CommandAGI Lab Logo" width="400"/>
</div>

CommandAGI Lab framework, high performance, easy to learn, easy to use, production-ready

[![PyPI version](https://badge.fury.io/py/commandLAB.svg)](https://badge.fury.io/py/commandLAB)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Documentation Status](https://readthedocs.org/projects/commandLAB/badge/?version=latest)](https://commandagi.com/documentation/commandLAB)
[![Build Status](https://github.com/commandAGI/commandLAB/workflows/CI/badge.svg)](https://github.com/commandAGI/commandLAB/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

📖 Documentation [commandagi.com/documentation/commandLAB](https://commandagi.com/documentation/commandLAB)

🐙 Source Code [github.com/commandAGI/commandLAB](https://github.com/commandAGI/commandLAB)

---

CommandAGI Lab is a framework for developing agents that control computers like a human. It's designed for desktop automation but can really be used in any situation where you need to control a computer using Python. If this sounds useful to you, give this readme a few minutes to read thru to the end and you'll learn how to build your own desktop automation agent like commandAGI!

## Features

- Interface with the desktop just like a human:
  - Take screenshots
  - Send mouse and keyboard commands
  - Read the mouse and keyboard states
  - Send/receive microphone/speaker/camera streams ([planned](https://github.com/commandAGI/commandLAB/issues/5))

- Work anywhere, at any scale:
  - directly control your local desktop
  - VNC into a remote machine
  - spawn docker containers with fully managed OS environments
  - connect to Kubernetes clusters and spin up swarms

- Batteries included `Agent` class for developing autonomous computer interaction agents:
  - Fully-typed `ComputerObservation` and `ComputerCommand` classes
  - Individual `get_screenshot() -> ScreenshotComputerObservation`, `get_keyboard_state() -> KeyboardStateComputerObservation`, `click(MouseClickComputerAction)`, etc can be passed for observing and controlling individual modalities

- Extensible and flexible:
  - Create new `Computer` subclasses to support other providers
  - OpenRL gym integrations (coming soon)
  - Custom training code

## Installation

You can install CommandAGI Lab using pip:

```bash
pip install commandLAB
```

Or using Poetry (recommended):

```bash
poetry add commandLAB
```

### Optional Dependencies

CommandAGI Lab provides optional dependencies for different use cases:

```bash
# For Docker support
poetry add commandLAB[docker]

# For Kubernetes support
poetry add commandLAB[kubernetes]

# For daemon support
poetry add commandLAB[daemon]
```

## Quick Start

Check out the `examples/` directory to get started quickly:

```python
from commandLAB import Agent

# Initialize an agent
agent = Agent()

# Run a simple desktop automation task
agent.execute("open_browser")
```

### Using the Daemon

CommandLAB includes a daemon server that allows remote control of computers:

```python
from commandLAB.daemon.server import ComputerDaemon
from commandLAB.computers.local_pynput_computer import LocalPynputComputer

# Create a computer instance
computer = LocalPynputComputer()

# Create a daemon with default settings
daemon = ComputerDaemon(computer=computer)

# Or with custom VNC and RDP configurations
daemon = ComputerDaemon(
    computer=computer,
    vnc_windows_executables=["ultravnc.exe", "tightvnc.exe"],
    vnc_unix_executables=["tigervnc", "x11vnc"],
    rdp_use_system_commands=True
)

# Start the daemon server
daemon.start_server(host="0.0.0.0", port=8000)
```

You can also start the daemon from the command line:

```bash
python -m commandLAB.daemon.cli start --port 8000
```

For more details on configuring VNC and RDP options, see the [VNC/RDP Configuration Tutorial](docs/tutorials/advanced/vnc-rdp-configuration.md).

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/commandagi/commandLAB.git
cd commandLAB

# Install dependencies with Poetry
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

## Documentation

For detailed documentation, visit:

- [Official Documentation](https://commandagi.com/documentation/commandLAB)
- [API Reference](https://commandagi.com/documentation/commandLAB/api)

## License

This project is licensed under the MIT License - see the [LICENSE file](LICENSE) for details.

## Additional Links

- [Homepage](https://commandagi.com)
- [PyPI Package](https://pypi.org/project/commandLAB/)
- [Discord Community](https://discord.gg/commandagi)
