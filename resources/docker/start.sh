#!/bin/bash

# Start display services in background
Xvfb :0 -screen 0 1024x768x24 &
sleep 2
export DISPLAY=:0
lxsession &
x11vnc -forever -display :0 -passwd secret &

# Activate virtual environment and run daemon in foreground
source /commandlab/.venv/bin/activate
exec python3 -m commandlab.daemon.daemon --port 8000 --backend pynput
