import unittest
import re

from commandAGI.version import (
    __version__,
    CONTAINER_VERSION,
    get_container_version,
    get_package_version,
)


class TestVersion(unittest.TestCase):
    def test_version_format(self):
        # Test that __version__ follows semantic versioning format (major.minor.patch)
        version_pattern = r"^\d+\.\d+\.\d+$"
        self.assertTrue(
            re.match(version_pattern, __version__),
            f"Version '{__version__}' does not match semantic versioning format",
        )

    def test_container_version(self):
        # Test that CONTAINER_VERSION is a string
        self.assertIsInstance(CONTAINER_VERSION, str)

        # Test that CONTAINER_VERSION is not empty
        self.assertTrue(len(CONTAINER_VERSION) > 0)

    def test_get_container_version(self):
        # Test that get_container_version returns CONTAINER_VERSION
        self.assertEqual(get_container_version(), CONTAINER_VERSION)

    def test_get_package_version(self):
        # Test that get_package_version returns __version__
        self.assertEqual(get_package_version(), __version__)


if __name__ == "__main__":
    unittest.main()
