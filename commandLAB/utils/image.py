import base64
import io
from PIL import Image

def b64ToImage(b64: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64)))

def imageToB64(image: Image.Image) -> str:
    return base64.b64encode(image.tobytes()).decode("utf-8")

def imageToBytes(image: Image.Image) -> bytes:
    return image.tobytes()

def bytesToImage(bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(bytes))
