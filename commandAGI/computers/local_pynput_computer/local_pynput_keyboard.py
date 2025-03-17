import base64
import datetime
import io
import os
import subprocess
import tempfile
import time
from typing import List, Literal, Optional, Union

try:
    import mss
    from PIL import Image
    from pynput import keyboard, mouse
    from pynput.keyboard import Key as PynputKey
    from pynput.keyboard import KeyCode as PynputKeyCode
    from pynput.mouse import Button as PynputButton
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandAGI with the local extra:\n\npip install commandAGI[local]"
    )

from commandAGI._internal.config import APPDIR
from commandAGI._utils.image import process_screenshot
from commandAGI.computers.local_computer import LocalComputer
from commandAGI.types import (
    ComputerObservation,
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
    ScreenshotObservation,
    ShellCommandAction,
    TypeAction,
)


def keyboard_key_to_pynput(
    key: Union[KeyboardKey, str],
) -> Union[PynputKey, PynputKeyCode]:
    """Convert KeyboardKey to Pynput key.

    Pynput uses Key enum for special keys and KeyCode for character keys.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # Pynput-specific key mappings for special keys
    pynput_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: PynputKey.enter,
        KeyboardKey.TAB: PynputKey.tab,
        KeyboardKey.SPACE: PynputKey.space,
        KeyboardKey.BACKSPACE: PynputKey.backspace,
        KeyboardKey.DELETE: PynputKey.delete,
        KeyboardKey.ESCAPE: PynputKey.esc,
        KeyboardKey.HOME: PynputKey.home,
        KeyboardKey.END: PynputKey.end,
        KeyboardKey.PAGE_UP: PynputKey.page_up,
        KeyboardKey.PAGE_DOWN: PynputKey.page_down,
        # Arrow keys
        KeyboardKey.UP: PynputKey.up,
        KeyboardKey.DOWN: PynputKey.down,
        KeyboardKey.LEFT: PynputKey.left,
        KeyboardKey.RIGHT: PynputKey.right,
        # Modifier keys
        KeyboardKey.SHIFT: PynputKey.shift,
        KeyboardKey.CTRL: PynputKey.ctrl,
        KeyboardKey.LCTRL: PynputKey.ctrl_l,
        KeyboardKey.RCTRL: PynputKey.ctrl_r,
        KeyboardKey.ALT: PynputKey.alt,
        KeyboardKey.LALT: PynputKey.alt_l,
        KeyboardKey.RALT: PynputKey.alt_r,
        KeyboardKey.META: PynputKey.cmd,  # Command/Windows key
        KeyboardKey.LMETA: PynputKey.cmd_l,
        KeyboardKey.RMETA: PynputKey.cmd_r,
        # Function keys
        KeyboardKey.F1: PynputKey.f1,
        KeyboardKey.F2: PynputKey.f2,
        KeyboardKey.F3: PynputKey.f3,
        KeyboardKey.F4: PynputKey.f4,
        KeyboardKey.F5: PynputKey.f5,
        KeyboardKey.F6: PynputKey.f6,
        KeyboardKey.F7: PynputKey.f7,
        KeyboardKey.F8: PynputKey.f8,
        KeyboardKey.F9: PynputKey.f9,
        KeyboardKey.F10: PynputKey.f10,
        KeyboardKey.F11: PynputKey.f11,
        KeyboardKey.F12: PynputKey.f12,
    }

    # Check if it's a special key
    if key in pynput_key_mapping:
        return pynput_key_mapping[key]

    # For letter keys and number keys, create a KeyCode
    return PynputKeyCode.from_char(key.value)


def keyboard_key_from_pynput(key) -> Optional[KeyboardKey]:
    """Convert Pynput key to KeyboardKey.

    Maps from pynput.keyboard.Key or KeyCode to our KeyboardKey enum.
    """
    # Handle character keys (KeyCode objects)
    if hasattr(key, "char") and key.char:
        # Try to find a matching key in KeyboardKey
        for k in KeyboardKey:
            if k.value == key.char:
                return k
        return None

    # Handle special keys (Key enum values)
    # Pynput Key to KeyboardKey mapping
    pynput_to_keyboard_key = {
        PynputKey.enter: KeyboardKey.ENTER,
        PynputKey.tab: KeyboardKey.TAB,
        PynputKey.space: KeyboardKey.SPACE,
        PynputKey.backspace: KeyboardKey.BACKSPACE,
        PynputKey.delete: KeyboardKey.DELETE,
        PynputKey.esc: KeyboardKey.ESCAPE,
        PynputKey.home: KeyboardKey.HOME,
        PynputKey.end: KeyboardKey.END,
        PynputKey.page_up: KeyboardKey.PAGE_UP,
        PynputKey.page_down: KeyboardKey.PAGE_DOWN,
        PynputKey.up: KeyboardKey.UP,
        PynputKey.down: KeyboardKey.DOWN,
        PynputKey.left: KeyboardKey.LEFT,
        PynputKey.right: KeyboardKey.RIGHT,
        PynputKey.shift: KeyboardKey.SHIFT,
        PynputKey.shift_l: KeyboardKey.SHIFT,
        PynputKey.shift_r: KeyboardKey.SHIFT,
        PynputKey.ctrl: KeyboardKey.CTRL,
        PynputKey.ctrl_l: KeyboardKey.LCTRL,
        PynputKey.ctrl_r: KeyboardKey.RCTRL,
        PynputKey.alt: KeyboardKey.ALT,
        PynputKey.alt_l: KeyboardKey.LALT,
        PynputKey.alt_r: KeyboardKey.RALT,
        PynputKey.cmd: KeyboardKey.META,
        PynputKey.cmd_l: KeyboardKey.LMETA,
        PynputKey.cmd_r: KeyboardKey.RMETA,
        PynputKey.f1: KeyboardKey.F1,
        PynputKey.f2: KeyboardKey.F2,
        PynputKey.f3: KeyboardKey.F3,
        PynputKey.f4: KeyboardKey.F4,
        PynputKey.f5: KeyboardKey.F5,
        PynputKey.f6: KeyboardKey.F6,
        PynputKey.f7: KeyboardKey.F7,
        PynputKey.f8: KeyboardKey.F8,
        PynputKey.f9: KeyboardKey.F9,
        PynputKey.f10: KeyboardKey.F10,
        PynputKey.f11: KeyboardKey.F11,
        PynputKey.f12: KeyboardKey.F12,
    }

    return pynput_to_keyboard_key.get(key)  # Returns None if not found
