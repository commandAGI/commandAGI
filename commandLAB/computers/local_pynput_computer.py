import base64
import io
import subprocess
import tempfile
import time
import os
import datetime
from typing import Union, Optional, Literal

try:
    import mss
    from pynput import keyboard, mouse
    from pynput.keyboard import Key as PynputKey
    from pynput.keyboard import KeyCode as PynputKeyCode
    from pynput.mouse import Button as PynputButton
    from PIL import Image
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandLAB with the local extra:\n\npip install commandLAB[local]"
    )

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
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
    TypeAction,
    ComputerObservation,
)
from commandLAB._utils.config import APPDIR
from commandLAB._utils.screenshot import process_screenshot


# Pynput-specific mappings
def mouse_button_to_pynput(button: Union[MouseButton, str]) -> PynputButton:
    """Convert MouseButton to Pynput mouse button.
    
    Pynput uses Button enum for mouse buttons:
    Button.left = left button
    Button.middle = middle button
    Button.right = right button
    """
    if isinstance(button, str):
        button = MouseButton(button)
    
    # Pynput mouse button mapping
    pynput_button_mapping = {
        MouseButton.LEFT: PynputButton.left,
        MouseButton.MIDDLE: PynputButton.middle,
        MouseButton.RIGHT: PynputButton.right
    }
    
    return pynput_button_mapping.get(button, PynputButton.left)  # Default to left button if not found

def mouse_button_from_pynput(button: PynputButton) -> Optional[MouseButton]:
    """Convert Pynput mouse button to MouseButton.
    
    Maps from pynput.mouse.Button to our MouseButton enum.
    """
    # Pynput to MouseButton mapping
    pynput_to_mouse_button = {
        PynputButton.left: MouseButton.LEFT,
        PynputButton.middle: MouseButton.MIDDLE,
        PynputButton.right: MouseButton.RIGHT
    }
    
    return pynput_to_mouse_button.get(button)  # Returns None if not found

