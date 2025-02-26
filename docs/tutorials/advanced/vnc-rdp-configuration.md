# Configuring VNC and RDP in CommandLAB

This tutorial explains how to configure VNC and RDP options in the CommandLAB daemon to work with different VNC and RDP implementations.

## Introduction

CommandLAB's daemon includes built-in support for starting and stopping VNC and RDP servers, which can be useful for remote viewing and control. These features are highly configurable to support different VNC and RDP implementations.

## Prerequisites

- CommandLAB installed with daemon support (`pip install "commandlab[daemon]"`)
- Basic understanding of VNC and RDP protocols
- VNC or RDP server software installed (optional, for testing)

## VNC Configuration

### Configuring VNC Executables

By default, the daemon looks for the following VNC executables:

- On Windows: `tvnserver.exe`, `vncserver.exe`, `winvnc.exe`
- On Unix-like systems: `vncserver`, `tigervncserver`, `x11vnc`

You can customize these lists to include other VNC implementations or specific paths:

```python
from commandLAB.daemon.server import ComputerDaemon
from commandLAB.computers.local_pynput_computer import LocalPynputComputer

# Create a computer instance
computer = LocalPynputComputer()

# Create a daemon with custom VNC executable paths
daemon = ComputerDaemon(
    computer=computer,
    vnc_windows_executables=["ultravnc.exe", "tightvnc.exe", "realvnc.exe"],
    vnc_unix_executables=["tigervnc", "tightvnc", "x11vnc", "novnc"]
)
```

When using the CLI, you can specify these as comma-separated lists:

```bash
python -m commandLAB.daemon.cli start \
    --vnc-windows-executables-str "ultravnc.exe,tightvnc.exe,realvnc.exe" \
    --vnc-unix-executables-str "tigervnc,tightvnc,x11vnc,novnc"
```

### Configuring VNC Start Commands

Different VNC implementations use different command-line arguments for starting the server. You can customize the start commands for each executable:

```python
daemon = ComputerDaemon(
    computer=computer,
    vnc_start_commands={
        "ultravnc.exe": "\"{path}\" -service",
        "x11vnc": "{path} -display :0 -bg -nopw -listen localhost -xkb",
        "tigervnc": "{path} -geometry 1920x1080 -depth 24"
    }
)
```

When using the CLI, you can specify these as a JSON string:

```bash
python -m commandLAB.daemon.cli start \
    --vnc-start-commands-str '{"ultravnc.exe": "\"{path}\" -service", "x11vnc": "{path} -display :0 -bg -nopw"}'
```

The `{path}` placeholder will be replaced with the full path to the VNC executable.

### Configuring VNC Stop Commands

Similarly, you can customize the stop commands for each executable:

```python
daemon = ComputerDaemon(
    computer=computer,
    vnc_stop_commands={
        "ultravnc.exe": "\"{path}\" -kill",
        "x11vnc": "pkill -f '{path}'",
        "tigervnc": "{path} -kill :1"
    }
)
```

When using the CLI, you can specify these as a JSON string:

```bash
python -m commandLAB.daemon.cli start \
    --vnc-stop-commands-str '{"ultravnc.exe": "\"{path}\" -kill", "x11vnc": "pkill -f \'{path}\'"}'
```

The stop commands support two placeholders:
- `{path}` - The full path to the VNC executable
- `{exe_name}` - The name of the VNC executable (useful for `taskkill` commands on Windows)

## RDP Configuration

### System Commands for RDP

On Windows, the daemon can use system commands to start and stop the built-in Remote Desktop Services. This is enabled by default, but you can disable it if you prefer to use a third-party RDP server like xrdp:

```python
daemon = ComputerDaemon(
    computer=computer,
    rdp_use_system_commands=False
)
```

When using the CLI, you can specify this as a boolean:

```bash
python -m commandLAB.daemon.cli start --rdp-use-system-commands false
```

When `rdp_use_system_commands` is `False`, the daemon will look for an `xrdp` installation instead of using Windows system commands.

## Complete Example

Here's a complete example that configures all VNC and RDP options:

```python
from commandLAB.daemon.server import ComputerDaemon
from commandLAB.computers.local_pynput_computer import LocalPynputComputer

# Create a computer instance
computer = LocalPynputComputer()

# Create a daemon with custom VNC and RDP configuration
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
    },
    
    # Disable system commands for RDP on Windows
    rdp_use_system_commands=False
)

# Start the daemon server
daemon.start_server(host="0.0.0.0", port=8000)
```

And the equivalent CLI command:

```bash
python -m commandLAB.daemon.cli start \
    --port 8000 \
    --vnc-windows-executables-str "ultravnc.exe,tightvnc.exe,realvnc.exe" \
    --vnc-unix-executables-str "tigervnc,tightvnc,x11vnc,novnc" \
    --vnc-start-commands-str '{"ultravnc.exe": "\"{path}\" -service", "x11vnc": "{path} -display :0 -bg -nopw -listen localhost -xkb", "tigervnc": "{path} -geometry 1920x1080 -depth 24"}' \
    --vnc-stop-commands-str '{"ultravnc.exe": "\"{path}\" -kill", "x11vnc": "pkill -f \'{path}\'", "tigervnc": "{path} -kill :1"}' \
    --rdp-use-system-commands false
```

## Using VNC and RDP

Once the daemon is running with your custom configuration, you can start and stop VNC and RDP servers using the API:

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer

# Connect to the daemon
computer = DaemonClientComputer(
    daemon_base_url="http://localhost",
    daemon_port=8000,
    daemon_token="your-api-token"
)

# Start a VNC server
result = computer.client.vnc_start_vnc_server()
print(f"VNC server started: {result.success}, Message: {result.message}")

# Start an RDP server
result = computer.client.rdp_start_rdp_server()
print(f"RDP server started: {result.success}, Message: {result.message}")

# Stop the servers when done
computer.client.vnc_stop_vnc_server()
computer.client.rdp_stop_rdp_server()
```

## Troubleshooting

### VNC Server Not Found

If you get a "No VNC server found" error, check that:

1. The VNC server is installed and in your PATH
2. You've configured the correct executable names
3. You have permission to run the VNC server

### VNC Server Failed to Start

If the VNC server fails to start, check that:

1. The start command template is correct for your VNC implementation
2. You have permission to start the VNC server
3. The VNC server is not already running

### RDP Server Issues

If you have issues with RDP:

1. On Windows, ensure you have administrator privileges if using system commands
2. If using xrdp, ensure it's installed and you have permission to start it
3. Check firewall settings to ensure the RDP port (usually 3389) is open

## Next Steps

- Learn about [Remote Control](../getting-started/remote-control.md) to understand how to use the daemon for remote control
- Explore [Cloud Deployment](cloud-deployment.md) for deploying the daemon in cloud environments
- Check out [Provisioner Usage](provisioner-usage.md) to learn how to automatically provision daemon environments 