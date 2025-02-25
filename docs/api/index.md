# API Reference

Welcome to the CommandLAB API reference. This section provides detailed documentation for all public APIs in the CommandLAB framework.

## Core

- [BaseComputer](core/base_computer.md) - Base class for all computer implementations
- [Types](core/types.md) - Data models for actions and observations
- [Utilities](core/utils.md) - Utility functions and helpers

## Computers

- [LocalPynputComputer](computers/local_pynput_computer.md) - Control local computer using pynput
- [LocalPyAutoGUIComputer](computers/local_pyautogui_computer.md) - Control local computer using PyAutoGUI
- [E2BDesktopComputer](computers/e2b_desktop_computer.md) - Control E2B Desktop Sandbox
- [DaemonClientComputer](computers/daemon_client_computer.md) - Control remote computers via daemon

## Provisioners

- [BaseProvisioner](provisioners/base_provisioner.md) - Base class for all provisioners
- [ManualProvisioner](provisioners/manual_provisioner.md) - Manual provisioning
- [DockerProvisioner](provisioners/docker_provisioner.md) - Docker container provisioning
- [KubernetesProvisioner](provisioners/kubernetes_provisioner.md) - Kubernetes provisioning
- [AWSProvisioner](provisioners/aws_provisioner.md) - AWS EC2 provisioning
- [AzureProvisioner](provisioners/azure_provisioner.md) - Azure VM provisioning
- [GCPProvisioner](provisioners/gcp_provisioner.md) - Google Cloud Platform provisioning

## Daemon

- [ComputerDaemon](daemon/computer_daemon.md) - Daemon server for remote control
- [DaemonClient](daemon/daemon_client.md) - Client for connecting to the daemon
- [CLI](daemon/cli.md) - Command-line interface for the daemon

## Gym Framework

- [BaseEnv](gym/base_env.md) - Base class for environments
- [MultiModalEnv](gym/multimodal_env.md) - Environment with multiple modalities
- [ComputerEnv](gym/computer_env.md) - Environment for computer control
- [BaseAgent](gym/base_agent.md) - Base class for agents
- [NaiveComputerAgent](gym/naive_computer_agent.md) - Simple vision-language agent
- [ReactComputerAgent](gym/react_computer_agent.md) - Agent using the ReAct framework
- [BaseDriver](gym/base_driver.md) - Base class for drivers
- [SimpleDriver](gym/simple_driver.md) - Single-threaded sequential driver
- [ThreadedDriver](gym/threaded_driver.md) - Multi-threaded driver
- [MultiprocessDriver](gym/multiprocess_driver.md) - Multi-process driver
- [BaseTrainer](gym/base_trainer.md) - Base class for trainers
- [OnlineTrainer](gym/online_trainer.md) - Trainer that trains after each episode
- [OfflineTrainer](gym/offline_trainer.md) - Trainer that trains after collecting all episodes
- [BatchTrainer](gym/batch_trainer.md) - Trainer that trains in batches

## Processors

- [ScreenParser](processors/screen_parser.md) - Parse text from screenshots
- [GridOverlay](processors/grid_overlay.md) - Overlay a grid on screenshots
- [AudioTranscription](processors/audio_transcription.md) - Transcribe audio to text
- [TextToSpeech](processors/tts.md) - Convert text to speech

## Utilities

- [Image](utils/image.md) - Image processing utilities
- [Viewer](utils/viewer.md) - GUI viewer for environments

## Using the API

### Basic Usage Pattern

Most CommandLAB APIs follow a consistent pattern:

```python
# Import the necessary classes
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.types import ClickAction, TypeAction

# Create an instance
computer = LocalPynputComputer()

# Use the instance
computer.execute_click(ClickAction(x=100, y=100))
computer.execute_type(TypeAction(text="Hello, CommandLAB!"))

# Clean up
computer.close()
```

### Error Handling

CommandLAB APIs use exceptions to indicate errors:

```python
try:
    computer = LocalPynputComputer()
    computer.execute_click(ClickAction(x=100, y=100))
except Exception as e:
    print(f"Error: {e}")
finally:
    computer.close()
```

### Async Support

Some CommandLAB APIs support async/await:

```python
import asyncio
from commandLAB.daemon.async_client import AsyncDaemonClient

async def main():
    client = AsyncDaemonClient("http://localhost:8000")
    try:
        screenshot = await client.get_screenshot()
        await client.execute_click(ClickAction(x=100, y=100))
    finally:
        await client.close()

asyncio.run(main())
```

## API Stability

CommandLAB follows semantic versioning:

- **Stable APIs**: Classes and methods in the public API without a leading underscore
- **Internal APIs**: Classes and methods with a leading underscore (e.g., `_internal_method`)
- **Experimental APIs**: Classes and methods in modules named `experimental`

## API Versioning

CommandLAB uses the following versioning scheme:

- **Major version**: Breaking changes to the API
- **Minor version**: New features without breaking changes
- **Patch version**: Bug fixes without breaking changes

## API Deprecation

When an API is deprecated:

1. It is marked with a `@deprecated` decorator
1. A warning is issued when the API is used
1. The API continues to work for at least one major version
1. The API is removed in the next major version

## Next Steps

- [Core Concepts](../concepts/index.md) - Learn about the fundamental concepts
- [Tutorials](../tutorials/index.md) - Step-by-step guides
- [Guides](../guides/index.md) - How-to guides for specific tasks
