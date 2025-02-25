from enum import Enum
from typing import Annotated, List, Literal, Optional, TypedDict, Union

from pydantic import BaseModel, Field, StringConstraints, field_validator
from pynput.keyboard import Key as PynputKey
from pynput.keyboard import KeyCode as PynputKeyCode
from pynput.mouse import Button as PynputButton

# Backend-specific mappings
_VNC_MOUSE_BUTTON_MAPPING = {"left": 1, "middle": 2, "right": 3}

_PYAUTOGUI_MOUSE_BUTTON_MAPPING = {"left": "left", "middle": "middle", "right": "right"}

# Add Pynput mapping
_PYNPUT_MOUSE_BUTTON_MAPPING = {
    "left": PynputButton.left,
    "middle": PynputButton.middle,
    "right": PynputButton.right,
}


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

    @classmethod
    def to_vnc(cls, button: Union["MouseButton", str]) -> int:
        """
        Convert a standard mouse button into the VNC-compatible code.
        For VNC, left=1, middle=2, right=3.
        """
        # If a MouseButton enum was passed, use its value; otherwise assume a string was passed.
        button_val = button.value if isinstance(button, cls) else button
        return _VNC_MOUSE_BUTTON_MAPPING.get(button_val, 1)

    @classmethod
    def to_pyautogui(cls, button: Union["MouseButton", str]) -> str:
        """
        Convert a standard mouse button into the PyAutoGUI-compatible string.
        """
        button_val = button.value if isinstance(button, cls) else button
        return _PYAUTOGUI_MOUSE_BUTTON_MAPPING.get(button_val, "left")

    @classmethod
    def to_pynput(cls, button: Union["MouseButton", str]) -> PynputButton:
        """Convert a standard mouse button to Pynput PynputButton"""
        button_val = button.value if isinstance(button, cls) else button
        return _PYNPUT_MOUSE_BUTTON_MAPPING.get(button_val, PynputButton.left)

    @classmethod
    def from_pynput(cls, button) -> "MouseButton":
        if button == PynputButton.left:
            return cls.LEFT
        elif button == PynputButton.middle:
            return cls.MIDDLE
        elif button == PynputButton.right:
            return cls.RIGHT
        return None

    @classmethod
    def is_valid_button(cls, button: str) -> bool:
        """
        Check if the supplied button string is one of the legal mouse buttons.
        """
        return any(button == item.value for item in cls)


