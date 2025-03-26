from typing import Union

try:
    pass
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandAGI with the local extra:\n\npip install commandAGI[local]"
    )

from commandAGI.types import (
    MouseButton,
)


# PyAutoGUI-specific mappings
def mouse_button_to_pyautogui(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to PyAutoGUI button name.

    PyAutoGUI uses string names for mouse buttons:
    'left' = left button
    'middle' = middle button
    'right' = right button
    'primary' = primary button (usually left)
    'secondary' = secondary button (usually right)
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # PyAutoGUI mouse button mapping
    pyautogui_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right",
    }

    return pyautogui_button_mapping.get(
        button, "left"
    )  # Default to left button if not found
