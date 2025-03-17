from http.server import BaseHTTPRequestHandler

# NOTE: this should really be consolidated into the daemon server


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

        # Create a request handler class that includes a reference to the
        # computer
        class Handler(RequestHandlerClass):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, computer=computer, **kwargs)

        super().__init__(server_address, Handler)
