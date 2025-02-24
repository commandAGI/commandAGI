FROM ubuntu:20.04

ARG VERSION=latest
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0
ENV COMMANDLAB_VERSION=$VERSION

# Install LXDE, VNC server, xdotool, Python, and other required packages
RUN apt-get update && apt-get install -y \
    lxde-core \
    lxterminal \
    x11vnc \
    xvfb \
    xdotool \
    sudo \
    dbus-x11 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install CommandLAB with specific version
RUN pip3 install commandlab[local,daemon]==${COMMANDLAB_VERSION}

# Configure VNC by setting a password (using 'secret' as default)
RUN mkdir -p /root/.vnc && \
    x11vnc -storepasswd secret /root/.vnc/passwd

# Create startup script that launches both VNC and the daemon
RUN echo '#!/bin/bash\n\
Xvfb :0 -screen 0 1024x768x24 &\n\
sleep 2\n\
export DISPLAY=:0\n\
lxsession &\n\
x11vnc -forever -display :0 -passwd secret &\n\
python3 -m commandlab.daemon.daemon --port 8000 --backend pynput' > /start.sh && \
    chmod +x /start.sh

# Expose both VNC and daemon ports
EXPOSE 5900 8000

# Start services
CMD ["/start.sh"] 