import base64
import io
import subprocess
import tempfile
import time
from typing import Union, Optional

try:
    import mss
    from pynput import keyboard, mouse
    from pynput.keyboard import Key as PynputKey
    from pynput.keyboard import KeyCode as PynputKeyCode
    from pynput.mouse import Button as PynputButton
except ImportError:
    raise ImportError(
        "pynput is not installed. Please install commandLAB with the local extra:\n\npip install commandLAB[local]"
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
from PIL import Image


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
            self._sct = mss.mss()
        if not self._temp_dir:
            self._temp_dir = tempfile.mkdtemp()
            
        # Start the keyboard listener if not already running
        if self._keyboard_listener is None or not self._keyboard_listener.running:
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_keyboard_press,
                on_release=self._on_keyboard_release,
            )
            self._keyboard_listener.start()

        # Start the mouse listener if not already running
        if self._mouse_listener is None or not self._mouse_listener.running:
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )
            self._mouse_listener.start()
            
        return True

    def _stop(self):
        """Stop the local computer environment and pynput listeners."""
        if self._sct:
            self._sct.close()
            self._sct = None
        if self._temp_dir:
            self._temp_dir = None
            
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
            
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
            
        return True

    def reset_state(self):
        """Reset environment, initialize pynput listener threads, and return the initial observation."""
        # Use keyboard hotkey to simulate Win+D
        self.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.META, KeyboardKey.D])
        )
        time.sleep(1)  # Give Windows time to minimize

        # Make sure listeners are running
        self._start()

    def _on_keyboard_press(self, key):
        """Callback for when a key is pressed."""
        self._pressed_keys.add(key)

    def _on_keyboard_release(self, key):
        """Callback for when a key is released."""
        if key in self._pressed_keys:
            self._pressed_keys.remove(key)

    def _on_mouse_move(self, x, y):
        """Callback for mouse movement events."""
        self._mouse_pos = (x, y)

    def _on_mouse_click(self, x, y, button, pressed):
        """Callback for mouse click events."""
        converted = mouse_button_from_pynput(button)
        if converted is not None:
            self._mouse_buttons[converted] = pressed
        self._mouse_pos = (x, y)

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Callback for mouse scroll events. (Currently updates mouse position.)"""
        self._mouse_pos = (x, y)

    def _get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        screenshot = self._sct.grab(self._sct.monitors[1])  # Primary monitor
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return ScreenshotObservation(screenshot=b64_screenshot)

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return the mouse state collected via pynput listeners."""
        return MouseStateObservation(
            buttons=self._mouse_buttons,
            position=self._mouse_pos,
        )

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return the keyboard state collected via pynput listeners."""
        keys_state = {key: False for key in KeyboardKey}
        for pressed in self._pressed_keys:
            conv_key = keyboard_key_from_pynput(pressed)
            if conv_key is not None and conv_key in keys_state:
                keys_state[conv_key] = True
        return KeyboardStateObservation(keys=keys_state)

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

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command using subprocess."""
        try:
            result = subprocess.run(
                action.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=action.timeout if action.timeout is not None else 10,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error executing command: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key."""
        pynput_key = keyboard_key_to_pynput(action.key)
        self._keyboard_controller.press(pynput_key)
        return True

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key."""
        pynput_key = keyboard_key_to_pynput(action.key)
        self._keyboard_controller.release(pynput_key)
        return True

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using pynput keyboard controller."""
        self._keyboard_controller.type(action.text)
        return True

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse using pynput mouse controller."""
        # Smooth movement implementation
        start_x, start_y = self._mouse_pos
        steps = max(int(action.move_duration * 60), 1)  # 60 steps per second

        for step in range(1, steps + 1):
            t = step / steps
            current_x = int(start_x + (action.x - start_x) * t)
            current_y = int(start_y + (action.y - start_y) * t)
            self._mouse_controller.position = (current_x, current_y)
            if action.move_duration > 0:
                time.sleep(action.move_duration / steps)

        return True

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll using pynput mouse controller."""
        self._mouse_controller.scroll(0, int(action.amount))
        return True

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button using pynput mouse controller."""
        pynput_button = mouse_button_to_pynput(action.button)
        self._mouse_controller.press(pynput_button)
        return True

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using pynput mouse controller."""
        pynput_button = mouse_button_to_pynput(action.button)
        self._mouse_controller.release(pynput_button)
        return True

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Press and release a keyboard key."""
        pynput_key = keyboard_key_to_pynput(action.key)
        self._keyboard_controller.press(pynput_key)
        time.sleep(action.duration)
        self._keyboard_controller.release(pynput_key)
        return True

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
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

        return True
