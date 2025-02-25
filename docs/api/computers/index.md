# Computers API

This section contains documentation for the computer control interfaces and implementations. Computers are the core abstraction in CommandLAB that provide a unified interface for controlling different types of computers.

## Base Classes

- **[Base Computer](base_computer.md)** - Abstract base class defining the computer interface

## Computer Implementations

- **[Local Pynput Computer](local_pynput_computer.md)** - Control the local computer using the Pynput library
- **[Local PyAutoGUI Computer](local_pyautogui_computer.md)** - Control the local computer using the PyAutoGUI library
- **[E2B Desktop Computer](e2b_desktop_computer.md)** - Control a computer using the E2B Desktop API
- **[Daemon Client Computer](daemon_client_computer.md)** - Control a remote computer via the CommandLAB daemon

## Subcomponents

- **[Provisioners](provisioners/index.md)** - Environment provisioning for different platforms (Docker, Kubernetes, cloud providers, etc.)