class KeyboardKey(str, Enum):
    # Special Keys
    ENTER = "enter"
    TAB = "tab"
    SPACE = "space"
    BACKSPACE = "backspace"
    DELETE = "delete"
    ESCAPE = "escape"
    HOME = "home"
    END = "end"
    PAGE_UP = "pageup"
    PAGE_DOWN = "pagedown"

    # Arrow Keys
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    # Modifier Keys - generic and with left/right differentiation
    SHIFT = "shift"
    CTRL = "ctrl"
    LCTRL = "lctrl"
    RCTRL = "rctrl"
    ALT = "alt"
    LALT = "lalt"
    RALT = "ralt"
    META = "meta"  # Generic / non-specified meta key
    LMETA = "lmeta"
    RMETA = "rmeta"

    # Function Keys F1 - F12
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"

    # Common Alphabet Keys A - Z
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"

    # Number Keys 0 - 9 (using NUM_x naming)
    NUM_0 = "0"
    NUM_1 = "1"
    NUM_2 = "2"
    NUM_3 = "3"
    NUM_4 = "4"
    NUM_5 = "5"
    NUM_6 = "6"
    NUM_7 = "7"
    NUM_8 = "8"
    NUM_9 = "9"

    @classmethod
    def to_vnc(cls, key: Union["KeyboardKey", str]) -> str:
        """Convert a standard key to VNC format"""
        key_val = key.value if isinstance(key, cls) else key
        if key_val in _SPECIAL_VNC_KEYBOARD_KEY_MAPPINGS:
            return _SPECIAL_VNC_KEYBOARD_KEY_MAPPINGS[str(key_val)]
        return key_val

    @classmethod
    def to_pyautogui(cls, key: Union["KeyboardKey", str]) -> str:
        """Convert a standard key to PyAutoGUI format"""
        key_val = key.value if isinstance(key, cls) else key
        if key_val in _SPECIAL_PYAUTOGUI_KEYBOARD_KEY_MAPPINGS:
            return _SPECIAL_PYAUTOGUI_KEYBOARD_KEY_MAPPINGS[str(key_val)]
        return key_val

    @classmethod
    def to_pynput(cls, key: Union["KeyboardKey", str]) -> PynputKey:
        """Convert a standard key to Pynput format"""
        key_val = key.value if isinstance(key, cls) else key
        if key_val in _SPECIAL_PYNPUT_KEYBOARD_KEY_MAPPINGS:
            return _SPECIAL_PYNPUT_KEYBOARD_KEY_MAPPINGS[str(key_val)]
        return key_val

    @classmethod
    def to_e2b(cls, key: Union["KeyboardKey", str]) -> str:
        """Convert a standard key to E2B format.
        If no mapping is provided in _E2B_MAPPING, defaults to returning the key itself.
        """
        key_val = key.value if isinstance(key, cls) else key
        if key_val in _SPECIAL_E2B_KEYBOARD_KEY_MAPPINGS:
            return _SPECIAL_E2B_KEYBOARD_KEY_MAPPINGS[str(key_val)]
        return key_val

    @classmethod
    def from_pynput(cls, key) -> "KeyboardKey":
        # Find the KeyboardKey enum value by looking up the pynput key in the mapping
        for enum_key, pynput_key in _SPECIAL_PYNPUT_KEYBOARD_KEY_MAPPINGS.items():
            if pynput_key == key:
                return cls(enum_key)
            # Special case for shift keys
            if key in (
                PynputKey.shift,
                PynputKey.shift_l,
                PynputKey.shift_r,
            ) and pynput_key in (PynputKey.shift, PynputKey.shift_l, PynputKey.shift_r):
                return cls.SHIFT
            # Special case for ctrl keys
            if key in (
                PynputKey.ctrl,
                PynputKey.ctrl_l,
                PynputKey.ctrl_r,
            ) and pynput_key in (PynputKey.ctrl, PynputKey.ctrl_l, PynputKey.ctrl_r):
                return cls.CTRL
            # Special case for alt keys
            if key in (
                PynputKey.alt,
                PynputKey.alt_l,
                PynputKey.alt_r,
            ) and pynput_key in (PynputKey.alt, PynputKey.alt_l, PynputKey.alt_r):
                return cls.ALT
            # Special case for meta keys
            if key in (
                PynputKey.cmd,
                PynputKey.cmd_l,
                PynputKey.cmd_r,
            ) and pynput_key in (PynputKey.cmd, PynputKey.cmd_l, PynputKey.cmd_r):
                return cls.META
        # Handle character keys
        if isinstance(key, PynputKeyCode) and key.char:
            try:
                return cls(key.char.lower())
            except ValueError:
                return None
        return None

    @classmethod
    def is_valid_key(cls, key: Union["KeyboardKey", str]) -> bool:
        """Check if a key is valid"""
        return any(
            key == value
            for value in vars(cls).values()
            if isinstance(value, str) and not value.startswith("_")
        )


# Mapping for different backends
_SPECIAL_VNC_KEYBOARD_KEY_MAPPINGS = {
    KeyboardKey.META: "meta",
    KeyboardKey.LMETA: "meta",
    KeyboardKey.RMETA: "meta",
    KeyboardKey.CTRL: "control",
    KeyboardKey.LCTRL: "control",
    KeyboardKey.RCTRL: "control",
    KeyboardKey.ALT: "alt",
    KeyboardKey.LALT: "alt",
    KeyboardKey.RALT: "alt",
}

_SPECIAL_PYAUTOGUI_KEYBOARD_KEY_MAPPINGS = {
    KeyboardKey.META: "meta",
    KeyboardKey.LMETA: "meta",
    KeyboardKey.RMETA: "meta",
    KeyboardKey.CTRL: "ctrl",
    KeyboardKey.LCTRL: "ctrl",
    KeyboardKey.RCTRL: "ctrl",
    KeyboardKey.ALT: "alt",
    KeyboardKey.LALT: "alt",
    KeyboardKey.RALT: "alt",
}

_SPECIAL_E2B_KEYBOARD_KEY_MAPPINGS = {
    KeyboardKey.META: "meta",
    KeyboardKey.LMETA: "meta",
    KeyboardKey.RMETA: "meta",
    KeyboardKey.CTRL: "control",
    KeyboardKey.LCTRL: "control",
    KeyboardKey.RCTRL: "control",
    KeyboardKey.ALT: "alt",
    KeyboardKey.LALT: "alt",
    KeyboardKey.RALT: "alt",
}

