## 🔍 **Troubleshooting**

### Common Issues

## 🔍 **Troubleshooting**

### Common Issues

#### SDR Not Detected (Ubuntu 24.04 Specific)
```bash
# Check USB connection and permissions
lsusb | grep -i ettus
# Should show: ID 2500:0020 Ettus Research LLC USRP B200

# Check udev rules (if setup was run)
ls -la /etc/udev/rules.d/10-ettus.rules

# Check user groups
groups $USER | grep usrp

# Manual SDR test
uhd_find_devices
uhd_usrp_probe --args "type=b200"
```

#### Docker Permission Issues
```bash
# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER

# Or run with sudo
sudo ./run.sh up
```

#### Container Build Failures
```bash
# Clean and rebuild
sudo ./run.sh clean
sudo ./run.sh build

# Check Docker space
docker system df
docker system prune -f
```

#### Network Start Failure
```bash
# Check if ports are in use
sudo netstat -tulpn | grep :36412
sudo netstat -tulpn | grep :2152

# View container logs
sudo ./run.sh logs

# Check configuration files
docker compose exec lte-simulator cat /opt/lte-simulator/config/epc.conf
```

#### Kernel 6.x Compatibility Issues
```bash
# Check kernel version
uname -r

# If using kernel 6.14+, ensure container has latest UHD
docker compose exec lte-simulator uhd_find_devices --verbose

# Check USB3 compatibility
dmesg | grep -i usb | tail -20
```

### Performance Issues on Ubuntu 24.04

#### Memory and CPU Optimization
```bash
# Check system resources
htop
free -h
df -h

# Optimize Docker settings
sudo systemctl edit docker
# Add:
# [Service]
# ExecStart=
# ExecStart=/usr/bin/dockerd --default-ulimit memlock=-1:-1

# Monitor container resources
docker stats lte-network-sim
```

#### USB Performance
```bash
# Check USB3 speed
lsusb -t
# Ensure B210 is on USB 3.0 bus

# Check USB power management
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2500", ATTR{power/control}="on"' | sudo tee -a /etc/udev/rules.d/10-ettus.rules
sudo udevadm control --reload-rules
```

### Debug Mode for Ubuntu 24.04

Enable comprehensive debugging:
```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export UHD_LOG_LEVEL=debug
export PYTHONUNBUFFERED=1

# Start with debug logging
sudo LOG_LEVEL=DEBUG ./run.sh up

# Monitor all logs simultaneously
sudo ./run.sh logs
```

### Recovery Procedures

#### Complete System Reset
```bash
# Stop everything
sudo ./run.sh down

# Clean all containers and images
sudo ./run.sh clean

# Re-run setup
sudo ./run.sh setup

# Rebuild and start
sudo ./run.sh build
sudo ./run.sh up
```

#### SDR Recovery
```bash
# Reset USB subsystem
sudo modprobe -r usbcore
sudo modprobe usbcore

# Power cycle B210 (unplug/replug)
# Then test
uhd_find_devices
```# LTE Network Simulator with Ettus B210 SDR

A comprehensive Docker-based LTE network simulator that mimics real cellular networks using the Ettus B210 SDR. This system allows you to create realistic cellular network environments for testing, research, and educational purposes.

## ⚠️ **IMPORTANT LEGAL NOTICE**

**THIS SYSTEM IS FOR TESTING AND RESEARCH PURPOSES ONLY**

- **Use only in RF-shielded environments** (Faraday cages, anechoic chambers)
- **Never transmit on live cellular frequencies** without proper authorization
- **Unauthorized cellular transmission is illegal** in most jurisdictions
- **Obtain proper licenses** before any RF transmission
- **Check local regulations** before operating

The authors are not responsible for any misuse of this software.

---

## 🎯 **Features**

### Core Functionality
- **Complete LTE Network Stack**: EPC, MME, HSS, SPGW, and eNodeB using srsRAN
- **Real-world Network Mimicking**: Simulate networks like Cambodia Smart, Cellcard, Metfone
- **Automatic Cell Configuration**: Pull Cell IDs and LACs for specific operators
- **Subscriber Management**: Complete IMSI/Ki/OPc credential management
- **SDR Integration**: Full Ettus B210 control and monitoring

