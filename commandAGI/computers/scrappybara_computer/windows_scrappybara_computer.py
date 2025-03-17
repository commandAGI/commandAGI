import base64
import datetime
import io
import os
import tempfile
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Literal, Optional, Union

try:
    import scrapybara
    from PIL import Image
except ImportError:
    raise ImportError(
        "The Scrapybara dependencies are not installed. Please install commandAGI with the scrapybara extra:\n\npip install commandAGI[scrapybara]"
    )

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI.computers.base_computer import BaseComputer, BaseComputerFile
from commandAGI.types import (
    ClickAction,
    DoubleClickAction,
    DragAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    RunProcessAction,
    ScreenshotObservation,
    ShellCommandAction,
    TypeAction,
)


class WindowsScrapybaraComputer(BaseScrapybaraComputer):
    """Scrapybara computer specifically for Windows instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _start(self):
        """Start a Windows Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                client = scrapybara.Client(api_key=self.api_key)
            else:
                client = scrapybara.Client()

            # Start a Windows instance
            self.client = client.start_windows()

    def _shell(
        self,
        command: str,
        timeout: Optional[float] = None,
        executable: Optional[str] = None,
    ):
        """Execute a command in the Windows instance.

        Note: Windows instances don't support bash commands directly.
        This implementation uses computer actions to open cmd and type commands.
        """
        # Open Windows Run dialog
        self.client.computer(action="key", text="meta+r")
        self.client.computer(action="wait")  # Wait for Run dialog to open

        # Type cmd and press Enter
        self.client.computer(action="type", text="cmd")
        self.client.computer(action="key", text="enter")
        self.client.computer(action="wait")  # Wait for cmd to open

        # Type the command and press Enter
        self.client.computer(action="type", text=command)
        self.client.computer(action="key", text="enter")

        # Wait for command to complete if timeout is specified
        if timeout:
            self.client.computer(action="wait")
