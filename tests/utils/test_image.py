import base64
import io
import unittest
from PIL import Image

from commandAGI.utils.image import b64ToImage, imageToB64, imageToBytes, bytesToImage


class TestImageUtils(unittest.TestCase):
    def setUp(self):
        # Create test images of different sizes and colors
        self.red_1x1 = Image.new("RGB", (1, 1), color="red")
        self.blue_10x10 = Image.new("RGB", (10, 10), color="blue")
        self.green_100x50 = Image.new("RGB", (100, 50), color="green")

        # Create base64 strings for testing
        buffer = io.BytesIO()
        self.red_1x1.save(buffer, format="PNG")
        self.red_1x1_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        buffer = io.BytesIO()
        self.blue_10x10.save(buffer, format="PNG")
        self.blue_10x10_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        buffer = io.BytesIO()
        self.green_100x50.save(buffer, format="PNG")
        self.green_100x50_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Create bytes for testing
        buffer = io.BytesIO()
        self.red_1x1.save(buffer, format="PNG")
        self.red_1x1_bytes = buffer.getvalue()

        buffer = io.BytesIO()
        self.blue_10x10.save(buffer, format="PNG")
        self.blue_10x10_bytes = buffer.getvalue()

    def test_b64ToImage(self):
        # Test converting base64 to image
        red_img = b64ToImage(self.red_1x1_b64)
        self.assertEqual(red_img.size, (1, 1))
        self.assertEqual(red_img.getpixel((0, 0)), (255, 0, 0))

        blue_img = b64ToImage(self.blue_10x10_b64)
        self.assertEqual(blue_img.size, (10, 10))
        self.assertEqual(blue_img.getpixel((5, 5)), (0, 0, 255))

        green_img = b64ToImage(self.green_100x50_b64)
        self.assertEqual(green_img.size, (100, 50))
        self.assertEqual(green_img.getpixel((50, 25)), (0, 128, 0))

    def test_imageToB64(self):
        # Test converting image to base64
        red_b64 = imageToB64(self.red_1x1)
        self.assertIsInstance(red_b64, str)
        self.assertTrue(len(red_b64) > 0)

        # Verify round-trip conversion
        round_trip_img = b64ToImage(red_b64)
        self.assertEqual(round_trip_img.size, (1, 1))

        # Test with different image sizes
        blue_b64 = imageToB64(self.blue_10x10)
        self.assertIsInstance(blue_b64, str)
        self.assertTrue(len(blue_b64) > 0)

        green_b64 = imageToB64(self.green_100x50)
        self.assertIsInstance(green_b64, str)
        self.assertTrue(len(green_b64) > 0)

    def test_imageToBytes(self):
        # Test converting image to bytes
        red_bytes = imageToBytes(self.red_1x1)
        self.assertIsInstance(red_bytes, bytes)
        self.assertTrue(len(red_bytes) > 0)

        # Test with different image sizes
        blue_bytes = imageToBytes(self.blue_10x10)
        self.assertIsInstance(blue_bytes, bytes)
        self.assertTrue(len(blue_bytes) > 0)

        green_bytes = imageToBytes(self.green_100x50)
        self.assertIsInstance(green_bytes, bytes)
        self.assertTrue(len(green_bytes) > 0)

    def test_bytesToImage(self):
        # Test converting bytes to image
        red_img = bytesToImage(self.red_1x1_bytes)
        self.assertEqual(red_img.size, (1, 1))

        blue_img = bytesToImage(self.blue_10x10_bytes)
        self.assertEqual(blue_img.size, (10, 10))

        # Test round-trip conversion
        img_bytes = imageToBytes(self.green_100x50)
        round_trip_img = bytesToImage(img_bytes)
        self.assertEqual(round_trip_img.size, (100, 50))

    def test_full_conversion_cycle(self):
        # Test full conversion cycle: Image -> B64 -> Image -> Bytes -> Image
        original_img = self.blue_10x10

        # Image to base64
        b64_str = imageToB64(original_img)

        # Base64 to image
        img_from_b64 = b64ToImage(b64_str)
        self.assertEqual(img_from_b64.size, original_img.size)

        # Image to bytes
        img_bytes = imageToBytes(img_from_b64)

        # Bytes to image
        final_img = bytesToImage(img_bytes)
        self.assertEqual(final_img.size, original_img.size)


if __name__ == "__main__":
    unittest.main()