### User Interface
- **Terminal User Interface (TUI)**: Rich, interactive interface using Textual
- **Real-time Monitoring**: Live network status, subscriber activity, and SDR metrics
- **Configuration Management**: Easy network parameter configuration
- **Subscriber Database**: Add, remove, and manage SIM card credentials

### Advanced Features
- **Cell Database**: Real-world cellular network information
- **Authentication System**: Full Milenage authentication implementation
- **Network Monitoring**: Real-time throughput and connection monitoring
- **SDR Calibration**: Automatic SDR calibration and testing
- **Backup & Restore**: Complete database backup and restoration

---

## 🛠️ **System Requirements**

### Hardware
- **SDR**: Ettus B210 USB 3.0 SDR
- **CPU**: Multi-core x86_64 processor (4+ cores recommended)
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 20GB available space
- **USB**: USB 3.0 port for B210

### Software
- **OS**: Ubuntu 22.04 LTS or 24.04 LTS (tested on 24.04 with kernel 6.x)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Python**: 3.8+ (for development)

### RF Environment
- **Faraday Cage** or RF-shielded room
- **Coaxial cables** and appropriate attenuators
- **Test equipment** for signal verification

---

## 🚀 **Quick Start (Ubuntu 24.04)**

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd lte-network-simulator

# Make launcher executable
chmod +x run.sh

# Run initial setup (requires sudo)
sudo ./run.sh setup
```

### 2. Connect Hardware

```bash
# Connect your Ettus B210 SDR via USB 3.0
# Verify detection
lsusb | grep -i ettus

# Should show: Bus XXX Device XXX: ID 2500:0020 Ettus Research LLC USRP B200
```

### 3. Build Container

```bash
# Build the LTE simulator container
sudo ./run.sh build
```

### 4. Start the System

**Option A: Interactive Mode (Recommended)**
```bash
# Start with full interactive TUI
sudo ./run.sh up
```

**Option B: Background Mode**
```bash
# Start in background
sudo ./run.sh background

# View logs
sudo ./run.sh logs
```

**Option C: Interactive Container Access**
```bash
# Run with container shell access
sudo ./run.sh interactive
```

### 5. Quick Commands Summary

```bash
# Essential commands for your workflow:
sudo ./run.sh build         # Build container
sudo ./run.sh up           # Start system (TUI interface)
sudo ./run.sh down         # Stop system
sudo ./run.sh status       # Check status
sudo ./run.sh logs         # View logs
```

### 4. Configure Network

1. **Select Operator**: Choose from Cambodia Smart, Cellcard, Metfone, etc.
2. **Load Cell Data**: Automatically populate Cell ID and LAC
3. **Configure Parameters**: Set MCC, MNC, frequency band
4. **Generate Config**: Create complete network configuration
5. **Start Network**: Launch the LTE network

### 5. Add Subscribers

1. **Navigate to Subscribers Tab**
2. **Add IMSI/Ki/OPc**: Either manually or generate random
3. **Authenticate**: Test subscriber authentication
4. **Monitor**: Watch real-time connection status

---

## 📁 **Project Structure**

```
lte-network-simulator/
├── Dockerfile                 # Main container definition
├── docker-compose.yml         # Multi-service orchestration
├── README.md                  # This documentation
├── scripts/                   # Setup and utility scripts
│   ├── setup.sh              # System setup and configuration
│   ├── start-tui.sh           # TUI launcher
│   ├── start-network.sh       # Network startup
│   ├── stop-network.sh        # Network shutdown
│   └── test-sdr.sh            # SDR connectivity test
├── tui/                       # Terminal User Interface
│   ├── main.py                # Main TUI application
│   ├── network_manager.py     # Network configuration and control
│   ├── subscriber_manager.py  # Subscriber database management
│   ├── sdr_controller.py      # SDR control and monitoring
│   └── cell_database.py       # Cellular network database
├── config/                    # Configuration files
│   ├── epc.conf               # srsEPC configuration
│   ├── enb.conf               # srsENB configuration
│   ├── sib.conf               # System Information Blocks
│   ├── rr.conf                # Radio Resource configuration
│   ├── drb.conf               # Data Radio Bearer configuration
│   └── user_db.csv            # Subscriber database
├── data/                      # Persistent data storage
│   ├── cell_database.json     # Cellular network information
│   ├── operator_database.json # Operator information
│   ├── subscribers.csv        # Internal subscriber database
│   └── sdr_configs/           # Saved SDR configurations
└── logs/                      # Application logs
    ├── tui.log                # TUI application logs
    ├── epc.log                # EPC component logs
    ├── enb.log                # eNodeB logs
    └── sdr.log                # SDR operation logs
