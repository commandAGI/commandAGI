# Remote Control Tutorial

This tutorial will guide you through the process of setting up and using CommandLAB's remote control capabilities. You'll learn how to control a computer remotely using the daemon.

## Introduction

CommandLAB's remote control feature allows you to control one computer from another. This is useful for:

- Automating tasks on remote servers
- Controlling headless machines
- Setting up distributed automation systems
- Testing applications across different environments

## Prerequisites

Before you begin, make sure you have:

- CommandLAB installed on both the controller and target machines
- Network connectivity between the machines
- Appropriate permissions to run the daemon on the target machine

### Installation

On both machines, install CommandLAB with daemon support:

```bash
pip install "commandlab[daemon]"
```

## Step 1: Start the Daemon on the Target Machine

The first step is to start the daemon on the target machine (the one you want to control).

```bash
python -m commandLAB.daemon.cli start --port 8000 --backend pynput
```

This will start the daemon on port 8000 using the pynput backend for computer control. The daemon will print an API token that looks something like this:

```
Starting daemon on port 8000
API Token: abcdef1234567890abcdef1234567890
```

Make note of this token, as you'll need it to authenticate with the daemon.

## Step 2: Connect to the Daemon from the Controller Machine

Now, on the controller machine, you can connect to the daemon using the `DaemonClientComputer` class:

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandLAB.types import TypeAction, ClickAction, KeyboardHotkeyAction, KeyboardKey

# Connect to the daemon
computer = DaemonClientComputer(
    daemon_base_url="http://target-machine-ip",  # Replace with the actual IP address
    daemon_port=8000,
    provisioning_method=ProvisioningMethod.MANUAL
)

# Now you can control the target machine
```

## Step 3: Basic Remote Control Operations

Once connected, you can control the target machine using the same API as local control:

```python
# Take a screenshot of the remote computer
screenshot = computer.get_screenshot()

# Click at coordinates (100, 100) on the remote computer
computer.execute_click(ClickAction(x=100, y=100))

# Type text on the remote computer
computer.execute_type(TypeAction(text="Hello from another machine!"))

# Press keyboard shortcut (Ctrl+S) on the remote computer
computer.execute_keyboard_hotkey(KeyboardHotkeyAction(
    keys=[KeyboardKey.CTRL, KeyboardKey.S]
))
```

## Step 4: Execute Commands on the Remote Machine

You can also execute system commands on the remote machine:

```python
from commandLAB.types import CommandAction

# Execute a command on the remote machine
result = computer.execute_command(CommandAction(
    command="ls -la",
    timeout=5  # Timeout in seconds
))

if result:
    print("Command executed successfully")
else:
    print("Command failed")
```

## Step 5: Clean Up

When you're done, make sure to close the connection:

```python
# Clean up when done
computer.close()
```

## Complete Example: Remote Web Automation

Here's a complete example that automates opening a browser and performing a web search on a remote machine:

```python
import time
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandLAB.types import (
    CommandAction,
    TypeAction,
    KeyboardKeyPressAction,
    KeyboardHotkeyAction,
    KeyboardKey
)

# Connect to the daemon
computer = DaemonClientComputer(
    daemon_base_url="http://target-machine-ip",  # Replace with the actual IP address
    daemon_port=8000,
    provisioning_method=ProvisioningMethod.MANUAL
)

try:
    # Open a browser on the remote machine
    computer.execute_command(CommandAction(command="chrome"))
    time.sleep(2)  # Wait for the browser to open

    # Type a URL
    computer.execute_type(TypeAction(text="https://www.google.com"))
    computer.execute_keyboard_key_press(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
    time.sleep(2)  # Wait for the page to load

    # Type a search query
    computer.execute_type(TypeAction(text="CommandLAB python automation"))
    computer.execute_keyboard_key_press(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
    time.sleep(2)  # Wait for search results

    # Take a screenshot of the results
    screenshot = computer.get_screenshot()
    print("Took screenshot of search results")

    # Close the browser
    computer.execute_keyboard_hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.ALT, KeyboardKey.F4]))

finally:
    # Always clean up
    computer.close()
```

## Advanced: Secure Remote Control

For production use, you should secure your daemon:

### 1. Use HTTPS

Generate a self-signed certificate:

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

Start the daemon with HTTPS:

```bash
python -m commandLAB.daemon.cli start --port 8443 --backend pynput --ssl-cert cert.pem --ssl-key key.pem
```

Connect using HTTPS:

```python
computer = DaemonClientComputer(
    daemon_base_url="https://target-machine-ip",
    daemon_port=8443,
    provisioning_method=ProvisioningMethod.MANUAL
)
```

### 2. Use a Firewall

Restrict access to the daemon port using a firewall:

```bash
# On Linux
sudo ufw allow from trusted-ip-address to any port 8000

# On Windows
netsh advfirewall firewall add rule name="CommandLAB Daemon" dir=in action=allow protocol=TCP localport=8000 remoteip=trusted-ip-address
```

## Advanced: Automatic Provisioning

Instead of manually starting the daemon, you can use provisioners to automatically set up and manage daemon environments:

### Docker Provisioning

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod
from commandLAB.computers.provisioners.docker_provisioner import DockerPlatform

# Create a computer with Docker provisioning
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.DOCKER,
    platform=DockerPlatform.LOCAL
)

# Use the computer
# ...

# Clean up (stops and removes the container)
computer.close()
```

### Cloud Provisioning

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer, ProvisioningMethod

# Create a computer in AWS EC2
computer = DaemonClientComputer(
    provisioning_method=ProvisioningMethod.AWS,
    region="us-west-2",
    instance_type="t2.micro"
)

# Use the computer
# ...

# Clean up (terminates the EC2 instance)
computer.close()
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting to the daemon:

1. **Check Network Connectivity**: Make sure the machines can communicate
   ```bash
   ping target-machine-ip
   ```

2. **Check Firewall Settings**: Make sure the daemon port is open
   ```bash
   # On Linux
   sudo ufw status
   
   # On Windows
   netsh advfirewall firewall show rule name="CommandLAB Daemon"
   ```

3. **Check Daemon Status**: Make sure the daemon is running
   ```bash
   # On Linux
   ps aux | grep commandLAB.daemon
   
   # On Windows
   tasklist | findstr python
   ```

### Authentication Issues

If you're having authentication issues:

1. **Check API Token**: Make sure you're using the correct API token
2. **Restart the Daemon**: Sometimes restarting the daemon can help
3. **Check Logs**: Look for error messages in the daemon logs

## Exercises

1. **Basic Remote Control**: Connect to a remote machine and take a screenshot
2. **Remote File Management**: Create a script that manages files on a remote machine
3. **Multi-Machine Control**: Create a script that controls multiple remote machines
4. **Secure Daemon**: Set up a secure daemon with HTTPS and firewall rules

## Next Steps

- Learn about [Cloud Containers](../guides/cloud_containers.md)
- Try the [Training Agents Tutorial](training_agents.md)
- Explore [Provisioners](../concepts/provisioners.md) 