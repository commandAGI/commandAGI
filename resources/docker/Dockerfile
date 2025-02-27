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
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.12 python3.12-venv python3.12-dev python3-distutils && \
    ln -sf /usr/bin/python3.12 /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

# Test Python version and fail if not 3.12
RUN python3 -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"'

# Update pip and install required packages
RUN python3 -m ensurepip --upgrade 
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
RUN python3 -m pip install --upgrade six
RUN python3 -m pip install --upgrade urllib3

# Copy the local codebase
COPY . /commandlab
WORKDIR /commandlab

# Install dependencies using pip
RUN apt-get update
RUN apt-get install -y libssl-dev openssl

RUN python3 -c "import platform; print('Python Platform:', platform.platform())"

# Install the package and its dependencies
RUN echo "Starting base package installation..." && \
    python3 -m pip install -e . && \
    echo "Successfully installed base package"

RUN echo "Starting optional dependencies installation..." && \
    python3 -m pip install -e ".[local,daemon-host]" && \
    echo "Successfully installed optional dependencies"

WORKDIR /

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