_SPECIAL_PYNPUT_KEYBOARD_KEY_MAPPINGS = {
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
    KeyboardKey.UP: PynputKey.up,
    KeyboardKey.DOWN: PynputKey.down,
    KeyboardKey.LEFT: PynputKey.left,
    KeyboardKey.RIGHT: PynputKey.right,
    KeyboardKey.SHIFT: PynputKey.shift,
    KeyboardKey.SHIFT: PynputKey.shift_l,
    KeyboardKey.SHIFT: PynputKey.shift_r,
    KeyboardKey.LCTRL: PynputKey.ctrl_l,
    KeyboardKey.RCTRL: PynputKey.ctrl_r,
    KeyboardKey.CTRL: PynputKey.ctrl,
    KeyboardKey.LALT: PynputKey.alt_l,
    KeyboardKey.RALT: PynputKey.alt_r,
    KeyboardKey.ALT: PynputKey.alt,
    KeyboardKey.LMETA: PynputKey.cmd_l,
    KeyboardKey.RMETA: PynputKey.cmd_r,
    KeyboardKey.META: PynputKey.cmd,
}


class ComputerObservationType(str, Enum):
    SCREENSHOT = "screenshot"
    MOUSE_STATE = "mouse_state"
    KEYBOARD_STATE = "keyboard_state"


class BaseComputerObservation(BaseModel):
    observation_type: str


class ScreenshotObservation(BaseComputerObservation):
    observation_type: Literal["screenshot"] = ComputerObservationType.SCREENSHOT.value
    screenshot: str

    @field_validator("screenshot")
    @classmethod
    def validate_screenshot(cls, v):
        if not v:
            raise ValueError("Screenshot cannot be empty")
        return v


class MouseStateObservation(BaseComputerObservation):
    observation_type: Literal["mouse_state"] = ComputerObservationType.MOUSE_STATE.value
    buttons: dict[MouseButton, bool]  # 0=released, 1=pressed
    position: tuple[int, int]

    @field_validator("buttons")
    @classmethod
    def validate_buttons(cls, v):
        if not v:
            raise ValueError("Buttons dictionary cannot be empty")
        for button in v:
            if not isinstance(button, MouseButton) and not MouseButton.is_valid_button(
                button
            ):
                raise ValueError(f"Invalid mouse button: {button}")
        return v


class KeyboardStateObservation(BaseComputerObservation):
    observation_type: Literal["keyboard_state"] = (
        ComputerObservationType.KEYBOARD_STATE.value
    )
    keys: dict[KeyboardKey, bool]  # 0=released, 1=pressed

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, v):
        if not v:
            raise ValueError("Keys dictionary cannot be empty")
        for key in v:
            if not isinstance(key, KeyboardKey) and not KeyboardKey.is_valid_key(key):
                raise ValueError(f"Invalid keyboard key: {key}")
        return v


# Define a Union type for computer observations
ComputerObservationUnion = Union[
    ScreenshotObservation, MouseStateObservation, KeyboardStateObservation
]


class ComputerObservation(TypedDict):
    screenshot: Optional[ScreenshotObservation] = None
    mouse_state: Optional[MouseStateObservation] = None
    keyboard_state: Optional[KeyboardStateObservation] = None
    # TODO: also add keyboard_events and mouse_events where you store the events that were collected since last observation


class ComputerActionType(str, Enum):
    COMMAND = "command"
    KEYBOARD_KEY_PRESS = "keyboard_key_press"
    KEYBOARD_KEY_DOWN = "keyboard_key_down"
    KEYBOARD_KEY_RELEASE = "keyboard_key_release"
    KEYBOARD_HOTKEY = "keyboard_hotkey"
    TYPE = "type"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"
    MOUSE_BUTTON_DOWN = "mouse_button_down"
    MOUSE_BUTTON_UP = "mouse_button_up"
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    DRAG = "drag"


class BaseComputerAction(BaseModel):
    action_type: str


class CommandAction(BaseComputerAction):
    action_type: Literal["command"] = ComputerActionType.COMMAND.value
    command: Annotated[str, StringConstraints(min_length=1)]
    timeout: float | None = (
        None  # important: None means the command will run indefinitely until it finishes
    )


class KeyboardKeysPressAction(BaseComputerAction):
    action_type: Literal["keyboard_key_press"] = (
        ComputerActionType.KEYBOARD_KEY_PRESS.value
    )
    keys: List[KeyboardKey]
    duration: float = 0.1


