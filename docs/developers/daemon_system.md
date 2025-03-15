# Daemon System for Developers

This guide provides detailed information about the commandAGI daemon system for library developers who want to extend or modify the system.

## Architecture Overview

The daemon system provides a remote control interface for computers, allowing you to control a computer from another machine or process. It follows a client-server architecture with the following components:

1. **ComputerDaemon**: The server component that exposes a REST API for computer control
2. **Computer**: The client component that connects to a daemon server

## ComputerDaemon

The `ComputerDaemon` class is the core of the daemon system. It wraps a `BaseComputer` instance and exposes its functionality through a REST API.

### Basic Usage

```python
from commandAGI.daemon.server import ComputerDaemon
from commandAGI.computers.local_pynput_computer import LocalPynputComputer

# Create a computer instance
computer = LocalPynputComputer()

# Create a daemon
daemon = ComputerDaemon(computer=computer)

# Start the daemon server
daemon.start_server(host="0.0.0.0", port=8000)
```

### API Endpoints

The daemon exposes the following API endpoints:

- `/reset` - Reset the computer state
- `/execute/command` - Execute a shell command
- `/execute/keyboard/key_down` - Press a keyboard key
- `/execute/keyboard/key_release` - Release a keyboard key
- `/execute/keyboard/key_press` - Press and release a keyboard key
- `/execute/keyboard/hotkey` - Press a keyboard hotkey
- `/execute/type` - Type text
- `/execute/mouse/move` - Move the mouse
- `/execute/mouse/scroll` - Scroll the mouse wheel
- `/execute/mouse/button_down` - Press a mouse button
- `/execute/mouse/button_up` - Release a mouse button
- `/observation` - Get the current observation
- `/observation/screenshot` - Get a screenshot
- `/observation/mouse_state` - Get the mouse state
- `/observation/keyboard_state` - Get the keyboard state
- `/vnc/start` - Start a VNC server
- `/vnc/stop` - Stop a VNC server
- `/rdp/start` - Start an RDP server
- `/rdp/stop` - Stop an RDP server

### Security

The daemon uses token-based authentication to secure the API. You can provide a token when creating the daemon, or a random token will be generated:

```python
# Create a daemon with a custom token
daemon = ComputerDaemon(computer=computer, api_token="my-secret-token")
```

## VNC and RDP Configuration

The daemon includes built-in support for starting and stopping VNC and RDP servers, which can be useful for remote viewing and control. These features are highly configurable to support different VNC and RDP implementations.

### VNC Configuration

You can configure the VNC server executables and commands used by the daemon:

```python
# Create a daemon with custom VNC configuration
daemon = ComputerDaemon(
    computer=computer,
    # Custom VNC executables to search for
    vnc_windows_executables=["ultravnc.exe", "tightvnc.exe", "realvnc.exe"],
    vnc_unix_executables=["tigervnc", "tightvnc", "x11vnc", "novnc"],
    
    # Custom VNC start commands
    vnc_start_commands={
        "ultravnc.exe": "\"{path}\" -service",
        "x11vnc": "{path} -display :0 -bg -nopw -listen localhost -xkb",
        "tigervnc": "{path} -geometry 1920x1080 -depth 24"
    },
    
    # Custom VNC stop commands
    vnc_stop_commands={
        "ultravnc.exe": "\"{path}\" -kill",
        "x11vnc": "pkill -f '{path}'",
        "tigervnc": "{path} -kill :1"
    }
)
```

#### VNC Command Templates

The VNC start and stop commands support the following template variables:

- `{path}` - The full path to the VNC executable
- `{exe_name}` - The name of the VNC executable (for stop commands only)

### RDP Configuration

You can also configure whether to use system commands for RDP on Windows:

```python
# Create a daemon with custom RDP configuration
daemon = ComputerDaemon(
    computer=computer,
    # Disable system commands for RDP on Windows
    rdp_use_system_commands=False
)
```

When `rdp_use_system_commands` is `True` (the default), the daemon will use Windows system commands to start and stop the RDP server. When it's `False`, the daemon will look for an `xrdp` installation instead.

## Command-Line Interface

The daemon can be started from the command line using the `commandAGI.daemon.cli` module:

```bash
python -m commandAGI.daemon.cli start --port 8000 --api-token my-token
```

### CLI Options

The CLI supports the following options:

- `--host` - The host to bind the daemon to (default: "0.0.0.0")
- `--port` - The port to bind the daemon to (default: 8000)
- `--api-token` - The API token to use for the daemon (default: randomly generated)
- `--backend` - The backend to use for the computer (default: "pynput")
- `--additional-computer-cls-kwargs-str` - Additional keyword arguments to pass to the computer class (default: "{}")

### VNC and RDP Configuration Options

The CLI also supports the VNC and RDP configuration options:

```bash
python -m commandAGI.daemon.cli start \
    --port 8000 \
    --vnc-windows-executables-str "ultravnc.exe,tightvnc.exe,realvnc.exe" \
    --vnc-unix-executables-str "tigervnc,tightvnc,x11vnc,novnc" \
    --vnc-start-commands-str '{"ultravnc.exe": "\"{path}\" -service", "x11vnc": "{path} -display :0 -bg -nopw"}' \
    --vnc-stop-commands-str '{"ultravnc.exe": "\"{path}\" -kill", "x11vnc": "pkill -f \'{path}\'"}' \
    --rdp-use-system-commands false
```

## Computer

The `Computer` class is a client for the daemon API. It implements the `BaseComputer` interface, allowing you to use it like any other computer:

```python
from commandAGI.computers.daemon_client_computer import Computer

# Connect to a daemon
computer = Computer(
    daemon_base_url="http://localhost",
    daemon_port=8000,
    daemon_token="my-token"
)

# Use the computer
computer.type(TypeAction(text="Hello, world!"))
```

### Provisioning

The `Computer` can also handle provisioning of the daemon environment:

```python
from commandAGI.computers.daemon_client_computer import Computer, ProvisioningMethod

# Create a computer with Docker provisioning
computer = Computer(
    provisioning_method=ProvisioningMethod.DOCKER
)

# Use the computer
computer.execute_command(CommandAction(command="ls -la"))

# Clean up when done
computer.close()
```

## Extending the Daemon System

### Creating a Custom Daemon

You can create a custom daemon by subclassing `ComputerDaemon`:

```python
class MyCustomDaemon(ComputerDaemon):
    def __init__(self, computer, api_token=None):
        super().__init__(computer, api_token)
        
        # Add custom endpoints
        @self.app.get("/custom-endpoint")
        async def custom_endpoint(token: str = Depends(self.verify_token)):
            return {"message": "Custom endpoint"}
```

### Creating a Custom Client

You can create a custom client by subclassing `Computer`:

```python
class MyCustomClient(Computer):
    def __init__(self, daemon_base_url="http://localhost", daemon_port=8000, daemon_token=None):
        super().__init__(daemon_base_url, daemon_port, daemon_token)
        
    def custom_method(self):
        # Implement custom functionality
        pass
```

## Best Practices

1. **Security**: Always use a strong API token in production environments
2. **Error Handling**: Implement robust error handling for network issues
3. **Resource Cleanup**: Always clean up resources when done (especially with provisioning)
4. **Timeouts**: Configure appropriate timeouts for your use case
5. **Logging**: Enable logging for troubleshooting

By following these guidelines, you can create robust and maintainable daemon implementations that integrate seamlessly with the commandAGI ecosystem.
