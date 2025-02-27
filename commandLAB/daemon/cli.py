import json
import typer
from commandLAB.daemon.server import ComputerDaemon
import uvicorn
import secrets
import signal
import sys
import time
from typing import Literal, Optional, Type, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.types import (
    ShellCommandAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)


cli = typer.Typer()


COMPUTER_CLS_OPTIONS = {
    "pynput": LocalPynputComputer,
    "pyautogui": LocalPyAutoGUIComputer,
}

@cli.command()
def start(
    host: Optional[str] = typer.Option(default="0.0.0.0", help="The host to bind the daemon to"),
    port: Optional[int] = typer.Option(default=8000, help="The port to bind the daemon to"),
    api_token: Optional[str] = typer.Option(default=None, help="The API token to use for the daemon"),
    backend: Optional[str] = typer.Option(default="pynput", help="The backend to use for the computer. Options: pynput, pyautogui"),
    additional_computer_cls_kwargs_str: Optional[str] = typer.Option(default='{}', help="Additional keyword arguments to pass to the computer class"),
    vnc_windows_executables_str: Optional[str] = typer.Option(default=None, help="Comma-separated list of VNC executables to search for on Windows"),
    vnc_unix_executables_str: Optional[str] = typer.Option(default=None, help="Comma-separated list of VNC executables to search for on Unix-like systems"),
    vnc_start_commands_str: Optional[str] = typer.Option(default=None, help="JSON string mapping executable names to command templates for starting VNC"),
    vnc_stop_commands_str: Optional[str] = typer.Option(default=None, help="JSON string mapping executable names to command templates for stopping VNC"),
    rdp_use_system_commands: bool = typer.Option(default=True, help="Whether to use system commands for RDP on Windows"),
    mcp_server_name: Optional[str] = typer.Option(default="CommandLAB MCP Server", help="The name of the MCP server"),
    http_server: bool = typer.Option(default=True, help="Whether to start the HTTP server"),
    mcp_server: bool = typer.Option(default=False, help="Whether to start the MCP server"),
):
    print('Starting daemon...')

    additional_computer_cls_kwargs = json.loads(additional_computer_cls_kwargs_str)

    # Configure computer backend
    computer_cls = COMPUTER_CLS_OPTIONS[backend]
    
    # Create the computer instance
    computer = computer_cls(**additional_computer_cls_kwargs)
    
    # Parse VNC and RDP configuration options
    vnc_windows_executables = None
    if vnc_windows_executables_str:
        vnc_windows_executables = [exe.strip() for exe in vnc_windows_executables_str.split(',')]
    
    vnc_unix_executables = None
    if vnc_unix_executables_str:
        vnc_unix_executables = [exe.strip() for exe in vnc_unix_executables_str.split(',')]
    
    vnc_start_commands = None
    if vnc_start_commands_str:
        vnc_start_commands = json.loads(vnc_start_commands_str)
    
    vnc_stop_commands = None
    if vnc_stop_commands_str:
        vnc_stop_commands = json.loads(vnc_stop_commands_str)
    
    # Pass the computer instance and configuration to the daemon
    daemon = ComputerDaemon(
        computer=computer, 
        api_token=api_token,
        vnc_windows_executables=vnc_windows_executables,
        vnc_unix_executables=vnc_unix_executables,
        vnc_start_commands=vnc_start_commands,
        vnc_stop_commands=vnc_stop_commands,
        rdp_use_system_commands=rdp_use_system_commands,
        mcp_server_name=mcp_server_name,
    )

    print(f"API Token: {daemon._api_token}")
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down servers gracefully...")
        if mcp_server:
            print("Stopping MCP server...")
            daemon.stop_mcp_server()
        if http_server:
            print("Stopping HTTP server...")
            daemon.stop_fastapi_server()
        print("Shutdown complete.")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Start servers based on flags
    if http_server:
        print(f"Starting HTTP server on {host}:{port}")
        success, message = daemon.start_fastapi_server(host=host, port=port)
        if not success:
            print(f"Failed to start HTTP server: {message}")
            return
        print(message)
    
    if mcp_server:
        print("Starting MCP server...")
        success, message = daemon.start_mcp_server()
        if not success:
            print(f"Failed to start MCP server: {message}")
            if not http_server:
                return
        else:
            print(message)
    
    # Keep the main thread alive to handle signals
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # This will be caught by our signal handler
        pass


if __name__ == "__main__":
    cli()
