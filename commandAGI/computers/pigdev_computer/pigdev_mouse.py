import base64
import datetime
import io
import os
import tempfile
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Literal, Optional, Union

try:
    from pig import Client
    from PIL import Image
except ImportError:
    raise ImportError(
        "The PigDev dependencies are not installed. Please install commandAGI with the pigdev extra:\n\npip install commandAGI[pigdev]"
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


# PigDev-specific mappings
def mouse_button_to_pigdev(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to PigDev button name.

    PigDev uses string names for mouse buttons that match our MouseButton values.
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # PigDev mouse button mapping
    pigdev_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right",
    }

    return pigdev_button_mapping.get(
        button, "left"
    )  # Default to left button if not found
