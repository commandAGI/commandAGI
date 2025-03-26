from typing import Union

try:
    pass
except ImportError:
    raise ImportError(
        "The Scrapybara dependencies are not installed. Please install commandAGI with the scrapybara extra:\n\npip install commandAGI[scrapybara]"
    )

from commandAGI.types import (
    MouseButton,
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