```

---

## 🖥️ **TUI Interface Guide**

### Main Tabs

#### 1. **Network Config**
- **Operator Selection**: Choose from real operators (Cambodia Smart, etc.)
- **Network Parameters**: Configure MCC, MNC, Cell ID, LAC
- **Frequency Settings**: Select LTE band and frequencies
- **Control Buttons**: Load cell data, generate config, start/stop network

#### 2. **Subscribers**
- **Add Subscribers**: Enter IMSI, Ki, OPc credentials
- **Random Generation**: Generate test subscriber credentials
- **Subscriber Table**: View all registered subscribers
- **Status Monitoring**: Track subscriber activity and authentication

#### 3. **Monitor**
- **Connection Status**: Real-time UE connection count
- **Data Throughput**: Monitor network data rates
- **System Logs**: Live log display with filtering
- **Performance Metrics**: Network performance statistics

#### 4. **SDR Control**
- **Device Status**: SDR connection and health monitoring
- **Frequency Control**: TX/RX frequency configuration
- **Gain Settings**: TX and RX gain adjustment
- **Calibration**: Automatic SDR calibration procedures
- **Testing**: Comprehensive SDR functionality tests

### Key Bindings
- **Q**: Quit application
- **S**: Start network
- **T**: Stop network
- **R**: Refresh interface
- **H**: Toggle help

---

## 🔧 **Configuration Details**

### Network Configuration

The system supports realistic network configurations for various operators:

#### Cambodia Smart (MCC: 456, MNC: 06)
```json
{
  "mcc": 456,
  "mnc": 6,
  "operator": "Smart Axiata",
  "band": 3,
  "frequency": "1800MHz",
  "cell_id": "auto-generated",
  "lac": "auto-generated"
}
```

#### Cell ID and LAC Generation
- **Cell IDs**: Generated based on MCC/MNC with realistic ranges
- **LACs**: Automatically assigned using geographical clustering
- **Frequency Planning**: Band-appropriate EARFCN assignment

### Subscriber Management

#### Authentication Credentials
- **IMSI**: 15-digit International Mobile Subscriber Identity
- **Ki**: 128-bit authentication key (32 hex characters)
- **OPc**: 128-bit operator key (32 hex characters)
- **AMF**: Authentication Management Field
- **SQN**: Sequence number for replay protection

#### Example Subscriber
```csv
imsi,ki,opc,operator,notes
456060123456789,00112233445566778899AABBCCDDEEFF,00000000000000000000000000000000,Smart Axiata,Test subscriber
```

### SDR Configuration

#### Supported Parameters
- **TX Frequency**: 70 MHz - 6 GHz
- **RX Frequency**: 70 MHz - 6 GHz  
- **TX Gain**: 0 - 89.8 dB
- **RX Gain**: 0 - 76 dB
- **Sample Rate**: 200 kHz - 56 MHz
- **Bandwidth**: Up to 56 MHz

#### Band Configurations
| Band | Frequency | EARFCN DL | EARFCN UL |
|------|-----------|-----------|-----------|
| 1    | 2100MHz   | 300       | 18300     |
| 3    | 1800MHz   | 1200      | 19200     |
| 8    | 900MHz    | 3450      | 21450     |
| 20   | 800MHz    | 6150      | 24150     |

---

## 🚀 **Advanced Usage**

### Custom Operator Configuration

To add a new operator:

1. **Update Operator Database**:
```python
new_operator = {
    "52001": {
        "country": "Thailand",
        "mcc": "520",
        "mnc": "01", 
        "operator": "AIS",
        "brand": "AIS",
        "network_type": ["GSM", "UMTS", "LTE"],
        "bands": ["GSM 900", "LTE 1800"]
    }
}
```

2. **Generate Cell Data**:
```bash
# Use the TUI to load cell data for the new operator
# Or import from CSV file
```

### Subscriber Import/Export

#### Import from CSV
```bash
# Place CSV file in data/ directory
# Use TUI Subscriber tab -> Import function
# Or use subscriber_manager API
```

#### Export for Testing
```bash
# Export current subscribers
# Use TUI Subscriber tab -> Export function
# Format compatible with external tools
```

### Network Monitoring

#### Real-time Metrics
- **UE Connections**: Active subscriber count
- **Throughput**: Data rate monitoring
- **Authentication Events**: Login/logout tracking
- **Error Rates**: Network performance statistics

#### Log Analysis
```bash
# View real-time logs
tail -f logs/epc.log
tail -f logs/enb.log

