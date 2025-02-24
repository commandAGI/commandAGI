# Installation

CommandLAB can be installed with different feature sets depending on your needs.

## Basic Installation

```bash
pip install commandlab
```

This installs the core framework without specific backends.

## Installation with Backends

### Local Control

```bash
pip install commandlab[local]
```

This installs dependencies for controlling your local computer (PyAutoGUI and pynput).

### Remote Daemon

```bash
pip install commandlab[daemon]
```

Installs the daemon server for remote control.

### Cloud Providers

```bash
pip install commandlab[aws,azure,gcp]
```

Installs dependencies for cloud deployments.

### All Features

```bash
pip install commandlab[all]
```

Installs all available backends and features.

## Development Installation

For contributing to CommandLAB:

```bash
git clone https://github.com/your-org/commandlab.git
cd commandlab
pip install -e ".[dev]"
```

## System Requirements

- Python 3.9+
- For local control: 
  - Windows, macOS, or Linux with GUI
  - Appropriate permissions for input control
- For cloud deployments:
  - Appropriate cloud provider credentials