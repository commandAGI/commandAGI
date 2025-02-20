<div align="center">
  <img src="assets/commandagi-lab-art.svg" alt="CommandAGI Lab Logo" width="400"/>
</div>

CommandAGI Lab framework, high performance, easy to learn, easy to use, production-ready

[![PyPI version](https://badge.fury.io/py/commandagi-lab.svg)](https://badge.fury.io/py/commandagi-lab)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Documentation Status](https://readthedocs.org/projects/commandagi-lab/badge/?version=latest)](https://commandagi.com/documentation/commandAGI_LAB)
[![Build Status](https://github.com/commandAGI/commandAGI_LAB/workflows/CI/badge.svg)](https://github.com/commandAGI/commandAGI_LAB/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

📖 Documentation [commandagi.com/documentation/commandAGI_LAB](https://commandagi.com/documentation/commandAGI_LAB)

🐙 Source Code [github.com/commandAGI/commandAGI_LAB](https://github.com/commandAGI/commandAGI_LAB)

---

CommandAGI Lab is a framework for developing agents that control computers like a human. It's designed for desktop automation but can really be used in any situation where you need to control a computer using Python. If this sounds useful to you, give this readme a few minutes to read thru to the end and you'll learn how to build your own desktop automation agent like commandAGI!

## Features

- Interface with the desktop just like a human:
  - Take screenshots
  - Send mouse and keyboard commands
  - Read the mouse and keyboard states
  - Send/receive microphone/speaker/camera streams ([planned](https://github.com/commandAGI/commandAGI_LAB/issues/5))

- Work anywhere, at any scale:
  - directly control your local desktop
  - VNC into a remote machine
  - spawn docker containers with fully managed OS environments
  - connect to Kubernetes clusters and spin up swarms

- Powerful abstractions for developing agentic commands:
  - Fully-typed `ComputerObservation` and `ComputerCommand` classes
  - Individual `get_screenshot() -> ScreenshotComputerObservation`, `get_keyboard_state() -> KeyboardStateComputerObservation`, `click(MouseClickComputerAction)`, etc for observing and controlling individual modalities
  - `ComputerEnv` openrl gym for integrating with openrl's (and by extention, gymnasiums and pettingzoo's) comprehensive suite of tools for training agents

- Extensible and flexible:
  - Create new `Computer` subclasses to support other providers
  - Custom training code

## Installation

You can install CommandAGI Lab using pip:

```bash
pip install commandagi-lab
```

Or using Poetry (recommended):

```bash
poetry add commandagi-lab
```

### Optional Dependencies

CommandAGI Lab provides optional dependencies for different use cases:

```bash
# For Docker support
poetry add commandagi-lab[docker]

# For Kubernetes support
poetry add commandagi-lab[kubernetes]
```

## Quick Start

Check out the `examples/` directory to get started quickly:

```python
from commandagi-lab import Agent

# Initialize an agent
agent = Agent()

# Run a simple desktop automation task
agent.execute("open_browser")
```

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/commandagi/commandagi-lab.git
cd commandagi-lab

# Install dependencies with Poetry
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

## Documentation

For detailed documentation, visit:

- [Official Documentation](https://commandagi.com/documentation/commandAGI_LAB)
- [API Reference](https://commandagi.com/documentation/commandAGI_LAB/api)

## License

This project is licensed under the MIT License - see the [LICENSE file](LICENSE) for details.

## Additional Links

- [Homepage](https://commandagi.com)
- [PyPI Package](https://pypi.org/project/commandagi-lab/)
- [Discord Community](https://discord.gg/commandagi)
