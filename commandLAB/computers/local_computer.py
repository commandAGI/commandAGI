import base64
import io
import os
import datetime
import subprocess
import tempfile
from textwrap import dedent
import time
import threading
import socket
import platform
import sys
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Union, Optional, Literal, List, Dict
import logging

try:
    import mss
    from PIL import Image
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandLAB with the local extra:\n\npip install commandLAB[local]"
    )

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
    KeyboardKey,
    KeyboardKeyDownAction,
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
    RunProcessAction,
    LayoutTreeObservation,
    ProcessesObservation,
    WindowsObservation,
    DisplaysObservation,
    Platform,
)
from commandLAB._utils.config import APPDIR
from commandLAB._utils.screenshot import process_screenshot


class VideoStreamHandler(BaseHTTPRequestHandler):
    """HTTP request handler for video streaming."""

    def __init__(self, *args, computer=None, **kwargs):
        self.computer = computer
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests for video streaming."""
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            # Simple HTML page with auto-refreshing image
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Local Computer Stream</title>
                <style>
                    body {{ margin: 0; padding: 0; background: #000; }}
                    img {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
                </style>
                <meta http-equiv="refresh" content="1">
            </head>
            <body>
                <img src="/screenshot.jpg" alt="Screen Capture">
            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif self.path == "/screenshot.jpg":
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()

            # Get screenshot from the computer
            if self.computer:
                screenshot = self.computer._get_screenshot(format="PIL")
                if screenshot.image:
                    img_byte_arr = io.BytesIO()
                    screenshot.image.save(img_byte_arr, format="JPEG", quality=70)
                    self.wfile.write(img_byte_arr.getvalue())
                else:
                    # Send a blank image if screenshot failed
                    blank = Image.new("RGB", (800, 600), color="black")
                    img_byte_arr = io.BytesIO()
                    blank.save(img_byte_arr, format="JPEG")
                    self.wfile.write(img_byte_arr.getvalue())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to use the computer's logger instead of printing to stderr."""
        if self.computer and self.computer.logger:
            self.computer.logger.debug(f"VideoStreamHandler: {format % args}")


class ThreadedHTTPServer(HTTPServer):
    """Threaded HTTP server for video streaming."""

    def __init__(self, server_address, RequestHandlerClass, computer=None):
        self.computer = computer

        # Create a request handler class that includes a reference to the computer
        class Handler(RequestHandlerClass):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, computer=computer, **kwargs)

        super().__init__(server_address, Handler)


