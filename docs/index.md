# Welcome to commandAGI

commandAGI is a powerful framework for automating and controlling computers across different environments. It provides a unified interface for interacting with local and remote computers, making it easy to build automation tools, test applications, and train AI agents.

![commandAGI Overview](assets/images/commandAGI2_overview.png)

## Key Features

- **Unified Computer Control API**: Control any computer with the same code, regardless of platform or location
- **Multiple Deployment Options**: Run locally, in containers, or in various cloud environments
- **Reinforcement Learning Framework**: Train and evaluate AI agents to use computers through a standardized gym interface
- **Modular Architecture**: Easily extend with new computer implementations, provisioners, or agent types
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
- **Cloud Integration**: Native support for AWS, Azure, and Google Cloud Platform
- **Container Support**: Docker and Kubernetes integration for scalable deployments

## Installation

```bash
pip install commandagi
```

### Optional Components

commandAGI uses a modular design with optional components that can be installed based on your needs:

| Component | Description | Installation |
|-----------|-------------|--------------|
| Local control | Control your local computer | `pip install "commandagi[local]"` |
| VNC support | Control computers via VNC | `pip install "commandagi[vnc]"` |
| Docker support | Run in Docker containers | `pip install "commandagi[docker]"` |
| Kubernetes support | Deploy in Kubernetes | `pip install "commandagi[kubernetes]"` |
| Cloud providers | AWS, Azure, GCP integration | `pip install "commandagi[cloud]"` |
| Daemon | Remote control server | `pip install "commandagi[daemon]"` |
| E2B Desktop | [E2B Desktop](https://e2b.dev/) integration | `pip install "commandagi[e2b-desktop]"` |
| Scrapybara | [Scrapybara](https://scrapybara.com/) integration | `pip install "commandagi[scrapybara]"` |
| LangChain | [LangChain](https://www.langchain.com/) integration | `pip install "commandagi[langchain]"` |
| PIG | [PIG](https://www.pig.dev/) integration | `pip install "commandagi[pig]"` |
| OCR | [Pytesseract](https://github.com/madmaze/pytesseract) OCR | `pip install "commandagi[pytesseract]"` |
| Development | Tools for contributing | `pip install "commandagi[dev]"` |
| All features | Everything included | `pip install "commandagi[all]"` |

## Quick Example

```python
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.types import ClickAction, TypeAction

# Create a computer instance
computer = LocalPynputComputer()

# Take a screenshot
screenshot = computer.get_screenshot()

# Click at coordinates (100, 100)
computer.click(ClickAction(x=100, y=100))

# Type text
computer.type(TypeAction(text="Hello, commandAGI!"))
```

## Remote Control Example

```python
from commandAGI.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer with Docker provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER
)

# Execute a command in the container
computer.execute_command(CommandAction(command="ls -la", timeout=5))

# Clean up when done
computer.close()
```

## Documentation

- [Installation Guide](installation.md) - Detailed installation instructions
- [Quick Start Guide](quickstart.md) - Get up and running quickly
- [Examples](examples.md) - Example scripts with status and usage information
- [Core Concepts](concepts/index.md) - Learn about the fundamental concepts
  - [Computers](concepts/computers.md) - Computer implementations
  - [Provisioners](concepts/provisioners.md) - Environment management
  - [Gym Framework](concepts/gym.md) - Reinforcement learning
  - [Daemon](concepts/daemon.md) - Remote control
  - [Types](concepts/types.md) - Data models
- [Tutorials](tutorials/index.md) - Step-by-step guides
  - [Getting Started](tutorials/index.md#getting-started) - Basic tutorials
  - [Advanced](tutorials/index.md#advanced) - Advanced topics
  - [Examples](tutorials/index.md#examples) - Real-world examples
- [API Reference](api/index.md) - Detailed API documentation
- [Developer Guide](developers/index.md) - Contributing to commandAGI

## Who is commandAGI for?

- **Automation Engineers**: Create robust automation scripts that work across different environments
- **AI Researchers**: Train and evaluate computer-using agents with a standardized interface
- **DevOps Teams**: Automate testing and deployment across different platforms
- **Python Developers**: Build tools that interact with computer UIs in a consistent way
- **QA Engineers**: Create automated tests for GUI applications

## Community and Support

- [GitHub Repository](https://github.com/your-org/commandagi) - Source code and issue tracking
- [Documentation](https://your-org.github.io/commandagi) - Online documentation
- [Discord Community](https://discord.gg/your-discord) - Community support and discussions

## License

commandAGI is released under the MIT License. See the [LICENSE](https://github.com/your-org/commandagi/blob/main/LICENSE) file for details.
