#!/bin/bash
#
# LTE Network Simulator Setup Script
# 
# This script sets up the LTE network simulator environment
# and prepares the system for SDR operations with Ettus B210.
#

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root (required for some operations)
check_root() {
    if [[ $EUID -ne 0 ]]; then
        warning "Some operations require root privileges"
        warning "You may need to run with sudo for full setup"
    fi
}

# Check system requirements
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check Ubuntu version
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" ]]; then
            warning "This script is designed for Ubuntu. Your system: $ID"
        fi
        info "Operating System: $PRETTY_NAME"
        
        # Check if Ubuntu 24.04
        if [[ "$VERSION_ID" == "24.04" ]]; then
            info "Ubuntu 24.04 detected - using compatible configurations"
        elif [[ "$VERSION_ID" < "22.04" ]]; then
            error "Ubuntu 22.04 or later required. Current: $VERSION_ID"
            exit 1
        fi
    fi
    
    # Check kernel version (6.x kernels need special handling)
    kernel_version=$(uname -r | cut -d. -f1)
    if [[ "$kernel_version" -ge 6 ]]; then
        info "Kernel 6.x detected - applying compatibility settings"
        # Set up compatibility for newer kernels
        export UHD_RFNOC_DIR=/usr/local/lib/uhd/rfnoc
    fi
    
    # Check available memory (minimum 4GB recommended)
    total_mem=$(free -g | awk 'NR==2{print $2}')
    if [ "$total_mem" -lt 4 ]; then
        warning "Low memory detected: ${total_mem}GB. Minimum 4GB recommended."
    else
        info "Memory: ${total_mem}GB"
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df / | awk 'NR==2{print $4}')
    available_gb=$((available_space / 1024 / 1024))
    if [ "$available_gb" -lt 10 ]; then
        warning "Low disk space: ${available_gb}GB available. Minimum 10GB recommended."
    else
        info "Disk space: ${available_gb}GB available"
    fi
    
    # Check Docker version
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version | grep -oP '\d+\.\d+')
        info "Docker version: $docker_version"
        
        # Check if Docker Compose v2 is available
        if docker compose version &> /dev/null; then
            info "Docker Compose v2 detected"
        elif docker-compose --version &> /dev/null; then
            warning "Docker Compose v1 detected. v2 recommended."
        else
            error "Docker Compose not found. Please install Docker Compose."
            exit 1
        fi
    else
        error "Docker not found. Please install Docker first."
        exit 1
    fi
}

# Setup directories
setup_directories() {
    log "Setting up directories..."
    
    # Create required directories
    mkdir -p /opt/lte-simulator/{config,data,logs,scripts,tui}
    mkdir -p /opt/lte-simulator/data/{sdr_configs,backups}
    
    # Set permissions
    if [[ $EUID -eq 0 ]]; then
        chown -R lteuser:lteuser /opt/lte-simulator 2>/dev/null || true
    fi
    
    chmod -R 755 /opt/lte-simulator
    
    info "Directories created successfully"
}

# Check and setup USB permissions for SDR
setup_usb_permissions() {
    log "Setting up USB permissions for SDR..."
    
    # Create udev rules for Ettus devices (updated for Ubuntu 24.04)
    if [[ $EUID -eq 0 ]]; then
        cat > /etc/udev/rules.d/10-ettus.rules << 'EOF'
# Ettus Research USRP devices - Updated for Ubuntu 24.04
SUBSYSTEM=="usb", ATTR{idVendor}=="fffe", ATTR{idProduct}=="0002", MODE="0666", GROUP="usrp"
SUBSYSTEM=="usb", ATTR{idVendor}=="2500", ATTR{idProduct}=="0002", MODE="0666", GROUP="usrp"
SUBSYSTEM=="usb", ATTR{idVendor}=="3923", ATTR{idProduct}=="7813", MODE="0666", GROUP="usrp"
SUBSYSTEM=="usb", ATTR{idVendor}=="3923", ATTR{idProduct}=="7814", MODE="0666", GROUP="usrp"
# B200/B210 specific
SUBSYSTEM=="usb", ATTR{idVendor}=="2500", ATTR{idProduct}=="0020", MODE="0666", GROUP="usrp"
SUBSYSTEM=="usb", ATTR{idVendor}=="2500", ATTR{idProduct}=="0021", MODE="0666", GROUP="usrp"
EOF
        
        # Create usrp group
        groupadd -f usrp
        
        # Add current user and lteuser to usrp group
        if [ -n "$SUDO_USER" ]; then
            usermod -a -G usrp "$SUDO_USER"
            info "Added $SUDO_USER to usrp group"
        fi
        usermod -a -G usrp lteuser 2>/dev/null || true
        
        # Reload udev rules
        udevadm control --reload-rules
        udevadm trigger
        
        info "USB permissions configured"
    else
        warning "Run as root to configure USB permissions for SDR"
    fi
}

