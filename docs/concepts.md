# CommandLAB Documentation

CommandLAB is a comprehensive framework for automating and interacting with computer environments. It provides a flexible architecture for controlling computers through various backends, supporting both local and remote execution.

## Core Architecture

CommandLAB is built around a modular architecture with several key components:

1. **Computers**: Implementations that provide direct control over computer systems
2. **Provisioners**: Components that set up and manage computer environments
3. **Gym**: A reinforcement learning framework for training agents
4. **Daemon**: A service that allows remote control of computers

## Computers

The `BaseComputer` class defines the interface for all computer implementations. It provides methods for:

- Taking screenshots
- Getting mouse and keyboard state
- Executing keyboard and mouse actions
- Running system commands

### Computer Implementations

- **LocalPynputComputer**: Uses the pynput library to control the local computer
- **LocalPyAutoGUIComputer**: Uses PyAutoGUI for local computer control
- **E2BDesktopComputer**: Integrates with E2B Desktop Sandbox for secure interactions
- **DaemonClientComputer**: Connects to a remote daemon for computer control

## Provisioners

Provisioners handle the setup, management, and teardown of computer environments. The framework supports multiple deployment options:

### Provisioner Types

- **ManualProvisioner**: Provides instructions for manual setup
- **DockerProvisioner**: Deploys environments in Docker containers
- **KubernetesProvisioner**: Manages deployments in Kubernetes clusters
- **AWSProvisioner**: Creates and manages EC2 instances
- **AzureProvisioner**: Provisions VMs in Azure
- **GCPProvisioner**: Sets up environments in Google Cloud

Each provisioner implements the `BaseComputerProvisioner` interface with methods for:
- `setup()`: Initialize the environment
- `teardown()`: Clean up resources
- `is_running()`: Check if the environment is active

## Daemon

The daemon component allows remote control of computers through a REST API:

- **ComputerDaemon**: Exposes computer functionality through a FastAPI server
- **DaemonClientComputer**: Connects to a daemon to control a remote computer

The daemon supports authentication via API tokens and provides endpoints for all computer actions.

## Gym Framework

CommandLAB includes a reinforcement learning framework inspired by OpenAI Gym:

### Key Components

- **BaseEnv**: Abstract environment interface
- **MultiModalEnv**: Environment with multiple observation and action types
- **ComputerEnv**: Environment specifically for computer interaction
- **BaseTask**: Defines goals for agents to accomplish
- **ComputerTaskMixin**: Base for computer-specific tasks

### Training Components

- **BaseDriver**: Collects episodes of agent-environment interaction
- **SimpleDriver**: Sequential episode collection
- **ThreadedDriver**: Multi-threaded collection
- **MultiprocessDriver**: Parallel collection using multiple processes
- **BaseTrainer**: Interface for training agents
- **Episode**: Records steps in an environment

## Types

CommandLAB defines a comprehensive type system for computer interactions:

- **MouseButton**: Enum for mouse buttons (LEFT, RIGHT, MIDDLE)
- **KeyboardKey**: Enum for keyboard keys
- **ComputerObservation**: Observations from the computer (screenshots, mouse/keyboard state)
- **ComputerAction**: Actions to perform on the computer (mouse movements, key presses, etc.)

## Development Tools

The package includes tools for development:

- **build_images.py**: Builds Docker images and cloud VM images
- **update_daemon_client.py**: Generates client code from the daemon API
- **version.py**: Manages package and container versioning

## Usage Examples

### Basic Local Control

```python
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.types import ClickAction, TypeAction

# Create a computer instance
computer = LocalPynputComputer()

# Take a screenshot
screenshot = computer.get_screenshot()

# Click at coordinates
computer.execute_click(ClickAction(x=100, y=100))

# Type text
computer.execute_type(TypeAction(text="Hello, world!"))
```

### Remote Control via Daemon

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandLAB.types import CommandAction

# Create a computer with Docker provisioning
computer = DaemonClientComputer(provisioning_method=ProvisioningMethod.DOCKER)

# Execute a command
computer.execute_command(CommandAction(command="echo Hello", timeout=5))

# Clean up when done
computer.close()
```

### Using the Gym Framework

```python
from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
from commandLAB.gym.drivers import SimpleDriver
from commandLAB.agents.simple_vision_language_computer_agent import SimpleComputerAgent

# Configure environment
config = ComputerEnvConfig(computer_cls_name="LocalPynputComputer")
env = ComputerEnv(config)

# Create agent
agent = SimpleComputerAgent()

# Create driver and collect episodes
driver = SimpleDriver(env, agent)
episode = driver.collect_episode()
```

## Versioning

CommandLAB uses semantic versioning:
- Package version: Defined in `__version__` variable
- Container version: May differ from package version, defined in `CONTAINER_VERSION`

## Development

To build container images:

```bash
python -m commandLAB.dev.build_images build_docker_image
```

To update the daemon client:

```bash
python -m commandLAB.dev.update_daemon_client
```

## Conclusion

CommandLAB provides a powerful framework for computer automation, with support for local and remote execution, various deployment options, and a reinforcement learning framework for training agents. Its modular architecture allows for easy extension and customization.
