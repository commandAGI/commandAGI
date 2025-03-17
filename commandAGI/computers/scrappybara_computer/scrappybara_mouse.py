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


# Scrapybara-specific mappings
def mouse_button_to_scrapybara(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to Scrapybara button action.

    Scrapybara uses specific action names for mouse buttons:
    - "left_click" for left button
    - "right_click" for right button
    - "middle_click" for middle button
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # Scrapybara mouse button mapping
    scrapybara_button_mapping = {
        MouseButton.LEFT: "left_click",
        MouseButton.MIDDLE: "middle_click",
        MouseButton.RIGHT: "right_click",
    }

    return scrapybara_button_mapping.get(
        button, "left_click"
    )  # Default to left click if not found
