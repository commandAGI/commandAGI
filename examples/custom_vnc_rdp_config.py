#!/usr/bin/env python3
"""
Example of using the ComputerDaemon with custom VNC and RDP configurations.

This example demonstrates how to:
1. Start a daemon with custom VNC executable paths
2. Configure custom VNC start/stop commands
3. Control RDP system command usage

Usage:
    python custom_vnc_rdp_config.py
"""

import json
import subprocess
import sys
import time
from typing import Dict, List, Optional


# Example 1: Start a daemon with custom VNC executables
def start_daemon_with_custom_vnc_executables():
    """
    Start a daemon with custom VNC executable paths.
    """
    print("Starting daemon with custom VNC executables...")

    # Custom VNC executables for Windows
    windows_exes = "ultravnc.exe,tightvnc.exe,realvnc.exe"

    # Custom VNC executables for Unix
    unix_exes = "tigervnc,tightvnc,x11vnc,novnc"

    # Start the daemon with custom executables
    cmd = [
        sys.executable,
        "-m",
        "commandAGI2.daemon.cli",
        "start",
        "--port",
        "8001",
        "--vnc-windows-executables-str",
        windows_exes,
        "--vnc-unix-executables-str",
        unix_exes,
    ]

    daemon_process = subprocess.Popen(cmd)

    # Wait for the daemon to start
    time.sleep(2)
    print("Daemon started with custom VNC executables")

    # In a real application, you would use the daemon here

    # Cleanup
    daemon_process.terminate()
    daemon_process.wait()
    print("Daemon stopped")


# Example 2: Start a daemon with custom VNC start/stop commands
def start_daemon_with_custom_vnc_commands():
    """
    Start a daemon with custom VNC start and stop commands.
    """
    print("\nStarting daemon with custom VNC start/stop commands...")

    # Custom VNC start commands
    start_commands = {
        "ultravnc.exe": '"{path}" -service',
        "x11vnc": "{path} -display :0 -bg -nopw -listen localhost -xkb",
        "tigervnc": "{path} -geometry 1920x1080 -depth 24",
    }

    # Custom VNC stop commands
    stop_commands = {
        "ultravnc.exe": '"{path}" -kill',
        "x11vnc": "pkill -f '{path}'",
        "tigervnc": "{path} -kill :1",
    }

    # Convert to JSON strings
    start_commands_json = json.dumps(start_commands)
    stop_commands_json = json.dumps(stop_commands)

    # Start the daemon with custom commands
    cmd = [
        sys.executable,
        "-m",
        "commandAGI2.daemon.cli",
        "start",
        "--port",
        "8002",
        "--vnc-start-commands-str",
        start_commands_json,
        "--vnc-stop-commands-str",
        stop_commands_json,
    ]

    daemon_process = subprocess.Popen(cmd)

    # Wait for the daemon to start
    time.sleep(2)
    print("Daemon started with custom VNC commands")

    # In a real application, you would use the daemon here

    # Cleanup
    daemon_process.terminate()
    daemon_process.wait()
    print("Daemon stopped")


# Example 3: Start a daemon with custom RDP configuration
def start_daemon_with_custom_rdp_config():
    """
    Start a daemon with custom RDP configuration.
    """
    print("\nStarting daemon with custom RDP configuration...")

    # Start the daemon with RDP system commands disabled
    cmd = [
        sys.executable,
        "-m",
        "commandAGI2.daemon.cli",
        "start",
        "--port",
        "8003",
        "--rdp-use-system-commands",
        "false",
    ]

    daemon_process = subprocess.Popen(cmd)

    # Wait for the daemon to start
    time.sleep(2)
    print("Daemon started with RDP system commands disabled")

    # In a real application, you would use the daemon here

    # Cleanup
    daemon_process.terminate()
    daemon_process.wait()
    print("Daemon stopped")


# Example 4: Start a daemon with all custom configurations
def start_daemon_with_all_custom_configs():
    """
    Start a daemon with all custom VNC and RDP configurations.
    """
    print("\nStarting daemon with all custom configurations...")

    # Custom VNC executables
    windows_exes = "ultravnc.exe,tightvnc.exe"
    unix_exes = "tigervnc,x11vnc"

    # Custom VNC commands
    start_commands = {
        "ultravnc.exe": '"{path}" -service',
        "x11vnc": "{path} -display :0 -bg -nopw",
    }
    stop_commands = {"ultravnc.exe": '"{path}" -kill', "x11vnc": "pkill -f '{path}'"}

    # Convert to JSON strings
    start_commands_json = json.dumps(start_commands)
    stop_commands_json = json.dumps(stop_commands)

    # Start the daemon with all custom configurations
    cmd = [
        sys.executable,
        "-m",
        "commandAGI2.daemon.cli",
        "start",
        "--port",
        "8004",
        "--vnc-windows-executables-str",
        windows_exes,
        "--vnc-unix-executables-str",
        unix_exes,
        "--vnc-start-commands-str",
        start_commands_json,
        "--vnc-stop-commands-str",
        stop_commands_json,
        "--rdp-use-system-commands",
        "false",
    ]

    daemon_process = subprocess.Popen(cmd)

    # Wait for the daemon to start
    time.sleep(2)
    print("Daemon started with all custom configurations")

    # In a real application, you would use the daemon here

    # Cleanup
    daemon_process.terminate()
    daemon_process.wait()
    print("Daemon stopped")


# Example 5: Programmatic usage with the ComputerDaemon class
def use_computer_daemon_class_directly():
    """
    Use the ComputerDaemon class directly with custom configurations.
    """
    print("\nUsing ComputerDaemon class directly...")

    from commandAGI2.daemon.server import ComputerDaemon
    from commandAGI2.computers.local_pynput_computer import LocalPynputComputer
    import threading

    # Custom VNC configurations
    vnc_windows_executables = ["ultravnc.exe", "tightvnc.exe"]
    vnc_unix_executables = ["tigervnc", "x11vnc"]

    vnc_start_commands = {
        "ultravnc.exe": '"{path}" -service',
        "x11vnc": "{path} -display :0 -bg -nopw",
    }

    vnc_stop_commands = {
        "ultravnc.exe": '"{path}" -kill',
        "x11vnc": "pkill -f '{path}'",
    }

    # Create a computer instance
    computer = LocalPynputComputer()

    # Create the daemon with custom configurations
    daemon = ComputerDaemon(
        computer=computer,
        vnc_windows_executables=vnc_windows_executables,
        vnc_unix_executables=vnc_unix_executables,
        vnc_start_commands=vnc_start_commands,
        vnc_stop_commands=vnc_stop_commands,
        rdp_use_system_commands=False,
    )

    # Start the daemon in a separate thread
    daemon_thread = threading.Thread(
        target=daemon.start_fastapi_server, kwargs={"host": "localhost", "port": 8005}
    )
    daemon_thread.daemon = True
    daemon_thread.start()

    print(f"Daemon started with API token: {daemon._api_token}")

    # Wait a moment for the server to start
    time.sleep(2)

    # In a real application, you would use the daemon here

    print("Daemon running (press Ctrl+C to stop)")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping daemon...")


if __name__ == "__main__":
    try:
        # Run the examples
        start_daemon_with_custom_vnc_executables()
        start_daemon_with_custom_vnc_commands()
        start_daemon_with_custom_rdp_config()
        start_daemon_with_all_custom_configs()

        # This example runs until interrupted
        use_computer_daemon_class_directly()
    except KeyboardInterrupt:
        print("\nExamples stopped by user")
