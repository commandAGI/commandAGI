# Daemon

The CommandLAB daemon is a service that allows remote control of computers through a REST API.

![Daemon Architecture](../assets/images/daemon_architecture.png)

## What is the Daemon?

The daemon is a FastAPI server that:

1. Exposes computer functionality through HTTP endpoints
1. Provides authentication via API tokens
1. Can be deployed in various environments (local, Docker, cloud)

This allows you to control computers remotely, even across networks or cloud environments.

## Starting the Daemon

You can start the daemon using the CLI:

```bash
python -m commandLAB.daemon.cli start --port 8000 --backend pynput
```

This starts a daemon server on port 8000 using the pynput backend for computer control.

## Daemon API

The daemon exposes endpoints for all computer actions:

- `/screenshot` - Get a screenshot
- `/mouse/state` - Get mouse state
- `/keyboard/state` - Get keyboard state
- `/command` - Execute a command
- `/keyboard/key/down` - Press a key down
- `/keyboard/key/release` - Release a key
- `/mouse/move` - Move the mouse
- `/mouse/button/down` - Press a mouse button
- `/mouse/button/up` - Release a mouse button
- ... and more

All endpoints require authentication via an API token, which is generated when the daemon starts.

## Connecting to the Daemon

You can connect to the daemon using the `DaemonClientComputer`:

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer

computer = DaemonClientComputer(
    daemon_base_url="http://localhost",
    daemon_port=8000
)
```

This creates a computer object that sends commands to the daemon over HTTP.

## Daemon with Provisioners

The `DaemonClientComputer` can use provisioners to automatically set up and manage daemon environments:

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer with Docker provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER
)

# This automatically:
# 1. Creates a Docker container with the daemon
# 2. Starts the daemon in the container
# 3. Connects to the daemon

# When you're done:
computer.close()  # Stops and removes the container
```

## Security Considerations

The daemon includes several security features:

- **API Token Authentication**: All requests require a valid token
- **HTTPS Support**: Can be configured to use HTTPS for encrypted communication
- **Isolation**: When deployed in containers or VMs, provides isolation from the host

However, you should be careful when exposing the daemon to untrusted networks, as it provides full control over the computer it runs on.

## Customizing the Daemon

You can customize the daemon by creating your own instance of `ComputerDaemon`:

```python
from commandLAB.daemon.server import ComputerDaemon
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
import uvicorn

# Create a custom daemon
daemon = ComputerDaemon(
    computer_cls=LocalPynputComputer,
    computer_cls_kwargs={"custom_option": True}
)

# Start the server
uvicorn.run(daemon.app, host="0.0.0.0", port=8000)
```

This allows you to use custom computer implementations or configuration options with the daemon.
