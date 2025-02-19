import subprocess
import time
import mss
from PIL import Image
import io
import base64
from typing import Optional
import threading

from pynput import keyboard, mouse

from commandagi_j2.computers.base_computer import Computer
from commandagi_j2.envs.computer_types import (
    KeyboardKey,
    MouseButton,
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

class PynputComputer(Computer):
    """Computer implementation using pynput for local input control and mss for screenshots"""

    def __init__(self):
        self.sct = mss.mss()
        self._keyboard_controller = keyboard.Controller()
        self._mouse_controller = mouse.Controller()

        self._pressed_keys = set()
        self._mouse_buttons = {
            MouseButton.LEFT: False,
            MouseButton.MIDDLE: False,
            MouseButton.RIGHT: False,
        }
        self._mouse_pos = (0, 0)

        # Start listeners for tracking keyboard and mouse state
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_keyboard_press, on_release=self._on_keyboard_release
        )
        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._keyboard_listener.start()
        self._mouse_listener.start()

    def _on_keyboard_press(self, key):
        self._pressed_keys.add(key)

    def _on_keyboard_release(self, key):
        if key in self._pressed_keys:
            self._pressed_keys.remove(key)

    def _on_mouse_move(self, x, y):
        self._mouse_pos = (x, y)

    def _on_mouse_click(self, x, y, button, pressed):
        from commandagi_j2.envs.computer_types import MouseButton as StandardMouseButton
        if button == mouse.Button.left:
            standard_btn = StandardMouseButton.LEFT
        elif button == mouse.Button.right:
            standard_btn = StandardMouseButton.RIGHT
        elif button == mouse.Button.middle:
            standard_btn = StandardMouseButton.MIDDLE
        else:
            standard_btn = StandardMouseButton.LEFT
        self._mouse_buttons[standard_btn] = pressed
        self._mouse_pos = (x, y)

    def _on_mouse_scroll(self, x, y, dx, dy):
        self._mouse_pos = (x, y)

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        screenshot = self.sct.grab(self.sct.monitors[1])
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_screenshot = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return ScreenshotObservation(screenshot=b64_screenshot)

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        return MouseStateObservation(
            buttons=self._mouse_buttons.copy(),
            position=self._mouse_pos,
        )

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        from commandagi_j2.envs.computer_types import KeyboardKey as StandardKeyboardKey
        keys_state = {key: False for key in StandardKeyboardKey}
        for key in self._pressed_keys:
            conv_key = KeyboardKey.from_pynput(key)
            if conv_key is not None:
                keys_state[conv_key] = True
        return KeyboardStateObservation(keys=keys_state)

    def execute_command(self, action: CommandAction) -> bool:
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
        pynput_key = KeyboardKey.to_pynput(action.key)
        self._keyboard_controller.press(pynput_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        pynput_key = KeyboardKey.to_pynput(action.key)
        self._keyboard_controller.release(pynput_key)
        return True

    def execute_type(self, action: TypeAction) -> bool:
        self._keyboard_controller.type(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        start_x, start_y = self._mouse_pos
        steps = max(int(action.move_duration * 60), 1)
        for step in range(1, steps + 1):
            t = step / steps
            current_x = int(start_x + (action.x - start_x) * t)
            current_y = int(start_y + (action.y - start_y) * t)
            self._mouse_controller.position = (current_x, current_y)
            if action.move_duration > 0:
                time.sleep(action.move_duration / steps)
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        self._mouse_controller.scroll(0, int(action.amount))
        return True

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        if action.button.value == "left":
            pynput_button = mouse.Button.left
        elif action.button.value == "right":
            pynput_button = mouse.Button.right
        elif action.button.value == "middle":
            pynput_button = mouse.Button.middle
        else:
            pynput_button = mouse.Button.left
        self._mouse_controller.press(pynput_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        if action.button.value == "left":
            pynput_button = mouse.Button.left
        elif action.button.value == "right":
            pynput_button = mouse.Button.right
        elif action.button.value == "middle":
            pynput_button = mouse.Button.middle
        else:
            pynput_button = mouse.Button.left
        self._mouse_controller.release(pynput_button)
        return True

    def close(self):
        self.sct.close()
        try:
            self._keyboard_listener.stop()
        except Exception:
            pass
        try:
            self._mouse_listener.stop()
        except Exception:
            pass 