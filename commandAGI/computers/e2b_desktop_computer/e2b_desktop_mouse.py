from typing import Union

try:
    pass
except ImportError:
    raise ImportError(
        "The E2B Desktop dependencies are not installed. Please install commandAGI with the e2b_desktop extra:\n\npip install commandAGI[e2b_desktop]"
    )

from commandAGI.types import (
    MouseButton,
)


# E2B Desktop-specific mappings
def mouse_button_to_e2b(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to E2B Desktop button name.

    E2B Desktop uses the following button names:
    'left' = left button
    'middle' = middle button
    'right' = right button
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # E2B Desktop mouse button mapping
    e2b_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right",
    }

    # Default to left button if not found
    return e2b_button_mapping.get(button, "left")
