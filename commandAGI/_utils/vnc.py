import logging
import threading
import time
from typing import Callable, Literal, Optional

import cv2
import numpy as np
import requests
from vnc import VNCClient, VNCServer
from vnc.client import MouseButton as VNCMouseButton
from vnc.server import VNCServerScreen

from commandAGI.types import KeyboardKey, MouseButton

logger = logging.getLogger(__name__)

# Map our MouseButton enum to VNC mouse button values
MOUSE_BUTTON_MAP = {
    MouseButton.LEFT: VNCMouseButton.LEFT,
    MouseButton.RIGHT: VNCMouseButton.RIGHT,
    MouseButton.MIDDLE: VNCMouseButton.MIDDLE,
}


class HTTPStreamScreen(VNCServerScreen):
    """VNC server screen that pulls frames from an HTTP video stream."""

    def __init__(
        self,
        http_stream_url: str,
        width: int = 1920,
        height: int = 1080,
        framerate: int = 30,
        quality: int = 80,
        scale: float = 1.0,
        compression: Literal["jpeg", "png"] = "jpeg",
    ):
        """Initialize the HTTP stream screen.

        Args:
            http_stream_url: URL of the HTTP video stream
            width: Screen width
            height: Screen height
            framerate: Target frame rate for capturing
            quality: Image quality (0-100)
            scale: Scale factor for the screen (0.1-1.0)
            compression: Image compression format
        """
        # Calculate scaled dimensions
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)
        super().__init__(scaled_width, scaled_height)

        self.http_stream_url = http_stream_url
        self.framerate = framerate
        self.quality = quality
        self.compression = compression
        self._current_frame = None
        self._stream_thread = None
        self._running = False

    def start(self):
        """Start the frame capture thread."""
        self._running = True
        self._stream_thread = threading.Thread(target=self._capture_frames)
        self._stream_thread.daemon = True
        self._stream_thread.start()

    def stop(self):
        """Stop the frame capture thread."""
        self._running = False
        if self._stream_thread:
            self._stream_thread.join()

    def _capture_frames(self):
        """Continuously capture frames from the HTTP stream."""
        try:
            # Open HTTP stream
            stream = requests.get(self.http_stream_url, stream=True)
            bytes_buffer = bytes()
            frame_interval = 1.0 / self.framerate

            last_frame_time = time.time()

            for chunk in stream.iter_content(chunk_size=1024):
                if not self._running:
                    break

                # Throttle frame rate
                current_time = time.time()
                if current_time - last_frame_time < frame_interval:
                    continue

                bytes_buffer += chunk
                a = bytes_buffer.find(b"\xff\xd8")  # JPEG start
                b = bytes_buffer.find(b"\xff\xd9")  # JPEG end

                if a != -1 and b != -1:
                    img_data = bytes_buffer[a : b + 2]
                    bytes_buffer = bytes_buffer[b + 2 :]

                    # Convert to numpy array
                    frame = cv2.imdecode(
                        np.frombuffer(img_data, dtype=np.uint8), cv2.IMREAD_COLOR
                    )

                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Apply quality and compression settings
                    if self.compression == "jpeg":
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                        _, frame = cv2.imencode(".jpg", frame, encode_param)
                        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                    else:  # png
                        encode_param = [
                            cv2.IMWRITE_PNG_COMPRESSION,
                            9 - (self.quality // 10),
                        ]
                        _, frame = cv2.imencode(".png", frame, encode_param)
                        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                    # Update current frame
                    self._current_frame = frame
                    last_frame_time = current_time

                    # Notify VNC server of screen update
                    self.updated.set()

        except Exception as e:
            logger.error(f"Error capturing frames: {e}")
            self._running = False

    def get_screen(self) -> np.ndarray:
        """Get the current screen content."""
        if self._current_frame is None:
            # Return black screen if no frame available
            return np.zeros((self.height, self.width, 3), dtype=np.uint8)
        return self._current_frame


class HTTPStreamVNCServer:
    """VNC server that proxies an HTTP video stream and handles input events."""

    def __init__(
        self,
        http_stream_url: str,
        host: str = "localhost",
        port: int = 5900,
        password: str = "commandagi",
        shared: bool = True,
        framerate: int = 30,
        quality: int = 80,
        encoding: Literal["raw", "tight", "zrle"] = "tight",
        compression_level: int = 6,
        scale: float = 1.0,
        allow_clipboard: bool = True,
        view_only: bool = False,
        allow_resize: bool = True,
        on_mouse_move: Optional[Callable[[int, int], None]] = None,
        on_mouse_click: Optional[Callable[[int, int, MouseButton], None]] = None,
        on_mouse_down: Optional[Callable[[MouseButton], None]] = None,
        on_mouse_up: Optional[Callable[[MouseButton], None]] = None,
        on_key_press: Optional[Callable[[KeyboardKey], None]] = None,
        on_key_down: Optional[Callable[[KeyboardKey], None]] = None,
        on_key_up: Optional[Callable[[KeyboardKey], None]] = None,
    ):
        """Initialize the VNC server.

        Args:
            http_stream_url: URL of the HTTP video stream to proxy
            host: VNC server host address
            port: VNC server port
            password: VNC server password
            shared: Allow multiple simultaneous connections
            framerate: Target frame rate for the VNC stream
            quality: Image quality level (0-100)
            encoding: VNC encoding method to use
            compression_level: Compression level (0-9)
            scale: Scale factor for the VNC display (0.1-1.0)
            allow_clipboard: Enable clipboard sharing
            view_only: Disable input from VNC clients
            allow_resize: Allow clients to resize the display
            on_mouse_move: Callback for mouse movement
            on_mouse_click: Callback for mouse clicks
            on_mouse_down: Callback for mouse button down
            on_mouse_up: Callback for mouse button up
            on_key_press: Callback for key press
            on_key_down: Callback for key down
            on_key_up: Callback for key up
        """
        self.http_stream_url = http_stream_url
        self.host = host
        self.port = port
        self.password = password
        self.shared = shared
        self.view_only = view_only
        self.allow_clipboard = allow_clipboard
        self.allow_resize = allow_resize

        # Store callback handlers
        self.on_mouse_move = on_mouse_move
        self.on_mouse_click = on_mouse_click
        self.on_mouse_down = on_mouse_down
        self.on_mouse_up = on_mouse_up
        self.on_key_press = on_key_press
        self.on_key_down = on_key_down
        self.on_key_up = on_key_up

        # Create screen with streaming parameters
        self.screen = HTTPStreamScreen(
            http_stream_url,
            framerate=framerate,
            quality=quality,
            scale=scale,
            compression="jpeg" if encoding == "tight" else "png",
        )

        # Create VNC server with configuration
        self.server = VNCServer(
            self.screen,
            password=password,
            shared=shared,
            encoding=encoding,
            compression_level=compression_level,
            allow_clipboard=allow_clipboard,
            view_only=view_only,
            allow_resize=allow_resize,
        )

        # Set up event handlers
        self.server.on_client_connected = self._handle_client_connected
        self.server.on_client_disconnected = self._handle_client_disconnected

        self._server_thread = None
        self._running = False

    def start(self):
        """Start the VNC server."""
        if self._running:
            return

        self._running = True

        # Start screen capture
        self.screen.start()

        # Start server in a separate thread
        self._server_thread = threading.Thread(target=self._run_server)
        self._server_thread.daemon = True
        self._server_thread.start()

    def stop(self):
        """Stop the VNC server."""
        if not self._running:
            return

        self._running = False

        # Stop screen capture
        self.screen.stop()

        # Stop server
        self.server.close()

        if self._server_thread:
            self._server_thread.join()

    def _run_server(self):
        """Run the VNC server."""
        try:
            self.server.listen(self.host, self.port)
            while self._running:
                self.server.handle_request()
        except Exception as e:
            logger.error(f"VNC server error: {e}")
            self._running = False

    def _handle_client_connected(self, client: VNCClient):
        """Handle VNC client connection."""
        logger.info(f"VNC client connected from {client.address}")

        # Set up input handlers for this client
        client.on_key_event = self._handle_key_event
        client.on_pointer_event = self._handle_pointer_event

    def _handle_client_disconnected(self, client: VNCClient):
        """Handle VNC client disconnection."""
        logger.info(f"VNC client disconnected from {client.address}")

    def _handle_key_event(self, client: VNCClient, key: int, down: bool):
        """Handle keyboard events from VNC client."""
        try:
            # Convert VNC key code to our KeyboardKey enum
            key_name = chr(key).lower()
            if not KeyboardKey.is_valid_key(key_name):
                return

            key_enum = KeyboardKey(key_name)

            if down:
                if self.on_key_down:
                    self.on_key_down(key_enum)
            else:
                if self.on_key_up:
                    self.on_key_up(key_enum)
                if self.on_key_press:
                    self.on_key_press(key_enum)

        except Exception as e:
            logger.error(f"Error handling key event: {e}")

    def _handle_pointer_event(
        self, client: VNCClient, x: int, y: int, button_mask: int
    ):
        """Handle mouse events from VNC client."""
        try:
            # Handle mouse movement
            if self.on_mouse_move:
                self.on_mouse_move(x, y)

            # Handle button events
            for button in MouseButton:
                vnc_button = MOUSE_BUTTON_MAP[button]
                button_pressed = bool(button_mask & vnc_button)

                if button_pressed:
                    if self.on_mouse_down:
                        self.on_mouse_down(button)
                    if self.on_mouse_click:
                        self.on_mouse_click(x, y, button)
                else:
                    if self.on_mouse_up:
                        self.on_mouse_up(button)

        except Exception as e:
            logger.error(f"Error handling pointer event: {e}")
