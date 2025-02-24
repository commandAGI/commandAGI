# Welcome to CommandLAB

CommandLAB is a powerful framework for automating and controlling computers across different environments. It provides a unified interface for interacting with local and remote computers, making it easy to build automation tools, test applications, and train AI agents.

![CommandLAB Overview](assets/images/commandlab_overview.png)

## Key Features

- **Unified Computer Control API**: Control any computer with the same code
- **Multiple Deployment Options**: Run locally or in various cloud environments
- **Reinforcement Learning Framework**: Train agents to use computers
- **Modular Architecture**: Easily extend with new components

## Installation

```bash
pip install commandlab
```

### Optional Components

- Local computer control: `pip install "commandlab[local]"`
- VNC support: `pip install "commandlab[vnc]"`
- Docker support: `pip install "commandlab[docker]"`
- Kubernetes support: `pip install "commandlab[kubernetes]"`
- Cloud provider support: `pip install "commandlab[cloud]"`
- Daemon support: `pip install "commandlab[daemon]"`
- [E2B Desktop](https://e2b.dev/) integration: `pip install "commandlab[e2b-desktop]"`
- [Scrapybara](https://scrapybara.com/) integration: `pip install "commandlab[scrapybara]"`
- [LangChain](https://www.langchain.com/) integration: `pip install "commandlab[langchain]"`
- [PIG](https://www.pig.dev/) integration: `pip install "commandlab[pig]"`
- [Pytesseract](https://github.com/madmaze/pytesseract) OCR: `pip install "commandlab[pytesseract]"`
- Development tools: `pip install "commandlab[dev]"`

## Quick Example

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

## Documentation

- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Core Concepts](concepts/index.md)
- [Tutorials](tutorials/index.md)
- [API Reference](api/index.md)

## Who is CommandLAB for?

- **Automation Engineers**: Create robust automation scripts
- **AI Researchers**: Train and evaluate computer-using agents
- **DevOps Teams**: Automate testing across different environments
- **Python Developers**: Build tools that interact with computer UIs

