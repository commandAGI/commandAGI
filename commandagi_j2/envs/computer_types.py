from enum import Enum
from typing import Literal, List, Optional, Union
from pydantic import BaseModel
from pynput.keyboard import Key as PynputKey, KeyCode as PynputKeyCode
from pynput.mouse import Button as PynputButton


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

    # Backend-specific mappings
    _VNC_MAPPING = {"left": 1, "middle": 2, "right": 3}

    _PYAUTOGUI_MAPPING = {"left": "left", "middle": "middle", "right": "right"}

    # Add Pynput mapping
    _PYNPUT_MAPPING = {
        "left": PynputButton.left,
        "middle": PynputButton.middle,
        "right": PynputButton.right,
    }

    @classmethod
    def to_vnc(cls, button: Union["MouseButton", str]) -> int:
        """
        Convert a standard mouse button into the VNC-compatible code.
        For VNC, left=1, middle=2, right=3.
        """
        # If a MouseButton enum was passed, use its value; otherwise assume a string was passed.
        button_val = button.value if isinstance(button, cls) else button
        return cls._VNC_MAPPING.get(button_val, 1)

    @classmethod
    def to_pyautogui(cls, button: Union["MouseButton", str]) -> str:
        """
        Convert a standard mouse button into the PyAutoGUI-compatible string.
        """
        button_val = button.value if isinstance(button, cls) else button
        return cls._PYAUTOGUI_MAPPING.get(button_val, "left")

    @classmethod
    def is_valid_button(cls, button: str) -> bool:
        """
        Check if the supplied button string is one of the legal mouse buttons.
        """
        return any(button == item.value for item in cls)

    @classmethod
    def to_pynput(cls, button: Union["MouseButton", str]) -> PynputButton:
        """Convert a standard mouse button to Pynput PynputButton"""
        button_val = button.value if isinstance(button, cls) else button
        return cls._PYNPUT_MAPPING.get(button_val, PynputButton.left)

    @classmethod
    def from_pynput(cls, button) -> "MouseButton":
        if button == PynputButton.left:
            return cls.LEFT
        elif button == PynputButton.middle:
            return cls.MIDDLE
        elif button == PynputButton.right:
            return cls.RIGHT
        return None


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

    # Mapping for different backends
    _SPECIAL_VNC_MAPPINGS = {
        META: "meta",
        LMETA: "meta",
        RMETA: "meta",
        CTRL: "control",
        LCTRL: "control",
        RCTRL: "control",
        ALT: "alt",
        LALT: "alt",
        RALT: "alt",
    }

    _SPECIAL_PYAUTOGUI_MAPPINGS = {
        META: "meta",
        LMETA: "meta",
        RMETA: "meta",
        CTRL: "ctrl",
        LCTRL: "ctrl",
        RCTRL: "ctrl",
        ALT: "alt",
        LALT: "alt",
        RALT: "alt",
    }

    _SPECIAL_E2B_MAPPINGS = {
        META: "meta",
        LMETA: "meta",
        RMETA: "meta",
        CTRL: "control",
        LCTRL: "control",
        RCTRL: "control",
        ALT: "alt",
        LALT: "alt",
        RALT: "alt",
    }

    _SPECIAL_PYNPUT_MAPPINGS = {
        ENTER: PynputKey.enter,
        TAB: PynputKey.tab,
        SPACE: PynputKey.space,
        BACKSPACE: PynputKey.backspace,
        DELETE: PynputKey.delete,
        ESCAPE: PynputKey.esc,
        HOME: PynputKey.home,
        END: PynputKey.end,
        PAGE_UP: PynputKey.page_up,
        PAGE_DOWN: PynputKey.page_down,
        UP: PynputKey.up,
        DOWN: PynputKey.down,
        LEFT: PynputKey.left,
        RIGHT: PynputKey.right,
        SHIFT: PynputKey.shift,
        SHIFT: PynputKey.shift_l,
        SHIFT: PynputKey.shift_r,
        LCTRL: PynputKey.ctrl_l,
        RCTRL: PynputKey.ctrl_r,
        CTRL: PynputKey.ctrl,
        LALT: PynputKey.alt_l,
        RALT: PynputKey.alt_r,
        ALT: PynputKey.alt,
        LMETA: PynputKey.cmd_l,
        RMETA: PynputKey.cmd_r,
        META: PynputKey.cmd,
    }

    @classmethod
    def to_vnc(cls, key: Union["KeyboardKey", str]) -> str:
        """Convert a standard key to VNC format"""
        if key in cls._SPECIAL_VNC_MAPPINGS:
            return cls._SPECIAL_VNC_MAPPINGS[key]
        return key

    @classmethod
    def to_pyautogui(cls, key: Union["KeyboardKey", str]) -> str:
        """Convert a standard key to PyAutoGUI format"""
        if key in cls._SPECIAL_PYAUTOGUI_MAPPINGS:
            return cls._SPECIAL_PYAUTOGUI_MAPPINGS[key]
        return key

    @classmethod
    def to_pynput(cls, key: Union["KeyboardKey", str]) -> str:
        """Convert a standard key to Pynput format"""
        if key in cls._SPECIAL_PYNPUT_MAPPINGS:
            return cls._SPECIAL_PYNPUT_MAPPINGS[key]
        return key

    @classmethod
    def to_e2b(cls, key: Union["KeyboardKey", str]) -> str:
        """Convert a standard key to E2B format.
        If no mapping is provided in _E2B_MAPPING, defaults to returning the key itself.
        """
        key_val = key.value if isinstance(key, cls) else key
        if key_val in cls._SPECIAL_E2B_MAPPINGS:
            return cls._SPECIAL_E2B_MAPPINGS[key_val]
        return key_val

    @classmethod
    def from_pynput(cls, key) -> "KeyboardKey":
        # Find the KeyboardKey enum value by looking up the pynput key in the mapping
        for enum_key, pynput_key in cls._SPECIAL_PYNPUT_MAPPINGS.items():
            if pynput_key == key:
                return enum_key
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