# Check SDR connectivity
check_sdr() {
    log "Checking SDR connectivity..."
    
    # Check if uhd_find_devices is available
    if command -v uhd_find_devices &> /dev/null; then
        info "UHD tools found"
        
        # Try to detect devices
        devices=$(uhd_find_devices 2>/dev/null | grep -c "Device Address" || echo "0")
        if [ "$devices" -gt 0 ]; then
            info "Found $devices UHD device(s)"
        else
            warning "No UHD devices detected. Make sure B210 is connected."
        fi
    else
        warning "UHD tools not found. Install UHD for SDR support."
    fi
}

# Setup network interfaces
setup_network() {
    log "Setting up network interfaces..."
    
    if [[ $EUID -eq 0 ]]; then
        # Enable IP forwarding
        echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
        sysctl -p
        
        # Setup iptables rules for packet forwarding
        iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true
        iptables -A FORWARD -i srs_spgw_sgi -o eth0 -j ACCEPT 2>/dev/null || true
        iptables -A FORWARD -i eth0 -o srs_spgw_sgi -j ACCEPT 2>/dev/null || true
        
        info "Network configuration completed"
    else
        warning "Run as root to configure network interfaces"
    fi
}

# Create default configuration files
create_default_configs() {
    log "Creating default configuration files..."
    
    # Create SIB configuration
    cat > /opt/lte-simulator/config/sib.conf << 'EOF'
sib1 = {
  intra_freq_reselection = "Allowed";
  q_rx_lev_min = -65;
  p_max = 23;
  freq_band_indicator = 3;
  si_window_length = 20;
  sched_info = (
    {
      si_periodicity = 16;
      si_mapping_info = []; // SIB2 and SIB3 mapped to first SI message
    }
  );
  system_info_value_tag = 0;
};

sib2 = {
  rr_config_common_sib = {
    rach_cnfg = {
      num_ra_preambles = 64;
      preambles_group_a_cnfg = {
        size_of_ra_preambles_group_a = 52;
        msg_size_group_a = 208;
        msg_pwr_offset_group_b = "minusinfinity";
      };
      pwr_ramping_step = 4;
      preamble_init_rx_target_pwr = -90;
      preamble_trans_max = 10;
      ra_resp_win_size = 7;
      mac_con_res_timer = 64;
      max_harq_msg3_tx = 4;
    };
  };
};
EOF

    # Create RR configuration
    cat > /opt/lte-simulator/config/rr.conf << 'EOF'
mac_cnfg = {
  phr_cnfg = {
    dl_pathloss_change = "dB3"; // Valid: 1, 3, 6 or "infinity"
    periodic_phr_timer = 50;
    prohibit_phr_timer = 0;
  };
  ulsch_cnfg = {
    max_harq_tx = 4;
    periodic_bsr_timer = 20;
    retx_bsr_timer = 320;
    ttі_bundling = false;
  };
  time_alignment_timer = 500; // -1 = infinity, 500, 750, 1280, 1920, 2560, 5120, 10240
};

phy_cnfg = {
  phich_cnfg = {
    duration = "Normal";
    phich_resource = "1/6";
  };
  pusch_cnfg_ded = {
    beta_offset_ack_idx = 10;
    beta_offset_ri_idx = 12;
    beta_offset_cqi_idx = 15;
  };
  
  // PUCCH-SR resources are scheduled on time-frequency domain by a round robin scheduler
  sched_request_cnfg = {
    dsr_trans_max = 64;
    period = 20; // in ms
    subframe = [1]; // vector of subframe indices allowed for SR transmissions (0..9)
  };
  
  cqi_report_cnfg = {
    mode = "periodic";
    simultaneousAckCQI = true;
    period = 40; // in ms
    subframe = [0]; // vector of subframe indices (0..9) 
    m_ri = 8; // RI period in CQI period
  };
};
EOF

    # Create DRB configuration
    cat > /opt/lte-simulator/config/drb.conf << 'EOF'
qci_config = (
{
  qci = 7;
  pdcp_config = {
    discard_timer = 100;
    pdcp_sn_size = 12;
  }
  rlc_config = {
    ul_um = {
      sn_field_length = 10;
    };
    dl_um = {
      sn_field_length = 10;
      t_reordering = 45;
    };
  };
  logical_channel_config = {
    priority = 13;
    prioritized_bit_rate = -1;
    bucket_size_duration = 100;
    logical_channel_group = 2;
  };
},
{
  qci = 9;
  pdcp_config = {
    discard_timer = 150;
    pdcp_sn_size = 12;
  }
  rlc_config = {
    ul_am = {
      t_poll_retx = 120;
      poll_pdu = 64;
      poll_byte = 750;
      max_retx_thresh = 16;
    };
    dl_am = {
      t_reordering = 50;
      t_status_prohibit = 10;
    };
  };
  logical_channel_config = {
    priority = 9;
    prioritized_bit_rate = -1;
    bucket_size_duration = 100;
    logical_channel_group = 3;
  };
}
);
EOF

    info "Default configuration files created"
}

