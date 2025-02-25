#!/usr/bin/env python3
"""
CommandLAB Getting Started Example

This example demonstrates how to import the CommandLAB library and print its version.
"""

from commandLAB.version import __version__, get_package_version, get_container_version

def main():
    print(f"CommandLAB Version: {__version__}")
    print(f"Package Version: {get_package_version()}")
    print(f"Container Version: {get_container_version()}")
    
    print("\nCommandLAB is a framework for automating and controlling computers.")
    print("This example demonstrates the basic import and version information.")

if __name__ == "__main__":
    main()
