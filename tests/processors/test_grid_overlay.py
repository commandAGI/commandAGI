import unittest
from PIL import Image, ImageDraw

from commandLAB.processors.grid_overlay import overlay_grid


class TestGridOverlay(unittest.TestCase):
    def setUp(self):
        # Create test images of different sizes
        self.white_100x100 = Image.new("RGB", (100, 100), color="white")
        self.black_200x150 = Image.new("RGB", (200, 150), color="black")
        self.blue_300x200 = Image.new("RGB", (300, 200), color="blue")

    def test_overlay_grid_dimensions(self):
        # Test that the output image has the same dimensions as the input
        result_100x100 = overlay_grid(self.white_100x100)
        self.assertEqual(result_100x100.size, (100, 100))

        result_200x150 = overlay_grid(self.black_200x150)
        self.assertEqual(result_200x150.size, (200, 150))

        result_300x200 = overlay_grid(self.blue_300x200)
        self.assertEqual(result_300x200.size, (300, 200))

    def test_overlay_grid_different_sizes(self):
        # Test with different grid sizes
        result_grid_50 = overlay_grid(self.white_100x100, grid_px_size=50)
        self.assertEqual(result_grid_50.size, (100, 100))

        result_grid_25 = overlay_grid(self.white_100x100, grid_px_size=25)
        self.assertEqual(result_grid_25.size, (100, 100))

        result_grid_10 = overlay_grid(self.white_100x100, grid_px_size=10)
        self.assertEqual(result_grid_10.size, (100, 100))

    def test_overlay_grid_creates_copy(self):
        # Test that the function creates a copy and doesn't modify the original
        original = self.white_100x100.copy()
        result = overlay_grid(self.white_100x100)

        # Check that the original is unchanged
        self.assertEqual(self.white_100x100.getpixel((0, 0)), (255, 255, 255))

        # Check that the result is different from the original
        self.assertIsNot(result, self.white_100x100)

    def test_overlay_grid_adds_red_lines(self):
        # Test that the grid lines are red
        result = overlay_grid(self.white_100x100, grid_px_size=50)

        # Check that grid lines are red
        # Vertical line at x=0
        self.assertEqual(result.getpixel((0, 25)), (255, 0, 0))
        # Vertical line at x=50
        self.assertEqual(result.getpixel((50, 25)), (255, 0, 0))
        # Horizontal line at y=0
        self.assertEqual(result.getpixel((25, 0)), (255, 0, 0))
        # Horizontal line at y=50
        self.assertEqual(result.getpixel((25, 50)), (255, 0, 0))

        # Check that non-grid areas maintain original color
        # Center of first cell
        self.assertEqual(result.getpixel((25, 25)), (255, 255, 255))

    def test_overlay_grid_with_odd_dimensions(self):
        # Test with dimensions that aren't multiples of the grid size
        odd_img = Image.new("RGB", (123, 77), color="white")
        result = overlay_grid(odd_img, grid_px_size=50)

        # Check dimensions are preserved
        self.assertEqual(result.size, (123, 77))

        # Check grid lines
        self.assertEqual(result.getpixel((0, 25)), (255, 0, 0))  # Vertical line at x=0
        self.assertEqual(
            result.getpixel((50, 25)), (255, 0, 0)
        )  # Vertical line at x=50
        self.assertEqual(
            result.getpixel((100, 25)), (255, 0, 0)
        )  # Vertical line at x=100

    def test_overlay_grid_with_small_image(self):
        # Test with image smaller than grid size
        small_img = Image.new("RGB", (30, 30), color="white")
        result = overlay_grid(small_img, grid_px_size=50)

        # Check dimensions are preserved
        self.assertEqual(result.size, (30, 30))

        # Check that at least the origin grid line is drawn
        self.assertEqual(result.getpixel((0, 15)), (255, 0, 0))  # Vertical line at x=0
        self.assertEqual(
            result.getpixel((15, 0)), (255, 0, 0)
        )  # Horizontal line at y=0


if __name__ == "__main__":
    unittest.main()
