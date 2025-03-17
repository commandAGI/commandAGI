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


class LocalPynputComputer(LocalComputer):
    def __init__(self):
        super().__init__()
        # These will hold the listener objects and controllers
        self._keyboard_listener = None
        self._mouse_listener = None
        self._keyboard_controller = keyboard.Controller()
        self._mouse_controller = mouse.Controller()

        # State containers updated via pynput callbacks.
        self._pressed_keys = set()  # holds currently pressed keys (pynput key objects)
        self._mouse_buttons = {
            MouseButton.LEFT: False,
            MouseButton.MIDDLE: False,
            MouseButton.RIGHT: False,
        }
        self._mouse_pos = (0, 0)

    def _start(self):
        """Start the local computer environment with pynput listeners."""
        # Call parent _start method to initialize screen capture and temp
        # directory
        super()._start()

        # Start the keyboard listener if not already running
        if self._keyboard_listener is None or not self._keyboard_listener.running:
            self.logger.info("Starting keyboard listener")
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_keyboard_press,
                on_release=self._on_keyboard_release,
            )
            self._keyboard_listener.start()

        # Start the mouse listener if not already running
        if self._mouse_listener is None or not self._mouse_listener.running:
            self.logger.info("Starting mouse listener")
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )
            self._mouse_listener.start()

        self.logger.info("Local Pynput computer started successfully")

    def _stop(self):
        """Stop the local computer environment and pynput listeners."""
        # Stop the keyboard listener if running
        if self._keyboard_listener and self._keyboard_listener.running:
            self.logger.info("Stopping keyboard listener")
            self._keyboard_listener.stop()
            self._keyboard_listener = None

        # Stop the mouse listener if running
        if self._mouse_listener and self._mouse_listener.running:
            self.logger.info("Stopping mouse listener")
            self._mouse_listener.stop()
            self._mouse_listener = None

        # Call parent _stop method to clean up screen capture and temp
        # directory
        super()._stop()

    def reset_state(self):
        """Reset environment and return initial observation"""
        self.logger.info("Resetting environment state (showing desktop)")
        # Show desktop to reset the environment state
        self._hotkey([KeyboardKey.META, KeyboardKey.D])
        time.sleep(1)  # Give windows time to minimize

    def _on_keyboard_press(self, key):
        """Callback for keyboard press events."""
        self.logger.debug(f"Keyboard press detected: {key}")
        self._pressed_keys.add(key)

    def _on_keyboard_release(self, key):
        """Callback for keyboard release events."""
        self.logger.debug(f"Keyboard release detected: {key}")
        if key in self._pressed_keys:
            self._pressed_keys.remove(key)

    def _on_mouse_move(self, x, y):
        """Callback for mouse move events."""
        self.logger.debug(f"Mouse move detected: ({x}, {y})")
        self._mouse_pos = (x, y)

    def _on_mouse_click(self, x, y, button, pressed):
        """Callback for mouse click events."""
        self.logger.debug(
            f"Mouse click detected: ({x}, {y}), button={button}, pressed={pressed}"
        )
        # Map pynput button to our MouseButton enum
        if button == PynputButton.left:
            self._mouse_buttons[MouseButton.LEFT] = pressed
        elif button == PynputButton.middle:
            self._mouse_buttons[MouseButton.MIDDLE] = pressed
        elif button == PynputButton.right:
            self._mouse_buttons[MouseButton.RIGHT] = pressed

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Callback for mouse scroll events."""
        self.logger.debug(f"Mouse scroll detected: ({x}, {y}), dx={dx}, dy={dy}")
        # We don't track scroll state, just position

    def _get_mouse_position(self) -> tuple[int, int]:
        """Return current mouse position."""
        self.logger.debug(f"Getting mouse position: {self._mouse_pos}")
        return self._mouse_pos

    def _get_mouse_button_states(self) -> dict[str, bool]:
        """Return states of mouse buttons."""
        self.logger.debug(f"Getting mouse button states: {self._mouse_buttons}")
        return self._mouse_buttons.copy()

    def _get_keyboard_key_states(self) -> dict[str, bool]:
        """Return states of keyboard keys."""
        # Convert pynput keys to our KeyboardKey enum
        pressed_keys = {}
        for key in self._pressed_keys:
            kb_key = keyboard_key_from_pynput(key)
            if kb_key:
                pressed_keys[kb_key] = True

        self.logger.debug(f"Getting keyboard key states: {pressed_keys}")
        return pressed_keys

    def _keydown(self, key: KeyboardKey):
        """Execute key down for a keyboard key."""
        pynput_key = keyboard_key_to_pynput(key)
        self.logger.debug(f"Pressing key down: {key} (Pynput key: {pynput_key})")
        self._keyboard_controller.press(pynput_key)

    def _keyup(self, key: KeyboardKey):
        """Execute key release for a keyboard key."""
        pynput_key = keyboard_key_to_pynput(key)
        self.logger.debug(f"Releasing key: {key} (Pynput key: {pynput_key})")
        self._keyboard_controller.release(pynput_key)

    def _type(self, text: str):
        """Type text using pynput."""
        self.logger.debug(f"Typing text: {text}")
        self._keyboard_controller.type(text)

    def _move(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to specified coordinates using pynput."""
        self.logger.debug(f"Moving mouse to: ({x}, {y})")
        # pynput doesn't have a direct move duration parameter, so we simulate
        # it
        if move_duration > 0:
            # Get current position
            current_x, current_y = self._mouse_controller.position

            # Calculate number of steps based on duration
            # 60 steps per second
            steps = max(int(move_duration * 60), 1)

            # Calculate step size
            step_x = (x - current_x) / steps
            step_y = (y - current_y) / steps

            # Move in steps
            for i in range(steps):
                next_x = current_x + step_x * (i + 1)
                next_y = current_y + step_y * (i + 1)
                self._mouse_controller.position = (next_x, next_y)
                time.sleep(move_duration / steps)
        else:
            # Instant move
            self._mouse_controller.position = (x, y)

    def _scroll(self, amount: float):
        """Scroll mouse using pynput."""
        self.logger.debug(f"Scrolling mouse by: {amount}")
        # pynput scroll is done with dx, dy values
        # Positive values scroll up, negative values scroll down
        self._mouse_controller.scroll(0, amount / 100)  # Scale to reasonable values

    def _mouse_down(self, button: MouseButton = MouseButton.LEFT):
        """Press mouse button down using pynput."""
        pynput_button = mouse_button_to_pynput(button)
        self.logger.debug(
            f"Pressing mouse button down: {button} (Pynput button: {pynput_button})"
        )
        self._mouse_controller.press(pynput_button)

    def _mouse_up(self, button: MouseButton = MouseButton.LEFT):
        """Release mouse button using pynput."""
        pynput_button = mouse_button_to_pynput(button)
        self.logger.debug(
            f"Releasing mouse button: {button} (Pynput button: {pynput_button})"
        )
        self._mouse_controller.release(pynput_button)

    def _keypress(self, key: KeyboardKey, duration: float = 0.1):
        """Press and release a keyboard key."""
        pynput_key = keyboard_key_to_pynput(key)
        self._keyboard_controller.press(pynput_key)
        time.sleep(duration)
        self._keyboard_controller.release(pynput_key)

    def _hotkey(self, keys: List[KeyboardKey]):
        """Execute a keyboard hotkey using pynput's context manager."""
        # Convert all modifier keys except the last key
        modifier_keys = [keyboard_key_to_pynput(key) for key in keys[:-1]]
        final_key = keyboard_key_to_pynput(keys[-1])

        # Use pynput's context manager for pressed keys
        for modifier in modifier_keys:
            self._keyboard_controller.pressed(modifier)

        # Press and release the final key
        self._keyboard_controller.press(final_key)
        time.sleep(0.1)
        self._keyboard_controller.release(final_key)
