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

# needd for screen reader
# RUN apt-get update && apt-get install -y \
#     python3-pyatspi2 \
#     && rm -rf /var/lib/apt/lists/*
    
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

# Execute setup script (using the already copied script)
RUN chmod +x /commandlab/resources/docker/setup.sh
RUN /commandlab/resources/docker/setup.sh

# Make startup script executable (using the already copied script)
RUN chmod +x /commandlab/resources/docker/start.sh

# Expose both VNC and daemon ports
EXPOSE 5900 8000

# Start services
# leading /commandlab is fine bec this is an abs path
# but we are already in the commandlab directory so just ./resources/docker/start.sh would be fine also
CMD ["/commandlab/resources/docker/start.sh"]
