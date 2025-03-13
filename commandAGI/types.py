from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict, Union

from pydantic import BaseModel, Field, StringConstraints, field_validator


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

    @classmethod
    def is_valid_button(cls, button: str) -> bool:
        """Check if a string is a valid mouse button."""
        return button in [b.value for b in cls]


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
    def is_valid_key(cls, key: Union["KeyboardKey", str]) -> bool:
        """Check if a string is a valid keyboard key."""
        if isinstance(key, KeyboardKey):
            return True
        return key in [k.value for k in cls]


# Platform enumeration
class Platform(str, Enum):
    """Operating system platform."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class ComputerObservationType(str, Enum):
    SCREENSHOT = "screenshot"
    MOUSE_STATE = "mouse_state"
    KEYBOARD_STATE = "keyboard_state"
    LAYOUT_TREE = "layout_tree"
    PROCESSES = "processes"
    WINDOWS = "windows"
    DISPLAYS = "displays"


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


# Define component tree types
class UIElementCommonProperties(TypedDict, total=False):
    """Common properties of a UI element across all platforms."""

    name: Optional[str]  # Name/label of the element
    # Role/type of the element (normalized across platforms)
    role: Optional[str]
    value: Optional[Any]  # Current value of the element
    description: Optional[str]  # Description of the element

    # State properties
    enabled: Optional[bool]  # Whether the element is enabled
    focused: Optional[bool]  # Whether the element has keyboard focus
    visible: Optional[bool]  # Whether the element is visible
    offscreen: Optional[bool]  # Whether the element is off-screen

    # Position and size
    bounds: Optional[Dict[str, int]]  # {left, top, width, height}

    # Control-specific properties
    selected: Optional[bool]  # Whether the element is selected
    checked: Optional[bool]  # Whether the element is checked
    expanded: Optional[bool]  # Whether the element is expanded

    # For elements with range values (sliders, progress bars)
    current_value: Optional[float]  # Current value
    min_value: Optional[float]  # Minimum value
    max_value: Optional[float]  # Maximum value
    percentage: Optional[float]  # Value as percentage


class UIElement(TypedDict):
    """A UI element in the accessibility tree."""

    # Common properties normalized across platforms
    properties: UIElementCommonProperties
    # Platform-specific properties
    platform: Platform  # The platform this element was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties
    # Child elements
    children: List["UIElement"]


# Define process information type
class ProcessInfo(TypedDict):
    """Information about a running process."""

    # Common properties across platforms
    pid: int  # Process ID
    name: str  # Process name
    cpu_percent: float  # CPU usage percentage
    memory_mb: float  # Memory usage in MB
    status: str  # Process status (running, sleeping, etc.)
    # Platform-specific properties
    platform: Platform  # The platform this process was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties


# Define window information type
class WindowInfo(TypedDict):
    """Information about a window."""

    # Common properties across platforms
    title: str  # Window title
    bounds: Dict[str, int]  # {left, top, width, height}
    minimized: bool  # Whether the window is minimized
    maximized: bool  # Whether the window is maximized
    focused: bool  # Whether the window has focus
    # Platform-specific properties
    platform: Platform  # The platform this window was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties


# Define display information type
class DisplayInfo(TypedDict):
    """Information about a display."""

    # Common properties across platforms
    id: int  # Display ID
    bounds: Dict[str, int]  # {left, top, width, height}
    is_primary: bool  # Whether this is the primary display
    # Platform-specific properties
    platform: Platform  # The platform this display was retrieved from
    platform_properties: Dict[str, Any]  # Raw platform-specific properties


class LayoutTreeObservation(BaseComputerObservation):
    observation_type: Literal["layout_tree"] = ComputerObservationType.LAYOUT_TREE.value
    tree: UIElement  # Structure containing the accessibility tree


class ProcessesObservation(BaseComputerObservation):
    observation_type: Literal["processes"] = ComputerObservationType.PROCESSES.value
    processes: List[ProcessInfo]  # List of process information dictionaries


class WindowsObservation(BaseComputerObservation):
    observation_type: Literal["windows"] = ComputerObservationType.WINDOWS.value
    windows: List[WindowInfo]  # List of window information dictionaries


class DisplaysObservation(BaseComputerObservation):
    observation_type: Literal["displays"] = ComputerObservationType.DISPLAYS.value
    displays: List[DisplayInfo]  # List of display information dictionaries


# Define a Union type for computer observations
ComputerObservationUnion = Union[
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    LayoutTreeObservation,
    ProcessesObservation,
    WindowsObservation,
    DisplaysObservation,
]


class ComputerObservation(TypedDict):
    screenshot: Optional[ScreenshotObservation] = None
    mouse_state: Optional[MouseStateObservation] = None
    keyboard_state: Optional[KeyboardStateObservation] = None
    layout_tree: Optional[LayoutTreeObservation] = None
    processes: Optional[ProcessesObservation] = None
    windows: Optional[WindowsObservation] = None
    displays: Optional[DisplaysObservation] = None
    # TODO: also add keyboard_events and mouse_events where you store the
    # events that were collected since last observation


class ComputerActionType(str, Enum):
    SHELL = "shell"
    KEYBOARD_KEYS_PRESS = "keyboard_keys_press"
    KEYBOARD_KEYS_DOWN = "keyboard_keys_down"
    KEYBOARD_KEYS_RELEASE = "keyboard_keys_release"
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
    RUN_PROCESS = "run_process"
    FILE_COPY_TO_COMPUTER = "file_copy_to_computer"
    FILE_COPY_FROM_COMPUTER = "file_copy_from_computer"
    JUPYTER_START_SERVER = "jupyter_start_server"
    JUPYTER_STOP_SERVER = "jupyter_stop_server"
    VIDEO_START_STREAM = "video_start_stream"
    VIDEO_STOP_STREAM = "video_stop_stream"
    COMPUTER_START = "computer_start"
    COMPUTER_STOP = "computer_stop"
    COMPUTER_PAUSE = "computer_pause"
    COMPUTER_RESUME = "computer_resume"
    VNC_START_SERVER = "vnc_start_server"
    VNC_STOP_SERVER = "vnc_stop_server"
    RDP_START_SERVER = "rdp_start_server"
    RDP_STOP_SERVER = "rdp_stop_server"
    MCP_START_SERVER = "mcp_start_server"
    MCP_STOP_SERVER = "mcp_stop_server"


class BaseComputerAction(BaseModel):
    action_type: str


class ShellCommandAction(BaseComputerAction):
    action_type: Literal["command"] = ComputerActionType.SHELL.value
    command: Annotated[str, StringConstraints(min_length=1)]
    timeout: float | None = (
        None  # important: None means the command will run indefinitely until it finishes
    )
    executible: Optional[str] = None


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


class RunProcessAction(BaseComputerAction):
    action_type: Literal["run_process"] = ComputerActionType.RUN_PROCESS.value
    command: str
    args: List[str] = Field(default_factory=list)
    cwd: Optional[str] = None
    env: Optional[dict] = None
    timeout: Optional[float] = None


class FileCopyToComputerAction(BaseComputerAction):
    action_type: Literal["file_copy_to_computer"] = (
        ComputerActionType.FILE_COPY_TO_COMPUTER.value
    )
    source_path: str
    destination_path: str


class FileCopyFromComputerAction(BaseComputerAction):
    action_type: Literal["file_copy_from_computer"] = (
        ComputerActionType.FILE_COPY_FROM_COMPUTER.value
    )
    source_path: str
    destination_path: str


class JupyterStartServerAction(BaseComputerAction):
    action_type: Literal["jupyter_start_server"] = (
        ComputerActionType.JUPYTER_START_SERVER.value
    )
    port: int = 8888
    notebook_dir: Optional[str] = None


class JupyterStopServerAction(BaseComputerAction):
    action_type: Literal["jupyter_stop_server"] = (
        ComputerActionType.JUPYTER_STOP_SERVER.value
    )


class VideoStartStreamAction(BaseComputerAction):
    action_type: Literal["video_start_stream"] = (
        ComputerActionType.VIDEO_START_STREAM.value
    )


class VideoStopStreamAction(BaseComputerAction):
    action_type: Literal["video_stop_stream"] = (
        ComputerActionType.VIDEO_STOP_STREAM.value
    )


class ComputerStartAction(BaseComputerAction):
    action_type: Literal["computer_start"] = ComputerActionType.COMPUTER_START.value


class ComputerStopAction(BaseComputerAction):
    action_type: Literal["computer_stop"] = ComputerActionType.COMPUTER_STOP.value


class ComputerPauseAction(BaseComputerAction):
    action_type: Literal["computer_pause"] = ComputerActionType.COMPUTER_PAUSE.value


class ComputerResumeAction(BaseComputerAction):
    action_type: Literal["computer_resume"] = ComputerActionType.COMPUTER_RESUME.value
    timeout_hours: Optional[float] = None


class VncStartServerAction(BaseComputerAction):
    action_type: Literal["vnc_start_server"] = ComputerActionType.VNC_START_SERVER.value


class VncStopServerAction(BaseComputerAction):
    action_type: Literal["vnc_stop_server"] = ComputerActionType.VNC_STOP_SERVER.value


class RdpStartServerAction(BaseComputerAction):
    action_type: Literal["rdp_start_server"] = ComputerActionType.RDP_START_SERVER.value


class RdpStopServerAction(BaseComputerAction):
    action_type: Literal["rdp_stop_server"] = ComputerActionType.RDP_STOP_SERVER.value


class McpStartServerAction(BaseComputerAction):
    action_type: Literal["mcp_start_server"] = ComputerActionType.MCP_START_SERVER.value


class McpStopServerAction(BaseComputerAction):
    action_type: Literal["mcp_stop_server"] = ComputerActionType.MCP_STOP_SERVER.value


# Define a Union type for computer actions
ComputerActionUnion = Union[
    ShellCommandAction,
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
    RunProcessAction,
    ComputerStartAction,
    ComputerStopAction,
    ComputerPauseAction,
    ComputerResumeAction,
    VncStartServerAction,
    VncStopServerAction,
    RdpStartServerAction,
    RdpStopServerAction,
    McpStartServerAction,
    McpStopServerAction,
]


class ComputerAction(TypedDict):
    command: Optional[ShellCommandAction] = None
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
    run_process: Optional[RunProcessAction] = None