# Search for specific events
grep "attach" logs/epc.log
grep "authentication" logs/epc.log
```

---

## 🔍 **Troubleshooting**

### Common Issues

#### SDR Not Detected
```bash
# Check USB connection
lsusb | grep -i ettus

# Check permissions
groups $USER | grep usrp

# Test manually
uhd_find_devices
```

#### Network Start Failure
```bash
# Check configuration
cat config/epc.conf
cat config/enb.conf

# Verify ports are free
netstat -tulpn | grep :36412
netstat -tulpn | grep :2152

# Check logs
tail logs/epc.log
tail logs/enb.log
```

#### Authentication Problems
```bash
# Verify subscriber database
cat config/user_db.csv

# Check credentials format
# IMSI: 15 digits
# Ki: 32 hex characters
# OPc: 32 hex characters
```

#### Performance Issues
```bash
# Check system resources
htop
df -h

# Monitor USB performance
dmesg | grep -i usb

# Verify real-time scheduling
ulimit -r
```

### Debug Mode

Enable detailed logging:
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Start with verbose output
python3 tui/main.py --verbose

# Check all log files
tail -f logs/*.log
```

### Recovery Procedures

#### Database Corruption
```bash
# Restore from backup
cp data/backups/subscribers_backup_*.csv data/subscribers.csv
cp data/backups/cells_backup_*.json data/cell_database.json

# Regenerate configuration
# Use TUI -> Network Config -> Generate Config
```

#### SDR Issues
```bash
# Reset SDR
sudo rmmod usbcore
sudo modprobe usbcore

# Re-run calibration
./scripts/test-sdr.sh

# Check for hardware issues
uhd_usrp_probe --args "type=b200"
```

---

## 🛡️ **Security Considerations**

### RF Security
- **Always use RF shielding** to prevent interference
- **Use proper attenuators** to limit transmission power
- **Monitor local spectrum** to avoid interference
- **Follow local regulations** for RF transmission

### Data Security
- **Protect subscriber credentials** - never use real SIM data
- **Secure network interfaces** - isolate from production networks
- **Encrypt sensitive data** - use strong encryption for backups
- **Access control** - limit system access to authorized users

### Network Isolation
- **Use dedicated hardware** for testing
- **Isolate from internet** to prevent security issues
- **Monitor network traffic** for unexpected activity
- **Regular security updates** for all components

---

## 📚 **API Reference**

### NetworkManager Class

```python
# Initialize network manager
network_mgr = NetworkManager()

# Generate configuration
config = await network_mgr.generate_config(
    mcc="456", mnc="06", cell_id="12345", lac="5001", band="3"
)

# Start network
success = await network_mgr.start_network(config)

# Stop network
await network_mgr.stop_network()

# Get status
status = await network_mgr.get_network_status()
```

### SubscriberManager Class

