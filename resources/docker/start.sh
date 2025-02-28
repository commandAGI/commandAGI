#!/bin/bash

# confirm we're in the commandlab directory
pwd
ls -a

# Start display services in background
Xvfb :0 -screen 0 1024x768x24 &
sleep 2
export DISPLAY=:0
lxsession &
x11vnc -forever -display :0 -passwd secret &

# Activate virtual environment and run daemon in foreground
source .venv/bin/activate
exec python3 -m commandLAB.daemon.cli --port 8000 --backend pynput
