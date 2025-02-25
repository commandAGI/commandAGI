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
