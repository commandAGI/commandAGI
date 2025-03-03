#!/bin/bash

echo "Installing commandagi2 dependencies..."

# install uv
pip install uv

# Create virtual environment using uv
uv venv --python 3.12

# Ensure we're using the virtual environment
source .venv/bin/activate

# Install the package in development mode
uv pip install -e ".[all]"

# Verify installation
python3 -c "import commandAGI2" || echo "Failed to install commandagi2 package"

# Configure VNC by setting a password
mkdir -p /root/.vnc
touch /root/.Xauthority  # Create empty Xauthority file
x11vnc -storepasswd secret /root/.vnc/passwd 