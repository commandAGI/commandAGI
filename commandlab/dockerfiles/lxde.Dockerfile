FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0

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

# Create startup script
RUN echo '#!/bin/bash\n\
Xvfb :0 -screen 0 1024x768x24 &\n\
sleep 2\n\
export DISPLAY=:0\n\
lxsession &\n\
x11vnc -forever -display :0 -passwd secret' > /start.sh && \
    chmod +x /start.sh

# Expose the VNC port
EXPOSE 5900

# Start services
CMD ["/start.sh"]
