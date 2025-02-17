FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install LXDE, VNC server, xdotool, and other required packages
RUN apt-get update && apt-get install -y \
    lxde-core \
    lxterminal \
    x11vnc \
    xvfb \
    xdotool \
    sudo \
    dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

# Configure VNC by setting a password (using 'secret' as default)
RUN mkdir -p /root/.vnc && \
    x11vnc -storepasswd secret /root/.vnc/passwd

# Expose the VNC port
EXPOSE 5900

# Start an X server (Xvfb), the LXDE session, and the VNC server.
CMD ["bash", "-c", "Xvfb :0 -screen 0 1024x768x24 & lxsession & x11vnc -forever -display :0 -passwd secret"] 