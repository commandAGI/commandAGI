#!/usr/bin/env python3
"""
commandAGI Getting Started Example

This example demonstrates how to import the commandAGI library and print its version.

Status: ✅ Works perfectly
- Correctly displays version information
"""

from commandAGI.version import __version__, get_package_version, get_container_version


def main():
    print(f"commandAGI Version: {__version__}")
    print(f"Package Version: {get_package_version()}")
    print(f"Container Version: {get_container_version()}")

    print("\ncommandAGI2 is a framework for automating and controlling computers.")
    print("This example demonstrates the basic import and version information.")


if __name__ == "__main__":
    main()
