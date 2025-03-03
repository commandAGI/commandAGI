# This file is automatically updated by the build system
__version__ = "0.1.0"

# Container/image version might be different from package version
CONTAINER_VERSION = "latest"  # Default to 'latest' if not specified


def get_container_version():
    """Get the container version to use for deployments"""
    return CONTAINER_VERSION


def get_package_version():
    """Get the package version"""
    return __version__