def keyboard_key_to_pynput(key: Union[KeyboardKey, str]) -> Union[PynputKey, PynputKeyCode]:
    """Convert KeyboardKey to Pynput key.
    
    Pynput uses Key enum for special keys and KeyCode for character keys.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)
    
    # Pynput-specific key mappings for special keys
    pynput_key_mapping = {
        # Special keys
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
        
        # Arrow keys
        KeyboardKey.UP: PynputKey.up,
        KeyboardKey.DOWN: PynputKey.down,
        KeyboardKey.LEFT: PynputKey.left,
        KeyboardKey.RIGHT: PynputKey.right,
        
        # Modifier keys
        KeyboardKey.SHIFT: PynputKey.shift,
        KeyboardKey.CTRL: PynputKey.ctrl,
        KeyboardKey.LCTRL: PynputKey.ctrl_l,
        KeyboardKey.RCTRL: PynputKey.ctrl_r,
        KeyboardKey.ALT: PynputKey.alt,
        KeyboardKey.LALT: PynputKey.alt_l,
        KeyboardKey.RALT: PynputKey.alt_r,
        KeyboardKey.META: PynputKey.cmd,  # Command/Windows key
        KeyboardKey.LMETA: PynputKey.cmd_l,
        KeyboardKey.RMETA: PynputKey.cmd_r,
        
        # Function keys
        KeyboardKey.F1: PynputKey.f1,
        KeyboardKey.F2: PynputKey.f2,
        KeyboardKey.F3: PynputKey.f3,
        KeyboardKey.F4: PynputKey.f4,
        KeyboardKey.F5: PynputKey.f5,
        KeyboardKey.F6: PynputKey.f6,
        KeyboardKey.F7: PynputKey.f7,
        KeyboardKey.F8: PynputKey.f8,
        KeyboardKey.F9: PynputKey.f9,
        KeyboardKey.F10: PynputKey.f10,
        KeyboardKey.F11: PynputKey.f11,
        KeyboardKey.F12: PynputKey.f12,
    }
    
    # Check if it's a special key
    if key in pynput_key_mapping:
        return pynput_key_mapping[key]
    
    # For letter keys and number keys, create a KeyCode
    return PynputKeyCode.from_char(key.value)

def keyboard_key_from_pynput(key) -> Optional[KeyboardKey]:
    """Convert Pynput key to KeyboardKey.
    
    Maps from pynput.keyboard.Key or KeyCode to our KeyboardKey enum.
    """
    # Handle character keys (KeyCode objects)
    if hasattr(key, 'char') and key.char:
        # Try to find a matching key in KeyboardKey
        for k in KeyboardKey:
            if k.value == key.char:
                return k
        return None
    
    # Handle special keys (Key enum values)
    # Pynput Key to KeyboardKey mapping
    pynput_to_keyboard_key = {
        PynputKey.enter: KeyboardKey.ENTER,
        PynputKey.tab: KeyboardKey.TAB,
        PynputKey.space: KeyboardKey.SPACE,
        PynputKey.backspace: KeyboardKey.BACKSPACE,
        PynputKey.delete: KeyboardKey.DELETE,
        PynputKey.esc: KeyboardKey.ESCAPE,
        PynputKey.home: KeyboardKey.HOME,
        PynputKey.end: KeyboardKey.END,
        PynputKey.page_up: KeyboardKey.PAGE_UP,
        PynputKey.page_down: KeyboardKey.PAGE_DOWN,
        PynputKey.up: KeyboardKey.UP,
        PynputKey.down: KeyboardKey.DOWN,
        PynputKey.left: KeyboardKey.LEFT,
        PynputKey.right: KeyboardKey.RIGHT,
        PynputKey.shift: KeyboardKey.SHIFT,
        PynputKey.shift_l: KeyboardKey.SHIFT,
        PynputKey.shift_r: KeyboardKey.SHIFT,
        PynputKey.ctrl: KeyboardKey.CTRL,
        PynputKey.ctrl_l: KeyboardKey.LCTRL,
        PynputKey.ctrl_r: KeyboardKey.RCTRL,
        PynputKey.alt: KeyboardKey.ALT,
        PynputKey.alt_l: KeyboardKey.LALT,
        PynputKey.alt_r: KeyboardKey.RALT,
        PynputKey.cmd: KeyboardKey.META,
        PynputKey.cmd_l: KeyboardKey.LMETA,
        PynputKey.cmd_r: KeyboardKey.RMETA,
        PynputKey.f1: KeyboardKey.F1,
        PynputKey.f2: KeyboardKey.F2,
        PynputKey.f3: KeyboardKey.F3,
        PynputKey.f4: KeyboardKey.F4,
        PynputKey.f5: KeyboardKey.F5,
        PynputKey.f6: KeyboardKey.F6,
        PynputKey.f7: KeyboardKey.F7,
        PynputKey.f8: KeyboardKey.F8,
        PynputKey.f9: KeyboardKey.F9,
        PynputKey.f10: KeyboardKey.F10,
        PynputKey.f11: KeyboardKey.F11,
        PynputKey.f12: KeyboardKey.F12,
    }
    
    return pynput_to_keyboard_key.get(key)  # Returns None if not found


class LocalPynputComputer(BaseComputer):
    def __init__(self):
        super().__init__()
        self._sct = None
        self._temp_dir = None

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
        if not self._sct:
            self.logger.info("Initializing MSS screen capture")
            self._sct = mss.mss()
        if not self._temp_dir:
            self.logger.info("Creating temporary directory")
            self._temp_dir = tempfile.mkdtemp()
            
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
        return True

    def _stop(self):
        """Stop the local computer environment and pynput listeners."""
        if self._sct:
            self.logger.info("Closing MSS screen capture")
            self._sct.close()
            self._sct = None
        if self._temp_dir:
            self.logger.info("Cleaning up temporary directory")
            self._temp_dir = None
            
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
            
        self.logger.info("Local Pynput computer stopped successfully")
        return True

    def reset_state(self):
        """Reset environment and return initial observation"""
        self.logger.info("Resetting environment state (showing desktop)")
        # Show desktop to reset the environment state
        self.execute_keyboard_hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.META, KeyboardKey.D]))
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
        self.logger.debug(f"Mouse click detected: ({x}, {y}), button={button}, pressed={pressed}")
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

    def _get_screenshot(self, display_id: int = 0, format: Literal['base64', 'PIL', 'path'] = 'PIL') -> ScreenshotObservation:
        """Return a screenshot of the current state in the specified format.
        
        Args:
            display_id: Optional ID of the display to capture. Defaults to 0 (primary display).
            format: Format to return the screenshot in. Options are:
                - 'base64': Return the screenshot as a base64 encoded string
                - 'PIL': Return the screenshot as a PIL Image object
                - 'path': Save the screenshot to a file and return the path
        """
        # Capture screenshot using mss
        self.logger.debug(f"Capturing screenshot of display {display_id}")
        monitor = self._sct.monitors[display_id + 1]  # mss uses 1-based indexing
        screenshot = self._sct.grab(monitor)
        
        # Use the utility function to process the screenshot
        return process_screenshot(
            screenshot_data=screenshot,
            output_format=format,
            input_format='PIL',
            computer_name="pynput"
        )

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from pynput listener."""
        self.logger.debug(f"Getting mouse state: position={self._mouse_pos}, buttons={self._mouse_buttons}")
        return MouseStateObservation(
            buttons=self._mouse_buttons.copy(),
            position=self._mouse_pos
        )

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from pynput listener."""
        # Convert pynput keys to our KeyboardKey enum
        pressed_keys = {}
        for key in self._pressed_keys:
            kb_key = keyboard_key_from_pynput(key)
            if kb_key:
                pressed_keys[kb_key] = True
                
        self.logger.debug(f"Getting keyboard state: {pressed_keys}")
        return KeyboardStateObservation(keys=pressed_keys)

    def get_observation(self):
        """Get the current observation of the computer state."""
        screenshot = self.get_screenshot()
        mouse_state = self.get_mouse_state()
        keyboard_state = self.get_keyboard_state()
        
        return ComputerObservation(
            screenshot=screenshot,
            mouse_state=mouse_state,
            keyboard_state=keyboard_state
        )

    def _execute_command(self, action: CommandAction):
        """Execute a system command using subprocess."""
        self.logger.info(f"Executing command: {action.command}")
        result = subprocess.run(
            action.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=action.timeout if action.timeout is not None else 10,
        )
        if result.returncode == 0:
            self.logger.info("Command executed successfully")
        else:
            self.logger.warning(f"Command returned non-zero exit code: {result.returncode}")
            raise RuntimeError(f"Command returned non-zero exit code: {result.returncode}")

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction):
        """Execute key down for a keyboard key."""
        pynput_key = keyboard_key_to_pynput(action.key)
        self.logger.debug(f"Pressing key down: {action.key} (Pynput key: {pynput_key})")
        self._keyboard_controller.press(pynput_key)

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction):
        """Execute key release for a keyboard key."""
        pynput_key = keyboard_key_to_pynput(action.key)
        self.logger.debug(f"Releasing key: {action.key} (Pynput key: {pynput_key})")
        self._keyboard_controller.release(pynput_key)

    def _execute_type(self, action: TypeAction):
        """Type text using pynput."""
        self.logger.debug(f"Typing text: {action.text}")
        self._keyboard_controller.type(action.text)

    def _execute_mouse_move(self, action: MouseMoveAction):
        """Move mouse to specified coordinates using pynput."""
        self.logger.debug(f"Moving mouse to: ({action.x}, {action.y})")
        # pynput doesn't have a direct move duration parameter, so we simulate it
        if action.move_duration > 0:
            # Get current position
            current_x, current_y = self._mouse_controller.position
            
            # Calculate number of steps based on duration
            steps = max(int(action.move_duration * 60), 1)  # 60 steps per second
            
            # Calculate step size
            step_x = (action.x - current_x) / steps
            step_y = (action.y - current_y) / steps
            
            # Move in steps
            for i in range(steps):
                next_x = current_x + step_x * (i + 1)
                next_y = current_y + step_y * (i + 1)
                self._mouse_controller.position = (next_x, next_y)
                time.sleep(action.move_duration / steps)
        else:
            # Instant move
            self._mouse_controller.position = (action.x, action.y)

    def _execute_mouse_scroll(self, action: MouseScrollAction):
        """Scroll mouse using pynput."""
        self.logger.debug(f"Scrolling mouse by: {action.amount}")
        # pynput scroll is done with dx, dy values
        # Positive values scroll up, negative values scroll down
        self._mouse_controller.scroll(0, action.amount / 100)  # Scale to reasonable values

    def _execute_mouse_button_down(self, action: MouseButtonDownAction):
        """Press mouse button down using pynput."""
        pynput_button = mouse_button_to_pynput(action.button)
        self.logger.debug(f"Pressing mouse button down: {action.button} (Pynput button: {pynput_button})")
        self._mouse_controller.press(pynput_button)

    def _execute_mouse_button_up(self, action: MouseButtonUpAction):
        """Release mouse button using pynput."""
        pynput_button = mouse_button_to_pynput(action.button)
        self.logger.debug(f"Releasing mouse button: {action.button} (Pynput button: {pynput_button})")
        self._mouse_controller.release(pynput_button)

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction):
        """Press and release a keyboard key."""
        pynput_key = keyboard_key_to_pynput(action.key)
        self._keyboard_controller.press(pynput_key)
        time.sleep(action.duration)
        self._keyboard_controller.release(pynput_key)

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction):
        """Execute a keyboard hotkey using pynput's context manager."""
        # Convert all modifier keys except the last key
        modifier_keys = [keyboard_key_to_pynput(key) for key in action.keys[:-1]]
        final_key = keyboard_key_to_pynput(action.keys[-1])

        # Use pynput's context manager for pressed keys
        for modifier in modifier_keys:
            self._keyboard_controller.pressed(modifier)

        # Press and release the final key
        self._keyboard_controller.press(final_key)
        time.sleep(0.1)
        self._keyboard_controller.release(final_key)

    def _pause(self):
        """Pause the Pynput computer.
        
        For local Pynput, pausing doesn't have a specific implementation
        as it's running on the local machine.
        """
        self.logger.info("Pausing local Pynput computer (no-op)")
        # No specific pause implementation for local Pynput

    def _resume(self, timeout_hours: Optional[float] = None):
        """Resume the Pynput computer.
        
        For local Pynput, resuming doesn't have a specific implementation
        as it's running on the local machine.
        
        Args:
            timeout_hours: Not used for local Pynput implementation.
        """
        self.logger.info("Resuming local Pynput computer (no-op)")
        # No specific resume implementation for local Pynput

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the local Pynput instance.
        
        Local Pynput doesn't support video streaming.
        
        Returns:
            str: Empty string as local Pynput doesn't support video streaming.
        """
        self.logger.debug("Video streaming not supported for local Pynput computer")
        return ""

    def start_video_stream(self) -> bool:
        """Start the video stream for the local Pynput instance.
        
        Local Pynput doesn't support video streaming.
        
        Returns:
            bool: False as local Pynput doesn't support video streaming.
        """
        self.logger.debug("Video streaming not supported for local Pynput computer")
        return False

    def stop_video_stream(self) -> bool:
        """Stop the video stream for the local Pynput instance.
        
        Local Pynput doesn't support video streaming.
        
        Returns:
            bool: False as local Pynput doesn't support video streaming.
        """
        self.logger.debug("Video streaming not supported for local Pynput computer")
        return False
