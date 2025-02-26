import json
import typer
from commandLAB.daemon.server import ComputerDaemon
import uvicorn
import secrets
from typing import Literal, Optional, Type, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.types import (
    CommandAction,
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


COMPUTER_CLS_OPTINOS = {
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
):
    print('Starting daemon...')

    additional_computer_cls_kwargs = json.loads(additional_computer_cls_kwargs_str)

    # Configure computer backend
    computer_cls = COMPUTER_CLS_OPTINOS[backend]
    
    # Create the computer instance
    computer = computer_cls(**additional_computer_cls_kwargs)
    
    # Pass the computer instance to the daemon
    daemon = ComputerDaemon(computer=computer, api_token=api_token)

    print(f"Starting daemon on port {port}")
    print(f"API Token: {daemon.api_token}")
    daemon.start_server(host=host, port=port)


if __name__ == "__main__":
    cli()