class ComputerObservationType(str, Enum):
    SCREENSHOT = "screenshot"
    MOUSE_STATE = "mouse_state"
    KEYBOARD_STATE = "keyboard_state"


class BaseComputerObservation(BaseModel):
    observation_type: ComputerObservationType


class ScreenshotObservation(BaseComputerObservation):
    observation_type: Literal[ComputerObservationType.SCREENSHOT] = (
        ComputerObservationType.SCREENSHOT
    )
    screenshot: str


class MouseStateObservation(BaseComputerObservation):
    observation_type: Literal[ComputerObservationType.MOUSE_STATE] = (
        ComputerObservationType.MOUSE_STATE
    )
    buttons: dict[MouseButton, bool]  # 0=released, 1=pressed
    position: tuple[int, int]


class KeyboardStateObservation(BaseComputerObservation):
    observation_type: Literal[ComputerObservationType.KEYBOARD_STATE] = (
        ComputerObservationType.KEYBOARD_STATE
    )
    keys: dict[KeyboardKey, bool]  # 0=released, 1=pressed


class ComputerObservation(BaseModel):
    screenshot: Optional[ScreenshotObservation] = None
    mouse_state: Optional[MouseStateObservation] = None
    keyboard_state: Optional[KeyboardStateObservation] = None


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
    DRAG = "drag"


class BaseComputerAction(BaseModel):
    action_type: ComputerActionType


class CommandAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.COMMAND] = ComputerActionType.COMMAND
    command: str
    timeout: float | None = (
        None  # important: None means the command will run indefinitely until it finishes
    )


class KeyboardKeysPressAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.KEYBOARD_KEY_PRESS] = (
        ComputerActionType.KEYBOARD_KEY_PRESS
    )
    keys: List[KeyboardKey]
    duration: float = 0.1


class KeyboardKeyPressAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.KEYBOARD_KEY_PRESS] = (
        ComputerActionType.KEYBOARD_KEY_PRESS
    )
    key: KeyboardKey
    duration: float = 0.1


class KeyboardKeysDownAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.KEYBOARD_KEY_DOWN] = (
        ComputerActionType.KEYBOARD_KEY_DOWN
    )
    keys: List[KeyboardKey]


class KeyboardKeyDownAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.KEYBOARD_KEY_DOWN] = (
        ComputerActionType.KEYBOARD_KEY_DOWN
    )
    key: KeyboardKey


class KeyboardKeysReleaseAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.KEYBOARD_KEY_RELEASE] = (
        ComputerActionType.KEYBOARD_KEY_RELEASE
    )
    keys: List[KeyboardKey]


class KeyboardKeyReleaseAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.KEYBOARD_KEY_RELEASE] = (
        ComputerActionType.KEYBOARD_KEY_RELEASE
    )
    key: KeyboardKey


class KeyboardHotkeyAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.KEYBOARD_HOTKEY] = (
        ComputerActionType.KEYBOARD_HOTKEY
    )
    keys: List[KeyboardKey]


class TypeAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.TYPE] = ComputerActionType.TYPE
    text: str


class MouseMoveAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.MOUSE_MOVE] = ComputerActionType.MOUSE_MOVE
    x: int
    y: int
    move_duration: float = 0.5


class MouseScrollAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.MOUSE_SCROLL] = (
        ComputerActionType.MOUSE_SCROLL
    )
    amount: float


class MouseButtonDownAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.MOUSE_BUTTON_DOWN] = (
        ComputerActionType.MOUSE_BUTTON_DOWN
    )
    button: MouseButton = MouseButton.LEFT


class MouseButtonUpAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.MOUSE_BUTTON_UP] = (
        ComputerActionType.MOUSE_BUTTON_UP
    )
    button: MouseButton = MouseButton.LEFT


class ClickAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.CLICK] = ComputerActionType.CLICK
    x: int
    y: int
    move_duration: float = 0.5
    press_duration: float = 0.1
    button: MouseButton = MouseButton.LEFT


class DragAction(BaseComputerAction):
    action_type: Literal[ComputerActionType.DRAG] = ComputerActionType.DRAG
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    move_duration: float = 0.5
    button: MouseButton = MouseButton.LEFT


class ComputerAction(BaseModel):
    command: Optional[CommandAction] = None
    keyboard_keys_press: Optional[KeyboardKeysPressAction] = None
    keyboard_keys_down: Optional[KeyboardKeysDownAction] = None
    keyboard_keys_release: Optional[KeyboardKeysReleaseAction] = None
    type: Optional[TypeAction] = None
    mouse_move: Optional[MouseMoveAction] = None
    mouse_scroll: Optional[MouseScrollAction] = None
    mouse_button_down: Optional[MouseButtonDownAction] = None
    mouse_button_up: Optional[MouseButtonUpAction] = None
    click: Optional[ClickAction] = None
    drag: Optional[DragAction] = None
