# LTE Network Simulator with Ettus B210 SDR
# Based on Ubuntu 24.04 with srsRAN and OpenAirInterface components
FROM ubuntu:24.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Set working directory
WORKDIR /opt/lte-simulator

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build essentials
    build-essential \
    cmake \
    git \
    pkg-config \
    # UHD and SDR dependencies
    libuhd-dev \
    uhd-host \
    # srsRAN dependencies
    libfftw3-dev \
    libmbedtls-dev \
    libboost-program-options-dev \
    libconfig++-dev \
    libsctp-dev \
    libyaml-cpp-dev \
    libgtest-dev \
    # Python and TUI dependencies
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    # Network tools
    iproute2 \
    iptables \
    # Additional dependencies for Ubuntu 24.04
    software-properties-common \
    gpg-agent \
    # Additional utilities
    wget \
    curl \
    vim \
    tmux \
    htop \
    net-tools \
    usbutils \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for TUI and cellular network management
RUN pip3 install --break-system-packages \
    textual==0.45.1 \
    requests \
    pycryptodome \
    click \
    pyyaml \
    rich \
    asyncio \
    numpy \
    scipy

# Download and build UHD (compatible with Ubuntu 24.04)
RUN cd /tmp && \
    git clone https://github.com/EttusResearch/uhd.git && \
    cd uhd && \
    git checkout v4.6.0.0 && \
    cd host && \
    mkdir build && \
    cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DENABLE_TESTS=OFF \
          -DENABLE_C_API=ON \
          -DENABLE_PYTHON_API=ON .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    rm -rf /tmp/uhd

# Download and build srsRAN (latest stable version)
RUN cd /tmp && \
    git clone https://github.com/srsran/srsRAN_4G.git && \
    cd srsRAN_4G && \
    git checkout release_23_11 && \
    mkdir build && \
    cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DENABLE_ZEROMQ=ON \
          -DENABLE_SRSUE=ON \
          -DENABLE_SRSENB=ON \
          -DENABLE_SRSEPC=ON .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    rm -rf /tmp/srsRAN_4G

# Create application directories
RUN mkdir -p /opt/lte-simulator/{config,data,logs,scripts,tui}

# Copy application files
COPY config/ /opt/lte-simulator/config/
COPY scripts/ /opt/lte-simulator/scripts/
COPY tui/ /opt/lte-simulator/tui/
COPY data/ /opt/lte-simulator/data/

# Make scripts executable
RUN chmod +x /opt/lte-simulator/scripts/*.sh
RUN chmod +x /opt/lte-simulator/tui/*.py

# Set up environment variables
ENV PATH="/opt/lte-simulator/scripts:/opt/lte-simulator/tui:$PATH"
ENV UHD_IMAGES_DIR="/usr/local/share/uhd/images"
ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
ENV UHD_RFNOC_DIR="/usr/local/lib/uhd/rfnoc"

# Create non-root user for security
RUN useradd -m -s /bin/bash lteuser && \
    chown -R lteuser:lteuser /opt/lte-simulator

# Switch to non-root user
USER lteuser

# Download UHD images
RUN /usr/local/lib/uhd/utils/uhd_images_downloader.py

# Expose ports for LTE services
EXPOSE 36412/sctp 36422/sctp 2152/udp

# Default command launches the TUI
CMD ["python3", "/opt/lte-simulator/tui/main.py"]