class KeyboardKeyPressAction(BaseComputerAction):
    action_type: Literal["keyboard_key_press"] = (
        ComputerActionType.KEYBOARD_KEY_PRESS.value
    )
    key: KeyboardKey
    duration: float = 0.1


class KeyboardKeysDownAction(BaseComputerAction):
    action_type: Literal["keyboard_key_down"] = (
        ComputerActionType.KEYBOARD_KEY_DOWN.value
    )
    keys: List[KeyboardKey]


class KeyboardKeyDownAction(BaseComputerAction):
    action_type: Literal["keyboard_key_down"] = (
        ComputerActionType.KEYBOARD_KEY_DOWN.value
    )
    key: KeyboardKey


class KeyboardKeysReleaseAction(BaseComputerAction):
    action_type: Literal["keyboard_key_release"] = (
        ComputerActionType.KEYBOARD_KEY_RELEASE.value
    )
    keys: List[KeyboardKey]


class KeyboardKeyReleaseAction(BaseComputerAction):
    action_type: Literal["keyboard_key_release"] = (
        ComputerActionType.KEYBOARD_KEY_RELEASE.value
    )
    key: KeyboardKey


class KeyboardHotkeyAction(BaseComputerAction):
    action_type: Literal["keyboard_hotkey"] = ComputerActionType.KEYBOARD_HOTKEY.value
    keys: List[KeyboardKey]


class TypeAction(BaseComputerAction):
    action_type: Literal["type"] = ComputerActionType.TYPE.value
    text: str


class MouseMoveAction(BaseComputerAction):
    action_type: Literal["mouse_move"] = ComputerActionType.MOUSE_MOVE.value
    x: int
    y: int
    move_duration: float = 0.5


class MouseScrollAction(BaseComputerAction):
    action_type: Literal["mouse_scroll"] = ComputerActionType.MOUSE_SCROLL.value
    amount: float


class MouseButtonDownAction(BaseComputerAction):
    action_type: Literal["mouse_button_down"] = (
        ComputerActionType.MOUSE_BUTTON_DOWN.value
    )
    button: MouseButton = MouseButton.LEFT


class MouseButtonUpAction(BaseComputerAction):
    action_type: Literal["mouse_button_up"] = ComputerActionType.MOUSE_BUTTON_UP.value
    button: MouseButton = MouseButton.LEFT


class ClickAction(BaseComputerAction):
    action_type: Literal["click"] = ComputerActionType.CLICK.value
    x: int
    y: int
    move_duration: float = 0.5
    press_duration: float = 0.1
    button: MouseButton = MouseButton.LEFT


class DoubleClickAction(BaseComputerAction):
    action_type: Literal["double_click"] = ComputerActionType.DOUBLE_CLICK.value
    x: int
    y: int
    move_duration: float = 0.5
    press_duration: float = 0.1
    button: MouseButton = MouseButton.LEFT
    double_click_interval_seconds: float = 0.1


class DragAction(BaseComputerAction):
    action_type: Literal["drag"] = ComputerActionType.DRAG.value
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    move_duration: float = 0.5
    button: MouseButton = MouseButton.LEFT


# Define a Union type for computer actions
ComputerActionUnion = Union[
    CommandAction,
    KeyboardKeysPressAction,
    KeyboardKeysDownAction,
    KeyboardKeysReleaseAction,
    KeyboardKeyPressAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardHotkeyAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    ClickAction,
    DoubleClickAction,
    DragAction,
]


class ComputerAction(TypedDict):
    command: Optional[CommandAction] = None
    keyboard_keys_press: Optional[KeyboardKeysPressAction] = None
    keyboard_keys_down: Optional[KeyboardKeysDownAction] = None
    keyboard_keys_release: Optional[KeyboardKeysReleaseAction] = None
    keyboard_key_press: Optional[KeyboardKeyPressAction] = None
    keyboard_key_down: Optional[KeyboardKeyDownAction] = None
    keyboard_key_release: Optional[KeyboardKeyReleaseAction] = None
    keyboard_hotkey: Optional[KeyboardHotkeyAction] = None
    type: Optional[TypeAction] = None
    mouse_move: Optional[MouseMoveAction] = None
    mouse_scroll: Optional[MouseScrollAction] = None
    mouse_button_down: Optional[MouseButtonDownAction] = None
    mouse_button_up: Optional[MouseButtonUpAction] = None
    click: Optional[ClickAction] = None
    double_click: Optional[DoubleClickAction] = None
    drag: Optional[DragAction] = None
