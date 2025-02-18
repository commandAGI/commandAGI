import subprocess
import time
import mss
from PIL import Image
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
import tempfile
import os

# Import pynput for keyboard and mouse listeners
from pynput import keyboard, mouse
from commandagi_j2.envs.computer_types import (
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    MouseButton,
)
from commandagi_j2.envs.computer_types import (
    CommandAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)
from commandagi_j2.envs.computer_types import KeyboardHotkeyAction


class LocalPynputComputeEnv(BaseComputerEnv):
    def __init__(self):
        super().__init__()
        self.sct = mss.mss()
        self.last_screenshot = None
        self.temp_dir = tempfile.mkdtemp()

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

    def reset(self):
        """Reset environment, initialize pynput listener threads, and return the initial observation."""
        # Use keyboard hotkey to simulate Win+D
        self.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.META, KeyboardKey.D])
        )
        time.sleep(1)  # Give Windows time to minimize

        # Start the keyboard listener if not already running.
        if self._keyboard_listener is None or not self._keyboard_listener.running:
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_keyboard_press,
                on_release=self._on_keyboard_release,
            )
            self._keyboard_listener.start()

        # Start the mouse listener if not already running.
        if self._mouse_listener is None or not self._mouse_listener.running:
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )
            self._mouse_listener.start()

        return self.get_observation()

    def close(self):
        """Clean up resources, including stopping pynput listeners."""
        self.sct.close()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()

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
        converted = MouseButton.from_pynput(button)
        if converted is not None:
            self._mouse_buttons[converted] = pressed
        self._mouse_pos = (x, y)

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Callback for mouse scroll events. (Currently updates mouse position.)"""
        self._mouse_pos = (x, y)

    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state using mss."""
        output_path = os.path.join(self.temp_dir, "screenshot.png")
        screenshot = self.sct.grab(self.sct.monitors[1])  # Primary monitor
        Image.frombytes("RGB", screenshot.size, screenshot.rgb).save(output_path)
        self.last_screenshot = output_path
        return ScreenshotObservation(screenshot=output_path)

    def get_mouse_state(self) -> MouseStateObservation:
        """Return the mouse state collected via pynput listeners."""
        return MouseStateObservation(
            buttons=self._mouse_buttons,
            position=self._mouse_pos,
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return the keyboard state collected via pynput listeners."""
        keys_state = {key: False for key in KeyboardKey}
        for pressed in self._pressed_keys:
            conv_key = KeyboardKey.from_pynput(pressed)
            if conv_key is not None and conv_key in keys_state:
                keys_state[conv_key] = True
        return KeyboardStateObservation(keys=keys_state)

    def execute_command(self, action: CommandAction) -> bool:
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

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key."""
        pynput_key = KeyboardKey.to_pynput(action.key)
        self._keyboard_controller.press(pynput_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key."""
        pynput_key = KeyboardKey.to_pynput(action.key)
        self._keyboard_controller.release(pynput_key)
        return True

    def execute_type(self, action: TypeAction) -> bool:
        """Type text using pynput keyboard controller."""
        self._keyboard_controller.type(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
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

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll using pynput mouse controller."""
        self._mouse_controller.scroll(0, int(action.amount))
        return True

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button using pynput mouse controller."""
        pynput_button = MouseButton.to_pynput(action.button)
        self._mouse_controller.press(pynput_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using pynput mouse controller."""
        pynput_button = MouseButton.to_pynput(action.button)
        self._mouse_controller.release(pynput_button)
        return True

    def execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Press and release a keyboard key."""
        pynput_key = KeyboardKey.to_pynput(action.key)
        self._keyboard_controller.press(pynput_key)
        time.sleep(action.duration)
        self._keyboard_controller.release(pynput_key)
        return True

    def execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey using pynput's context manager."""
        # Convert all modifier keys except the last key
        modifier_keys = [KeyboardKey.to_pynput(key) for key in action.keys[:-1]]
        final_key = KeyboardKey.to_pynput(action.keys[-1])

        # Use pynput's context manager for pressed keys
        for modifier in modifier_keys:
            self._keyboard_controller.pressed(modifier)

        # Press and release the final key
        self._keyboard_controller.press(final_key)
        time.sleep(0.1)
        self._keyboard_controller.release(final_key)

        return True