class LocalComputer(BaseComputer):
    """Base class for local computer implementations.

    This class provides common functionality for local computer implementations
    such as screenshot capture, command execution, and basic resource management.
    """

    def __init__(self):
        super().__init__()
        self._sct = None
        self._temp_dir = None
        self._video_server = None
        self._video_server_thread = None
        self._video_server_port = None
        self._video_streaming = False
        self._ui_automation = None
        self._pyax = None
        self._atspi = None

    def _start(self):
        """Start the local computer environment."""
        if not self._sct:
            self.logger.info("Initializing MSS screen capture")
            self._sct = mss.mss()
        if not self._temp_dir:
            self.logger.info("Creating temporary directory")
            self._temp_dir = tempfile.mkdtemp()
        self.logger.info(f"{self.__class__.__name__} started")
        return True

    def _stop(self):
        """Stop the local computer environment."""
        # Stop video streaming if active
        if self._video_streaming:
            self.stop_video_stream()

        if self._sct:
            self.logger.info("Closing MSS screen capture")
            self._sct.close()
            self._sct = None
        if self._temp_dir:
            self.logger.info("Cleaning up temporary directory")
            self._temp_dir = None
        self.logger.info(f"{self.__class__.__name__} stopped")
        return True

    def _get_screenshot(
        self, display_id: int = 0, format: Literal["base64", "PIL", "path"] = "PIL"
    ) -> ScreenshotObservation:
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
            input_format="PIL",
            computer_name=self.__class__.__name__.lower(),
        )

    def _get_layout_tree(self) -> LayoutTreeObservation:
        """Return a LayoutTreeObservation containing the accessibility tree of the current UI.

        This method uses platform-specific accessibility APIs to retrieve the UI component tree.
        """
        system = platform.system()

        if system == "Windows":
            return self._get_windows_layout_tree()
        elif system == "Darwin":
            return self._get_macos_layout_tree()
        elif system == "Linux":
            return self._get_linux_layout_tree()
        else:
            self.logger.warning(f"Layout tree retrieval not implemented for {system}")
            return LayoutTreeObservation(tree={})

    def _get_windows_layout_tree(self) -> LayoutTreeObservation:
        """Get the UI component tree on Windows using UIAutomation."""
        try:
            if self._ui_automation is None:
                try:
                    import uiautomation as auto

                    self._ui_automation = auto
                except ImportError:
                    self.logger.error(
                        "UIAutomation not available. Install with: pip install uiautomation"
                    )
                    return LayoutTreeObservation(
                        tree={"error": "UIAutomation not available"}
                    )
            auto = self._ui_automation
            desktop = auto.GetRootControl()

            def build_tree(element):
                if not element:
                    return None
                # Build common normalized properties
                common_props = {
                    "name": element.Name if hasattr(element, "Name") else None,
                    "role": (
                        element.ControlTypeName
                        if hasattr(element, "ControlTypeName")
                        else None
                    ),
                    "enabled": (
                        element.IsEnabled if hasattr(element, "IsEnabled") else None
                    ),
                    "focused": (
                        element.HasKeyboardFocus
                        if hasattr(element, "HasKeyboardFocus")
                        else None
                    ),
                    "offscreen": (
                        element.IsOffscreen if hasattr(element, "IsOffscreen") else None
                    ),
                    "bounds": (
                        {
                            "left": element.BoundingRectangle.left,
                            "top": element.BoundingRectangle.top,
                            "width": element.BoundingRectangle.width(),
                            "height": element.BoundingRectangle.height(),
                        }
                        if hasattr(element, "BoundingRectangle")
                        else None
                    ),
                    "selected": None,
                    "checked": None,
                    "expanded": None,
                    "current_value": None,
                    "min_value": None,
                    "max_value": None,
                    "percentage": None,
                }
                # Collect platform specific properties
                platform_props = {
                    "AutomationId": (
                        element.AutomationId
                        if hasattr(element, "AutomationId")
                        else None
                    ),
                    "ClassName": (
                        element.ClassName if hasattr(element, "ClassName") else None
                    ),
                }
                children = []
                for child in element.GetChildren():
                    child_tree = build_tree(child)
                    if child_tree:
                        children.append(child_tree)
                return {
                    "properties": common_props,
                    "platform": Platform.WINDOWS,
                    "platform_properties": platform_props,
                    "children": children,
                }

            tree = build_tree(desktop)
            return LayoutTreeObservation(tree=tree)

        except Exception as e:
            self.logger.error(f"Error getting Windows layout tree: {e}")
            return LayoutTreeObservation(tree={"error": str(e)})

    def _get_macos_layout_tree(self) -> LayoutTreeObservation:
        """Get the UI component tree on macOS using pyax (Accessibility API)."""
        try:
            if self._pyax is None:
                try:
                    import pyax

                    self._pyax = pyax
                except ImportError:
                    self.logger.error(
                        "pyax not available. Install with: pip install pyax"
                    )
                    return LayoutTreeObservation(tree={"error": "pyax not available"})
            pyax = self._pyax

            def build_tree(element):
                if not element:
                    return None
                # Normalize common properties
                common_props = {
                    "name": (
                        element.get("AXTitle")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "role": (
                        element.get("AXRole")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "enabled": (
                        element.get("AXEnabled")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "focused": (
                        element.get("AXFocused")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "offscreen": None,
                    "bounds": None,
                    "selected": (
                        element.get("AXSelected")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "checked": None,
                    "expanded": (
                        element.get("AXExpanded")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "current_value": (
                        element.get("AXValue")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "min_value": (
                        element.get("AXMinValue")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "max_value": (
                        element.get("AXMaxValue")
                        if hasattr(element, "__getitem__")
                        else None
                    ),
                    "percentage": None,
                }
                # Platform-specific properties: store entire element dict
                platform_props = dict(element) if hasattr(element, "items") else {}
                children = []
                try:
                    # Assuming element is iterable for children
                    for child in element:
                        child_tree = build_tree(child)
                        if child_tree:
                            children.append(child_tree)
                except Exception:
                    pass
                return {
                    "properties": common_props,
                    "platform": Platform.MACOS,
                    "platform_properties": platform_props,
                    "children": children,
                }

            frontmost_app = pyax.get_frontmost_application()
            if not frontmost_app:
                return LayoutTreeObservation(
                    tree={"error": "No frontmost application found"}
                )
            tree = build_tree(frontmost_app)
            return LayoutTreeObservation(tree=tree)

        except Exception as e:
            self.logger.error(f"Error getting macOS layout tree: {e}")
            return LayoutTreeObservation(tree={"error": str(e)})

    def _get_linux_layout_tree(self) -> LayoutTreeObservation:
        """Get the UI component tree on Linux using AT-SPI."""
        try:
            if self._atspi is None:
                try:
                    import pyatspi

                    self._atspi = pyatspi
                except ImportError:
                    self.logger.error(
                        "pyatspi not available. Install with: pip install pyatspi"
                    )
                    return LayoutTreeObservation(
                        tree={"error": "pyatspi not available"}
                    )
            pyatspi = self._atspi

            def build_tree(element):
                if not element:
                    return None
                common_props = {
                    "name": element.name if hasattr(element, "name") else None,
                    "role": (
                        element.getRole().name if hasattr(element, "getRole") else None
                    ),
                    "enabled": None,
                    "focused": None,
                    "offscreen": None,
                    "bounds": None,
                    "selected": None,
                    "checked": None,
                    "expanded": None,
                    "current_value": None,
                    "min_value": None,
                    "max_value": None,
                    "percentage": None,
                }
                platform_props = {}
                try:
                    state_set = element.getState()
                    states = {
                        state: bool(state_set.contains(getattr(pyatspi.STATE, state)))
                        for state in pyatspi.STATE_VALUE_TO_NAME.values()
                    }
                    common_props["enabled"] = states.get("ENABLED", False)
                    common_props["focused"] = states.get("FOCUSED", False)
                    common_props["selected"] = states.get("SELECTED", False)
                    platform_props["States"] = states
                except Exception:
                    pass
                children = []
                try:
                    for i in range(element.childCount):
                        child = element.getChildAtIndex(i)
                        child_tree = build_tree(child)
                        if child_tree:
                            children.append(child_tree)
                except Exception:
                    pass
                return {
                    "properties": common_props,
                    "platform": Platform.LINUX,
                    "platform_properties": platform_props,
                    "children": children,
                }

            desktop = pyatspi.Registry.getDesktop(0)
            tree = build_tree(desktop)
            return LayoutTreeObservation(tree=tree)

        except Exception as e:
            self.logger.error(f"Error getting Linux layout tree: {e}")
            return LayoutTreeObservation(tree={"error": str(e)})

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
            self.logger.warning(
                f"Command returned non-zero exit code: {result.returncode}"
            )
            raise RuntimeError(
                f"Command returned non-zero exit code: {result.returncode}"
            )

    def _run_process(self, action: RunProcessAction) -> bool:
        """Run a process with the specified parameters.

        Args:
            action: RunProcessAction containing the process parameters

        Returns:
            bool: True if the process was executed successfully
        """
        self.logger.info(f"Running process: {action.command} with args: {action.args}")

        # Prepare environment variables
        env = os.environ.copy()
        if action.env:
            env.update(action.env)

        # Run the process
        result = subprocess.run(
            [action.command] + action.args,
            cwd=action.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=action.timeout,
        )

        if result.returncode == 0:
            self.logger.info("Process executed successfully")
            return True
        else:
            self.logger.warning(
                f"Process returned non-zero exit code: {result.returncode}"
            )
            raise RuntimeError(
                f"Process returned non-zero exit code: {result.returncode}"
            )

    def _pause(self):
        """Pause the local computer.

        For local computers, pausing doesn't have a specific implementation
        as it's running on the local machine.
        """
        self.logger.info(f"Pausing {self.__class__.__name__} (no-op)")
        # No specific pause implementation for local computers

    def _resume(self, timeout_hours: Optional[float] = None):
        """Resume the local computer.

        For local computers, resuming doesn't have a specific implementation
        as it's running on the local machine.

        Args:
            timeout_hours: Not used for local computer implementations.
        """
        self.logger.info(f"Resuming {self.__class__.__name__} (no-op)")
        # No specific resume implementation for local computers

    def _find_free_port(self) -> int:
        """Find a free port to use for the video server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    @property
    def video_stream_url(self) -> str:
        """Get the URL for the video stream of the local computer instance.

        Returns:
            str: The URL for the video stream, or an empty string if video streaming is not active.
        """
        if self._video_streaming and self._video_server_port:
            return f"http://localhost:{self._video_server_port}/"
        return ""

    def start_video_stream(self) -> bool:
        """Start the video stream for the local computer instance.

        This starts a simple HTTP server that serves screenshots as a video stream.

        Returns:
            bool: True if the video stream was successfully started, False otherwise.
        """
        if self._video_streaming:
            self.logger.info("Video stream is already running")
            return True

        try:
            # Find a free port
            port = self._find_free_port()
            self._video_server_port = port

            # Create and start the HTTP server
            self.logger.info(f"Starting video stream server on port {port}")
            server = ThreadedHTTPServer(
                ("localhost", port), VideoStreamHandler, computer=self
            )

            # Run the server in a separate thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = (
                True  # So the thread will exit when the main program exits
            )
            server_thread.start()

            # Store references
            self._video_server = server
            self._video_server_thread = server_thread
            self._video_streaming = True

            self.logger.info(f"Video stream started at http://localhost:{port}/")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start video stream: {e}")
            self._video_streaming = False
            self._video_server = None
            self._video_server_thread = None
            self._video_server_port = None
            return False

    def stop_video_stream(self) -> bool:
        """Stop the video stream for the local computer instance.

        Returns:
            bool: True if the video stream was successfully stopped, False otherwise.
        """
        if not self._video_streaming:
            self.logger.info("No video stream is running")
            return True

        try:
            if self._video_server:
                self.logger.info("Stopping video stream server")
                self._video_server.shutdown()
                self._video_server.server_close()
                self._video_server = None
                self._video_server_thread = None
                self._video_streaming = False
                self.logger.info("Video stream stopped")
                return True
        except Exception as e:
            self.logger.error(f"Error stopping video stream: {e}")
            return False

        return False

    def _get_processes(self) -> ProcessesObservation:
        """Return a ProcessesObservation containing information about running processes."""
        processes_info = []

        # Get all running processes using psutil
        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "username",
                "memory_info",
                "cpu_percent",
                "create_time",
                "status",
            ]
        ):
            try:
                # Get process info as a dictionary
                proc_info = proc.info

                # Add additional information
                proc_info["memory_mb"] = (
                    proc_info["memory_info"].rss / (1024 * 1024)
                    if proc_info["memory_info"]
                    else 0
                )
                proc_info["cpu_percent"] = proc.cpu_percent(interval=0.1)

                # Format create time
                if proc_info["create_time"]:
                    proc_info["create_time"] = datetime.datetime.fromtimestamp(
                        proc_info["create_time"]
                    ).strftime("%Y-%m-%d %H:%M:%S")

                # Remove memory_info object as it's not JSON serializable
                if "memory_info" in proc_info:
                    del proc_info["memory_info"]

                # Add command line if available
                try:
                    proc_info["cmdline"] = proc.cmdline()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    proc_info["cmdline"] = []

                # Add executable path if available
                try:
                    proc_info["exe"] = proc.exe()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    proc_info["exe"] = ""

                processes_info.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        return ProcessesObservation(processes=processes_info)

    def _get_windows(self) -> WindowsObservation:
        """Return a WindowsObservation containing information about open windows."""
        system = platform.system()

        if system == "Windows":
            return self._get_windows_windows()
        elif system == "Darwin":
            return self._get_windows_macos()
        elif system == "Linux":
            return self._get_windows_linux()
        else:
            self.logger.warning(
                f"Windows information retrieval not implemented for {system}"
            )
            return WindowsObservation(windows=[])

    def _get_windows_windows(self) -> WindowsObservation:
        """Get information about open windows on Windows."""
        # Lazy import UIAutomation to avoid dependency issues on non-Windows platforms
        if self._ui_automation is None:
            try:
                import uiautomation as auto

                self._ui_automation = auto
            except ImportError:
                self.logger.error(
                    "UIAutomation not available. Install with: pip install uiautomation"
                )
                return WindowsObservation(
                    windows=[{"error": "UIAutomation not available"}]
                )

        auto = self._ui_automation

        windows_info = []

        # Get all top-level windows
        desktop = auto.GetRootControl()
        for window in desktop.GetChildren():
            # Only include actual windows (not desktop elements)
            if window.ControlTypeName == "Window" and window.Name:
                window_info = {
                    "title": window.Name,
                    "class_name": window.ClassName,
                    "handle": window.NativeWindowHandle,
                    "is_minimized": not window.IsVisible,
                    "is_maximized": window.BoundingRectangle.width()
                    == desktop.BoundingRectangle.width()
                    and window.BoundingRectangle.height()
                    == desktop.BoundingRectangle.height(),
                    "position": {
                        "left": window.BoundingRectangle.left,
                        "top": window.BoundingRectangle.top,
                        "width": window.BoundingRectangle.width(),
                        "height": window.BoundingRectangle.height(),
                    },
                    "is_focused": window.HasKeyboardFocus,
                }
                windows_info.append(window_info)

        return WindowsObservation(windows=windows_info)

    def _get_windows_macos(self) -> WindowsObservation:
        """Get information about open windows on macOS."""
        windows_info = []

        # Try to use Quartz for window information
        import Quartz

        # Get all windows
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly
            | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID,
        )

        for window in window_list:
            try:
                # Extract window information
                window_info = {
                    "title": window.get("kCGWindowName", ""),
                    "owner_name": window.get("kCGWindowOwnerName", ""),
                    "window_id": window.get("kCGWindowNumber", 0),
                    "layer": window.get("kCGWindowLayer", 0),
                    "is_on_screen": window.get("kCGWindowIsOnscreen", False),
                    "memory_usage": window.get("kCGWindowMemoryUsage", 0),
                }

                # Get window bounds
                bounds = window.get("kCGWindowBounds", {})
                if bounds:
                    window_info["position"] = {
                        "left": bounds.get("X", 0),
                        "top": bounds.get("Y", 0),
                        "width": bounds.get("Width", 0),
                        "height": bounds.get("Height", 0),
                    }

                windows_info.append(window_info)
            except Exception as e:
                self.logger.warning(f"Error processing window: {e}")

        return WindowsObservation(windows=windows_info)

    def _get_windows_linux(self) -> WindowsObservation:
        """Get information about open windows on Linux using python-ewmh."""
        try:
            from ewmh import EWMH
            from Xlib.display import Display
        except ImportError as e:
            self.logger.warning(
                "python-ewmh or python-xlib not available, falling back to parsing output"
            )
            raise e

        ewmh = EWMH()
        display = Display()
        client_list = ewmh.getClientList()
        windows_info = []

        for win in client_list:
            try:
                window_info = {}
                # Get window title using EWMH
                title = ewmh.getWmName(win)
                if title:
                    window_info["title"] = title
                else:
                    window_info["title"] = ""

                # Get window geometry from Xlib
                geom = win.get_geometry()
                abs_pos = win.query_tree().parent.get_geometry()
                position = {
                    "left": geom.x + abs_pos.x,
                    "top": geom.y + abs_pos.y,
                    "width": geom.width,
                    "height": geom.height,
                }
                window_info["position"] = position

                # Other properties, store raw properties in platform_properties
                platform_props = {}
                # Try to get WM_CLASS
                try:
                    wm_class = win.get_wm_class()
                    if wm_class:
                        platform_props["wm_class"] = wm_class
                except Exception:
                    pass

                window_info.update(platform_props)

                windows_info.append(window_info)
            except Exception as e:
                self.logger.warning(f"Error processing window: {e}")

        return WindowsObservation(windows=windows_info)

    def _get_displays(self) -> DisplaysObservation:
        """Return a DisplaysObservation containing information about connected displays."""
        displays_info = []

        # Get display information using mss
        for i, monitor in enumerate(
            self._sct.monitors[1:]
        ):  # Skip the "all monitors" entry at index 0
            display_info = {
                "id": i,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"],
                "is_primary": i == 0,  # Assume first monitor is primary
            }

            # Add platform-specific information
            system = platform.system()
            if system == "Windows":
                display_info = self._get_windows_display_info(display_info)
            elif system == "Darwin":
                display_info = self._get_macos_display_info(display_info, i)
            elif system == "Linux":
                display_info = self._get_linux_display_info(display_info, i)

            displays_info.append(display_info)

        return DisplaysObservation(displays=displays_info)

    def _get_windows_display_info(self, display_info: dict) -> dict:
        """Get Windows-specific display information."""
        if self._ui_automation:
            # No additional info from UIAutomation for displays
            pass
        return display_info

    def _get_macos_display_info(self, display_info: dict, display_index: int) -> dict:
        """Get macOS-specific display information."""
        import Quartz

        main_display = Quartz.CGMainDisplayID()
        all_displays = Quartz.CGGetActiveDisplayList(10, None, None)[1]

        if display_index < len(all_displays):
            display_id = all_displays[display_index]
            display_info["is_primary"] = display_id == main_display

            # Get additional display properties
            display_info["model"] = Quartz.CGDisplayModelNumber(display_id)
            display_info["vendor"] = Quartz.CGDisplayVendorNumber(display_id)
            display_info["serial"] = Quartz.CGDisplaySerialNumber(display_id)
            display_info["is_builtin"] = Quartz.CGDisplayIsBuiltin(display_id)
            display_info["is_online"] = Quartz.CGDisplayIsOnline(display_id)

        return display_info

    def _get_linux_display_info(self, display_info: dict, display_index: int) -> dict:
        """Get Linux-specific display information."""
        # Try to get display information using xrandr
        result = subprocess.run(["xrandr", "--query"], capture_output=True, text=True)

        if result.returncode == 0:
            lines = result.stdout.splitlines()
            displays = []

            for line in lines:
                if " connected " in line:
                    parts = line.split()
                    name = parts[0]
                    is_primary = "primary" in line

                    # Extract resolution if available
                    resolution = None
                    for part in parts:
                        if "x" in part and part[0].isdigit():
                            resolution = part.split("+")[0]
                            break

                    displays.append(
                        {
                            "name": name,
                            "is_primary": is_primary,
                            "resolution": resolution,
                        }
                    )

            # Match xrandr displays with mss monitors based on resolution
            if display_index < len(displays):
                display_info.update(displays[display_index])
        return display_info
