from abc import ABC, abstractmethod
from typing import Optional
from commandagi_j2.envs.computer_types import (
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)

class Computer(ABC):
    """Base class defining the interface for computer interactions."""

    @abstractmethod
    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        """Capture and return a screenshot."""
        pass

    @abstractmethod
    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        """Get current mouse state."""
        pass

    @abstractmethod
    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        """Get current keyboard state."""
        pass

    @abstractmethod
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command."""
        pass

    @abstractmethod
    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Press down a keyboard key."""
        pass

    @abstractmethod
    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Release a keyboard key."""
        pass

    @abstractmethod
    def execute_type(self, action: TypeAction) -> bool:
        """Type text."""
        pass

    @abstractmethod
    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse cursor."""
        pass

    @abstractmethod
    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse wheel."""
        pass

    @abstractmethod
    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press down a mouse button."""
        pass

    @abstractmethod
    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release a mouse button."""
        pass

    def close(self):
        """Clean up resources. Override if needed."""
        pass 