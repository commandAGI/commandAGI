import typer
from commandLAB.daemon.server import ComputerDaemon
import uvicorn
import secrets
from typing import Type, Dict, Any
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



def main(port: int = 8000, backend: str = "pynput", **kwargs):
    # Configure computer backend
    computer_cls = (
        LocalPynputComputer if backend == "pynput" else LocalPyAutoGUIComputer
    )
    daemon = ComputerDaemon(computer_cls=computer_cls, computer_cls_kwargs=kwargs)

    print(f"Starting daemon on port {port}")
    print(f"API Token: {daemon.API_TOKEN}")
    daemon.start_server()


if __name__ == "__main__":
    typer.run(main)