# Create startup scripts
create_startup_scripts() {
    log "Creating startup scripts..."
    
    # Create TUI launcher script
    cat > /opt/lte-simulator/scripts/start-tui.sh << 'EOF'
#!/bin/bash
# Launch the LTE Simulator TUI

cd /opt/lte-simulator
export PYTHONPATH=/opt/lte-simulator/tui:$PYTHONPATH

echo "Starting LTE Network Simulator TUI..."
python3 /opt/lte-simulator/tui/main.py
EOF

    # Create network starter script
    cat > /opt/lte-simulator/scripts/start-network.sh << 'EOF'
#!/bin/bash
# Start LTE network components

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="/opt/lte-simulator/config"
LOG_DIR="/opt/lte-simulator/logs"

echo "Starting LTE Network..."

# Start EPC
echo "Starting srsEPC..."
srsepc $CONFIG_DIR/epc.conf &
EPC_PID=$!
echo $EPC_PID > $LOG_DIR/epc.pid

sleep 2

# Start eNodeB
echo "Starting srsENB..."
srsenb $CONFIG_DIR/enb.conf &
ENB_PID=$!
echo $ENB_PID > $LOG_DIR/enb.pid

echo "LTE Network started successfully"
echo "EPC PID: $EPC_PID"
echo "ENB PID: $ENB_PID"
echo "Use stop-network.sh to stop the network"
EOF

    # Create network stopper script
    cat > /opt/lte-simulator/scripts/stop-network.sh << 'EOF'
#!/bin/bash
# Stop LTE network components

LOG_DIR="/opt/lte-simulator/logs"

echo "Stopping LTE Network..."

# Stop eNodeB
if [ -f "$LOG_DIR/enb.pid" ]; then
    ENB_PID=$(cat $LOG_DIR/enb.pid)
    if kill -0 $ENB_PID 2>/dev/null; then
        echo "Stopping srsENB (PID: $ENB_PID)..."
        kill -TERM $ENB_PID
        sleep 2
        kill -KILL $ENB_PID 2>/dev/null || true
    fi
    rm -f $LOG_DIR/enb.pid
fi

# Stop EPC
if [ -f "$LOG_DIR/epc.pid" ]; then
    EPC_PID=$(cat $LOG_DIR/epc.pid)
    if kill -0 $EPC_PID 2>/dev/null; then
        echo "Stopping srsEPC (PID: $EPC_PID)..."
        kill -TERM $EPC_PID
        sleep 2
        kill -KILL $EPC_PID 2>/dev/null || true
    fi
    rm -f $LOG_DIR/epc.pid
fi

# Clean up any remaining processes
pkill -f srsenb || true
pkill -f srsepc || true

echo "LTE Network stopped"
EOF

    # Create SDR test script
    cat > /opt/lte-simulator/scripts/test-sdr.sh << 'EOF'
#!/bin/bash
# Test SDR connectivity and functionality

echo "Testing SDR connectivity..."

# Check for UHD tools
if ! command -v uhd_find_devices &> /dev/null; then
    echo "Error: UHD tools not found. Please install UHD."
    exit 1
fi

echo "Searching for UHD devices..."
uhd_find_devices

echo ""
echo "Testing B210 connectivity..."
if uhd_find_devices | grep -q "type: b200"; then
    echo "B210 device found!"
    
    echo "Running device probe..."
    timeout 10 uhd_usrp_probe --args "type=b200" | head -20
    
    echo ""
    echo "Testing RX functionality..."
    timeout 5 rx_samples_to_file \
        --args "type=b200" \
        --freq 1800000000 \
        --rate 1000000 \
        --gain 20 \
        --duration 1 \
        --file /tmp/sdr_test.bin
    
    if [ -f /tmp/sdr_test.bin ]; then
        echo "RX test successful!"
        rm -f /tmp/sdr_test.bin
    else
        echo "RX test failed!"
    fi
else
    echo "B210 device not found. Please check connection."
    exit 1
fi
EOF

    # Make scripts executable
    chmod +x /opt/lte-simulator/scripts/*.sh
    
    info "Startup scripts created"
}

# Create systemd service files
create_systemd_services() {
    log "Creating systemd service files..."
    
    if [[ $EUID -eq 0 ]]; then
        # Create LTE simulator service
        cat > /etc/systemd/system/lte-simulator.service << 'EOF'
[Unit]
Description=LTE Network Simulator
After=network.target

[Service]
Type=simple
User=lteuser
Group=lteuser
WorkingDirectory=/opt/lte-simulator
Environment=PYTHONPATH=/opt/lte-simulator/tui
ExecStart=/usr/bin/python3 /opt/lte-simulator/tui/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd
        systemctl daemon-reload
        
        info "Systemd service created. Enable with: systemctl enable lte-simulator"
    else
        warning "Run as root to create systemd services"
    fi
}

# Perform system optimization
optimize_system() {
    log "Optimizing system for SDR operations..."
    
    if [[ $EUID -eq 0 ]]; then
        # Increase USB buffer sizes
        echo 'vm.dirty_background_ratio = 2' >> /etc/sysctl.conf
        echo 'vm.dirty_ratio = 10' >> /etc/sysctl.conf
        
        # Set real-time scheduling limits
        cat >> /etc/security/limits.conf << 'EOF'
@usrp    -    rtprio    99
@usrp    -    memlock   unlimited
lteuser  -    rtprio    99
lteuser  -    memlock   unlimited
EOF

        # Apply changes
        sysctl -p
        
        info "System optimization completed"
    else
        warning "Run as root for system optimization"
    fi
}

# Generate sample data
generate_sample_data() {
    log "Generating sample data..."
    
    # Create sample subscriber data
    cat > /opt/lte-simulator/data/sample_subscribers.csv << 'EOF'
imsi,ki,opc,operator,notes
456060123456789,00112233445566778899AABBCCDDEEFF,00000000000000000000000000000000,Smart Axiata,Test subscriber 1
456010987654321,FEDCBA9876543210FEDCBA9876543210,11111111111111111111111111111111,Cellcard,Test subscriber 2
456081111111111,AAAABBBBCCCCDDDDEEEEFFFFAAAABBBB,22222222222222222222222222222222,Metfone,Test subscriber 3
EOF

    # Create sample cell configuration
    cat > /opt/lte-simulator/data/sample_cells.csv << 'EOF'
cell_id,lac,tac,mcc,mnc,plmn_id,operator,technology,band,earfcn_dl,earfcn_ul,pci,latitude,longitude,location
12345,5001,5001,456,06,45606,Smart Axiata,LTE,3,1275,19275,150,11.5564,104.9282,Phnom Penh Central
12346,5002,5002,456,01,45601,Cellcard,LTE,3,1300,19300,200,13.3671,103.8448,Siem Reap
12347,5003,5003,456,08,45608,Metfone,LTE,3,1325,19325,250,11.9804,104.7690,Battambang
EOF

    info "Sample data files created"
}

# Main installation function
main() {
    echo "========================================"
    echo "LTE Network Simulator Setup"
    echo "========================================"
    echo ""
    
    check_root
    check_system_requirements
    setup_directories
    setup_usb_permissions
    check_sdr
    setup_network
    create_default_configs
    create_startup_scripts
    create_systemd_services
    optimize_system
    generate_sample_data
    
    echo ""
    log "Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Connect your Ettus B210 SDR"
    echo "2. Test SDR connectivity: ./scripts/test-sdr.sh"
    echo "3. Start the TUI interface: ./scripts/start-tui.sh"
    echo ""
    echo "Important notes:"
    echo "- Use only in RF-shielded environments"
    echo "- Ensure you have proper licenses for transmission"
    echo "- Review local regulations before operating"
    echo ""
    warning "This system creates fake cellular networks for testing only!"
}

# Run main function
main "$@"