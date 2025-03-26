from typing import Union

try:
    pass
except ImportError:
    raise ImportError(
        "The PigDev dependencies are not installed. Please install commandAGI with the pigdev extra:\n\npip install commandAGI[pigdev]"
    )

from commandAGI.types import (
    KeyboardKey,
)


def keyboard_key_to_pigdev(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to PigDev key name.

    PigDev uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # PigDev-specific key mappings
    pigdev_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "enter",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "escape",
        KeyboardKey.HOME: "home",
        KeyboardKey.END: "end",
        KeyboardKey.PAGE_UP: "pageup",
        KeyboardKey.PAGE_DOWN: "pagedown",
        # Arrow keys
        KeyboardKey.UP: "up",
        KeyboardKey.DOWN: "down",
        KeyboardKey.LEFT: "left",
        KeyboardKey.RIGHT: "right",
        # Modifier keys
        KeyboardKey.SHIFT: "shift",
        KeyboardKey.CTRL: "ctrl",
        KeyboardKey.LCTRL: "ctrl",  # PigDev may not distinguish between left/right
        KeyboardKey.RCTRL: "ctrl",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # PigDev may not distinguish between left/right
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "super",  # Command/Windows key is called "super" in PigDev
        KeyboardKey.LMETA: "super",  # PigDev may not distinguish between left/right
        KeyboardKey.RMETA: "super",
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
    return pigdev_key_mapping.get(key, key.value)
