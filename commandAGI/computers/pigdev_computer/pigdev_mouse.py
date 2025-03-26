from typing import Union

try:
    pass
except ImportError:
    raise ImportError(
        "The PigDev dependencies are not installed. Please install commandAGI with the pigdev extra:\n\npip install commandAGI[pigdev]"
    )

from commandAGI.types import (
    MouseButton,
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
