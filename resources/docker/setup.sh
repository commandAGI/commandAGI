#!/bin/bash

# Configure VNC by setting a password
mkdir -p /root/.vnc
x11vnc -storepasswd secret /root/.vnc/passwd 