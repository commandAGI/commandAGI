
from enum import Enum
from typing import Optional, TypedDict


class ComputerRunningState(Enum, str):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


# Platform enumeration
class Platform(str, Enum):
    """Operating system platform."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


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


class SystemInfo(BaseModel):
    """Information about the system."""

    cpu_usage: float = Field(
        description="CPU usage percentage from system monitoring APIs"
    )
    memory_usage: float = Field(
        description="Memory usage percentage from system monitoring APIs"
    )
    disk_usage: float = Field(description="Disk usage percentage from filesystem APIs")
    uptime: float = Field(description="System uptime in seconds")
    hostname: str = Field(description="System hostname")
    ip_address: str = Field(description="Primary IP address from network interfaces")
    user: str = Field(description="Current username")
    os: str = Field(description="Operating system name")
    version: str = Field(description="Operating system version")
    architecture: str = Field(description="CPU architecture (x86_64, arm64, etc.)")

