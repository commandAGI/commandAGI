from typing import Union

try:
    pass
except ImportError:
    raise ImportError(
        "The Scrapybara dependencies are not installed. Please install commandAGI with the scrapybara extra:\n\npip install commandAGI[scrapybara]"
    )

from commandAGI.types import (
    KeyboardKey,
)


def keyboard_key_to_scrapybara(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to Scrapybara key name.

    Scrapybara uses specific key names that may differ from our standard KeyboardKey values.
    For hotkeys, Scrapybara uses the '+' separator (e.g., "ctrl+c").
    """
    if isinstance(key, str):
        key = KeyboardKey(key)

    # Scrapybara-specific key mappings
    scrapybara_key_mapping = {
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
        KeyboardKey.LCTRL: "ctrl",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RCTRL: "ctrl",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "meta",  # Command/Windows key
        KeyboardKey.LMETA: "meta",  # Scrapybara doesn't distinguish between left/right
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
    return scrapybara_key_mapping.get(key, key.value)
