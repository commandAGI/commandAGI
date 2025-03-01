#!/bin/bash

echo "Starting commandlab daemon..."

# Get port from environment variable or use default
PORT=${DAEMON_PORT:-8000}
echo "Using port: $PORT"

# Start display services in background
Xvfb :0 -screen 0 1024x768x24 &
sleep 5  # Increased sleep time to ensure display is ready

# Create .Xauthority file if it doesn't exist
touch ~/.Xauthority

# Set up X authentication properly
xauth add :0 . $(mcookie)

# Set display environment variable
export DISPLAY=:0

# Start window manager
lxsession &
sleep 2  # Give lxsession time to initialize

# Start VNC server with proper authentication
x11vnc -forever -display :0 -passwd secret -auth ~/.Xauthority &
sleep 2  # Give VNC server time to initialize

# Activate virtual environment and run daemon in foreground
source .venv/bin/activate
python3 -m commandLAB.daemon.cli --port $PORT --backend pynput --token "$DAEMON_TOKEN"
