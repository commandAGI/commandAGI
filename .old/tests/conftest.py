import pytest
import os
import shutil


@pytest.fixture(autouse=True)
def cleanup_test_data():
    # Setup
    yield
    # Cleanup
    if os.path.exists("test_data"):
        shutil.rmtree("test_data")
