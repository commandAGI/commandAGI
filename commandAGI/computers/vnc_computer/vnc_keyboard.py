import base64
import datetime
import io
import os
import tempfile
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Literal, Optional, Union

try:
    import vncdotool.api as vnc
    from PIL import Image

    # Try to import paramiko for SFTP file transfer
    try:
        import paramiko

        SFTP_AVAILABLE = True
    except ImportError:
        SFTP_AVAILABLE = False
except ImportError:
    raise ImportError(
        "The VNC dependencies are not installed. Please install commandAGI with the vnc extra:\n\npip install commandAGI[vnc]"
    )

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI.computers.base_computer import BaseComputer, BaseComputerFile
from commandAGI.types import (
    KeyboardKey,
    KeyboardKeyDownAction,
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



def keyboard_key_to_vnc(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to VNC key name.

    VNC uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # VNC-specific key mappings
    vnc_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "return",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "escape",
        KeyboardKey.HOME: "home",
        KeyboardKey.END: "end",
        KeyboardKey.PAGE_UP: "page_up",
        KeyboardKey.PAGE_DOWN: "page_down",
        # Arrow keys
        KeyboardKey.UP: "up",
        KeyboardKey.DOWN: "down",
        KeyboardKey.LEFT: "left",
        KeyboardKey.RIGHT: "right",
        # Modifier keys
        KeyboardKey.SHIFT: "shift",
        KeyboardKey.CTRL: "control",
        KeyboardKey.LCTRL: "control",
        KeyboardKey.RCTRL: "control",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "meta",
        KeyboardKey.LMETA: "meta",
        KeyboardKey.RMETA: "meta",
        # Function keys
        KeyboardKey.F1: "f1",
        KeyboardKey.F2: "f2",
        KeyboardKey.F3: "f3",
        KeyboardKey.F4: "f4",
        KeyboardKey.F5: "f5",
        KeyboardKey.F6: "f6",
        KeyboardKey.F7: "f7",
        KeyboardKey.F8: "f8",
        KeyboardKey.F9: "f9",
        KeyboardKey.F10: "f10",
        KeyboardKey.F11: "f11",
        KeyboardKey.F12: "f12",
    }

    # For letter keys and number keys, use the value directly
    return vnc_key_mapping.get(key, key.value)
