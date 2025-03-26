import base64
import datetime
import io
import os
from typing import Any, Literal

try:
    from PIL import Image
except ImportError:
    Image = None  # PIL is optional

from commandAGI._internal.config import APPDIR
from commandAGI.types import ScreenshotObservation


def process_screenshot(
    screenshot_data: Any,
    output_format: Literal["base64", "PIL", "path"] = "PIL",
    input_format: Literal["bytes", "PIL", "path", "base64"] = None,
    computer_name: str = "computer",
    cleanup_temp_file: bool = True,
) -> ScreenshotObservation:
    """Process a screenshot into the requested format.

    Args:
        screenshot_data: The screenshot data to process
        output_format: Format to return the screenshot in. Options are:
            - 'base64': Return the screenshot as a base64 encoded string
            - 'PIL': Return the screenshot as a PIL Image object
            - 'path': Save the screenshot to a file and return the path
        input_format: Format of the input data. If None, will be auto-detected. Options are:
            - 'bytes': Raw image data as bytes
            - 'PIL': A PIL Image object
            - 'path': Path to an image file
            - 'base64': Base64 encoded string
        computer_name: Name of the computer implementation (used in filename)
        cleanup_temp_file: Whether to delete the temporary file if screenshot_data is a path

    Returns:
        ScreenshotObservation with the screenshot in the requested format
    """
    # Auto-detect input format if not specified
    if input_format is None:
        if isinstance(screenshot_data, bytes):
            input_format = "bytes"
        elif Image and isinstance(screenshot_data, Image.Image):
            input_format = "PIL"
        elif isinstance(screenshot_data, str):
            # Check if it's a base64 string or a file path
            if os.path.exists(screenshot_data):
                input_format = "path"
            else:
                try:
                    base64.b64decode(screenshot_data)
                    input_format = "base64"
                except BaseException:
                    # Default to path if we can't determine
                    input_format = "path"
        else:
            raise ValueError(
                f"Unsupported screenshot data type: {type(screenshot_data)}"
            )

    # First convert input to a common intermediate format (PIL Image)
    img = None
    temp_file = None

    match input_format:
        case "bytes":
            if output_format == "base64":
                # Direct conversion without PIL
                b64_screenshot = base64.b64encode(screenshot_data).decode("utf-8")
                return ScreenshotObservation(screenshot=b64_screenshot)
            elif Image is not None:
                img = Image.open(io.BytesIO(screenshot_data))
            else:
                # If PIL is not available, we need to save to a temp file first
                temp_file = os.path.join(
                    APPDIR,
                    "temp",
                    f"{computer_name}_temp_{
                        datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png",
                )
                os.makedirs(os.path.dirname(temp_file), exist_ok=True)
                with open(temp_file, "wb") as f:
                    f.write(screenshot_data)

        case "PIL":
            if Image is None:
                raise ImportError("PIL is required for PIL format input")
            img = screenshot_data

        case "path":
            temp_file = screenshot_data
            if output_format == "path" and os.path.dirname(
                screenshot_data
            ) == os.path.join(APPDIR, "screenshots"):
                # Already in the right location
                return ScreenshotObservation(screenshot=screenshot_data)
            elif Image is not None and output_format != "path":
                img = Image.open(screenshot_data)

        case "base64":
            if output_format == "base64":
                # Already in the right format
                return ScreenshotObservation(screenshot=screenshot_data)

            # Decode base64 to bytes
            img_data = base64.b64decode(screenshot_data)

            if output_format == "path":
                # Save directly to file
                screenshots_dir = os.path.join(APPDIR, "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filepath = os.path.join(
                    screenshots_dir, f"{computer_name}_screenshot_{timestamp}.png"
                )

                with open(filepath, "wb") as f:
                    f.write(img_data)

                return ScreenshotObservation(screenshot=filepath)
            elif Image is not None:
                img = Image.open(io.BytesIO(img_data))
            else:
                # If PIL is not available, we need to save to a temp file first
                temp_file = os.path.join(
                    APPDIR,
                    "temp",
                    f"{computer_name}_temp_{
                        datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png",
                )
                os.makedirs(os.path.dirname(temp_file), exist_ok=True)
                with open(temp_file, "wb") as f:
                    f.write(img_data)

    # Now convert to the output format
    match output_format:
        case "base64":
            if img is not None:
                # Convert PIL Image to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                b64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return ScreenshotObservation(screenshot=b64_screenshot)
            elif temp_file is not None:
                # Read file and convert to base64
                with open(temp_file, "rb") as f:
                    file_data = f.read()

                b64_screenshot = base64.b64encode(file_data).decode("utf-8")

                # Clean up temporary file if requested
                if cleanup_temp_file and input_format == "path":
                    try:
                        os.remove(temp_file)
                    except BaseException:
                        pass

                return ScreenshotObservation(screenshot=b64_screenshot)

        case "PIL":
            if img is not None:
                return ScreenshotObservation(screenshot=img)
            elif temp_file is not None and Image is not None:
                # Read file into PIL Image
                img = Image.open(temp_file)

                # Clean up temporary file if requested
                if cleanup_temp_file and input_format == "path":
                    try:
                        os.remove(temp_file)
                    except BaseException:
                        pass

                return ScreenshotObservation(screenshot=img)
            else:
                raise ImportError("PIL is required for PIL format output")

        case "path":
            screenshots_dir = os.path.join(APPDIR, "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filepath = os.path.join(
                screenshots_dir, f"{computer_name}_screenshot_{timestamp}.png"
            )

            if img is not None:
                # Save PIL Image to file
                img.save(filepath, format="PNG")
                return ScreenshotObservation(screenshot=filepath)
            elif temp_file is not None:
                # Move/copy the file to the screenshots directory
                if Image is not None:
                    # Use PIL to read and save (handles format conversion if
                    # needed)
                    img = Image.open(temp_file)
                    img.save(filepath)
                else:
                    # Simple file copy
                    with open(temp_file, "rb") as src, open(filepath, "wb") as dst:
                        dst.write(src.read())

                # Clean up temporary file if requested
                if cleanup_temp_file and input_format == "path":
                    try:
                        os.remove(temp_file)
                    except BaseException:
                        pass

                return ScreenshotObservation(screenshot=filepath)

    # If we get here, we couldn't process the screenshot
    raise ValueError(
        f"Failed to process screenshot from {input_format} to {output_format}"
    )