```python
# Initialize subscriber manager
sub_mgr = SubscriberManager()

# Add subscriber
success = await sub_mgr.add_subscriber(
    imsi="456060123456789",
    ki="00112233445566778899AABBCCDDEEFF", 
    opc="00000000000000000000000000000000"
)

# Generate random credentials
imsi, ki, opc = await sub_mgr.generate_random_credentials()

# Authenticate subscriber
auth_result = await sub_mgr.authenticate_subscriber(imsi, rand)
```

### SDRController Class

```python
# Initialize SDR controller
sdr = SDRController()

# Connect to device
success = await sdr.connect()

# Configure parameters
config = {
    "tx_freq": 1842500000,
    "rx_freq": 1747500000,
    "tx_gain": 50,
    "rx_gain": 40
}
await sdr.configure(config)

# Run tests
test_results = await sdr.test()

# Get status
status = await sdr.get_status()
```

### CellDatabase Class

```python
# Initialize cell database
cell_db = CellDatabase()

# Get cells for operator
cells = await cell_db.get_cells_for_operator("45606")

# Add new cell
cell_data = {
    "cell_id": 12345,
    "lac": 5001,
    "mcc": 456,
    "mnc": 6,
    "plmn_id": "45606",
    "operator": "Smart Axiata"
}
await cell_db.add_cell(cell_data)

# Search cells
matches = await cell_db.search_cells(operator="Smart")
```

---

## 🧪 **Testing Procedures**

### System Testing

#### 1. SDR Functionality Test
```bash
# Run comprehensive SDR test
./scripts/test-sdr.sh

# Expected output:
# - Device detection: PASS
# - Basic connectivity: PASS
# - TX path: PASS
# - RX path: PASS
# - Frequency accuracy: PASS
# - Gain control: PASS
```

#### 2. Network Stack Test
```bash
# Start network components
./scripts/start-network.sh

# Verify processes
ps aux | grep srs

# Check network interfaces
ip addr show

# Test S1 interface
netstat -tulpn | grep 36412
```

#### 3. Subscriber Authentication Test
```python
# Use TUI or API to test authentication
# Add test subscriber
# Generate authentication challenge
# Verify authentication response
```

### Performance Testing

#### 1. Throughput Testing
- Monitor data rates during operation
- Test with multiple concurrent subscribers
- Measure latency and jitter

#### 2. Stress Testing
- Connect maximum supported UEs
- Sustained operation testing
- Resource utilization monitoring

#### 3. RF Performance Testing
- Spectrum analysis of transmitted signals
- Power output verification
- Adjacent channel leakage measurement

---

## 🤝 **Contributing**

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd lte-network-simulator

# Create development environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Code Style

- **Python**: Follow PEP 8 with Black formatting
- **Documentation**: Use Google-style docstrings
- **Comments**: Explain complex logic and algorithms
- **Testing**: Include unit tests for new features

### Contribution Guidelines

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Submit pull request** with detailed description

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Important**: This license covers the software only. RF transmission requires separate legal authorization in most jurisdictions.

---

## 📞 **Support**

### Documentation
- **API Documentation**: See docstrings in source code
- **Configuration Examples**: Check `config/` directory
- **Sample Data**: Review `data/` directory examples

### Community
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Wiki**: Contribute to project documentation

### Commercial Support
For commercial support, custom development, or consulting services, please contact the maintainers.

---

## 🙏 **Acknowledgments**

### Open Source Projects
- **srsRAN**: LTE software radio suite
- **UHD**: Ettus Research USRP Hardware Driver  
- **Textual**: Modern TUI framework for Python
- **Docker**: Containerization platform

### Contributors
- Initial development team
- Community contributors
- Testing and validation teams

### Special Thanks
- Ettus Research for SDR hardware
- Software Radio Systems for srsRAN
- The open source community

---

## 📋 **Changelog**

### Version 1.0.0
- Initial release
- Complete LTE network simulation
- Ettus B210 SDR integration
- TUI interface implementation
- Subscriber management system
- Cell database functionality

### Future Releases
- 5G NR support
- Additional SDR hardware support
- Web-based interface
- Enhanced monitoring and analytics
- Machine learning-based optimization

---

**Remember: This system is for testing and research only. Always use in controlled, shielded environments and comply with local regulations.**