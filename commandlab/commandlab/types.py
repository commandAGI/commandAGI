from typing import Union

from pynput.keyboard import Key as PynputKey
from pynput.keyboard import KeyCode as PynputKeyCode
from pynput.mouse import Button as PynputButton

from commandlab.src.commandlab_core.types import KeyboardKey, MouseButton

# Backend-specific mappings
_VNC_MOUSE_BUTTON_MAPPING = {"left": 1, "middle": 2, "right": 3}

_PYAUTOGUI_MOUSE_BUTTON_MAPPING = {"left": "left", "middle": "middle", "right": "right"}

_PYNPUT_MOUSE_BUTTON_MAPPING = {
    "left": PynputButton.left,
    "middle": PynputButton.middle,
    "right": PynputButton.right,
}


@classmethod
def mouse_button_to_vnc(cls, button: Union["MouseButton", str]) -> int:
    """
    Convert a standard mouse button into the VNC-compatible code.
    For VNC, left=1, middle=2, right=3.
    """
    # If a MouseButton enum was passed, use its value; otherwise assume a string was passed.
    button_val = button.value if isinstance(button, cls) else button
    return _VNC_MOUSE_BUTTON_MAPPING.get(button_val, 1)


@classmethod
def mouse_button_to_pyautogui(cls, button: Union["MouseButton", str]) -> str:
    """
    Convert a standard mouse button into the PyAutoGUI-compatible string.
    """
    button_val = button.value if isinstance(button, cls) else button
    return _PYAUTOGUI_MOUSE_BUTTON_MAPPING.get(button_val, "left")


@classmethod
def mouse_button_to_pynput(cls, button: Union["MouseButton", str]) -> PynputButton:
    """Convert a standard mouse button to Pynput PynputButton"""
    button_val = button.value if isinstance(button, cls) else button
    return _PYNPUT_MOUSE_BUTTON_MAPPING.get(button_val, PynputButton.left)


@classmethod
def mouse_button_from_pynput(cls, button) -> "MouseButton":
    if button == PynputButton.left:
        return cls.LEFT
    elif button == PynputButton.middle:
        return cls.MIDDLE
    elif button == PynputButton.right:
        return cls.RIGHT
    return None


# Backend specific mappings
_VNC_SPECIAL_KEYBOARD_KEY_MAPPINGS = {
    KeyboardKey.META: "meta",
    KeyboardKey.LMETA: "meta",
    KeyboardKey.RMETA: "meta",
    KeyboardKey.CTRL: "control",
    KeyboardKey.LCTRL: "control",
    KeyboardKey.RCTRL: "control",
    KeyboardKey.ALT: "alt",
    KeyboardKey.LALT: "alt",
    KeyboardKey.RALT: "alt",
}

_PYAUTOGUI_SPECIAL_KEYBOARD_KEY_MAPPINGS = {
    KeyboardKey.META: "meta",
    KeyboardKey.LMETA: "meta",
    KeyboardKey.RMETA: "meta",
    KeyboardKey.CTRL: "ctrl",
    KeyboardKey.LCTRL: "ctrl",
    KeyboardKey.RCTRL: "ctrl",
    KeyboardKey.ALT: "alt",
    KeyboardKey.LALT: "alt",
    KeyboardKey.RALT: "alt",
}

_PYNPUT_SPECIAL_KEYBOARD_KEY_MAPPINGS = {
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
    KeyboardKey.UP: PynputKey.up,
    KeyboardKey.DOWN: PynputKey.down,
    KeyboardKey.LEFT: PynputKey.left,
    KeyboardKey.RIGHT: PynputKey.right,
    KeyboardKey.SHIFT: PynputKey.shift,
    KeyboardKey.SHIFT: PynputKey.shift_l,
    KeyboardKey.SHIFT: PynputKey.shift_r,
    KeyboardKey.LCTRL: PynputKey.ctrl_l,
    KeyboardKey.RCTRL: PynputKey.ctrl_r,
    KeyboardKey.CTRL: PynputKey.ctrl,
    KeyboardKey.LALT: PynputKey.alt_l,
    KeyboardKey.RALT: PynputKey.alt_r,
    KeyboardKey.ALT: PynputKey.alt,
    KeyboardKey.LMETA: PynputKey.cmd_l,
    KeyboardKey.RMETA: PynputKey.cmd_r,
    KeyboardKey.META: PynputKey.cmd,
}


@classmethod
def keyboard_key_to_vnc(cls, key: Union["KeyboardKey", str]) -> str:
    """Convert a standard key to VNC format"""
    key_val = key.value if isinstance(key, cls) else key
    if key_val in _VNC_SPECIAL_KEYBOARD_KEY_MAPPINGS:
        return _VNC_SPECIAL_KEYBOARD_KEY_MAPPINGS[str(key_val)]
    return key_val


@classmethod
def keyboard_key_to_pyautogui(cls, key: Union["KeyboardKey", str]) -> str:
    """Convert a standard key to PyAutoGUI format"""
    key_val = key.value if isinstance(key, cls) else key
    if key_val in _PYAUTOGUI_SPECIAL_KEYBOARD_KEY_MAPPINGS:
        return _PYAUTOGUI_SPECIAL_KEYBOARD_KEY_MAPPINGS[str(key_val)]
    return key_val


@classmethod
def keyboard_key_to_pynput(cls, key: Union["KeyboardKey", str]) -> PynputKey:
    """Convert a standard key to Pynput format"""
    key_val = key.value if isinstance(key, cls) else key
    if key_val in _PYNPUT_SPECIAL_KEYBOARD_KEY_MAPPINGS:
        return _PYNPUT_SPECIAL_KEYBOARD_KEY_MAPPINGS[str(key_val)]
    return key_val


@classmethod
def keyboard_key_from_pynput(cls, key) -> "KeyboardKey":
    # Find the KeyboardKey enum value by looking up the pynput key in the mapping
    for enum_key, pynput_key in _PYNPUT_SPECIAL_KEYBOARD_KEY_MAPPINGS.items():
        if pynput_key == key:
            return enum_key
    # Handle character keys
    if isinstance(key, PynputKeyCode) and key.char:
        try:
            return cls(key.char.lower())
        except ValueError:
            return None
    return None