import base64
import io

from PIL import Image


def b64ToImage(b64: str) -> Image.Image:
    """
    Convert a base64 encoded image string to a PIL Image.

    Args:
        b64: Base64 encoded image string

    Returns:
        PIL Image object

    Examples:
        >>> # This example shows the pattern but won't actually run in doctest
        >>> import base64
        >>> from PIL import Image
        >>> # Create a small red 1x1 pixel image
        >>> img = Image.new('RGB', (1, 1), color='red')
        >>> buffer = io.BytesIO()
        >>> img.save(buffer, format="PNG")
        >>> b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        >>> result_img = b64ToImage(b64_str)
        >>> result_img.size
        (1, 1)
        >>> result_img.getpixel((0, 0))
        (255, 0, 0)
    """
    return Image.open(io.BytesIO(base64.b64decode(b64)))


def imageToB64(image: Image.Image) -> str:
    """
    Convert a PIL Image to a base64 encoded string.

    Args:
        image: PIL Image object

    Returns:
        Base64 encoded string of the image

    Examples:
        >>> # This example shows the pattern but won't actually run in doctest
        >>> from PIL import Image
        >>> img = Image.new('RGB', (1, 1), color='red')
        >>> b64_str = imageToB64(img)
        >>> isinstance(b64_str, str)
        True
        >>> len(b64_str) > 0
        True
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def imageToBytes(image: Image.Image) -> bytes:
    """
    Convert a PIL Image to bytes.

    Args:
        image: PIL Image object

    Returns:
        Bytes representation of the image

    Examples:
        >>> # This example shows the pattern but won't actually run in doctest
        >>> from PIL import Image
        >>> img = Image.new('RGB', (1, 1), color='red')
        >>> img_bytes = imageToBytes(img)
        >>> isinstance(img_bytes, bytes)
        True
        >>> len(img_bytes) > 0
        True
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def bytesToImage(bytes_data: bytes) -> Image.Image:
    """
    Convert bytes to a PIL Image.

    Args:
        bytes_data: Bytes representation of an image

    Returns:
        PIL Image object

    Examples:
        >>> # This example shows the pattern but won't actually run in doctest
        >>> from PIL import Image
        >>> import io
        >>> img = Image.new('RGB', (1, 1), color='red')
        >>> buffer = io.BytesIO()
        >>> img.save(buffer, format="PNG")
        >>> result_img = bytesToImage(buffer.getvalue())
        >>> result_img.size
        (1, 1)
        >>> result_img.getpixel((0, 0))
        (255, 0, 0)
    """
    return Image.open(io.BytesIO(bytes_data))
