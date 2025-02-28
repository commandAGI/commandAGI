#!/bin/bash

# confirm we're in the commandlab directory
pwd
ls -a

# install uv
pip install uv

# Create virtual environment
uv venv --python 3.12

# Ensure we're using the virtual environment
source .venv/bin/activate

# Install the package in development mode
uv pip install -e ".[all]"

# Verify installation
python3 -c "import commandLAB" || echo "Failed to install commandlab package"

# Configure VNC by setting a password
mkdir -p /root/.vnc
x11vnc -storepasswd secret /root/.vnc/passwd 