class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

    @classmethod
    def is_valid_button(cls, button: str) -> bool:
        """Check if a string is a valid mouse button."""
        return button in [b.value for b in cls]
