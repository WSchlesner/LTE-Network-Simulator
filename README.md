# LTE Network Simulator with Ettus B210 SDR

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

### 1. Clone and Verify Setup

```bash
# Clone the repository
git clone <repository-url>
cd lte-network-simulator

# Make launcher executable
chmod +x run.sh

# Verify your system is ready (NEW!)
./run.sh verify
```

The verify command will check:
- ✅ Operating System compatibility
- ✅ Kernel version
- ✅ Docker installation and permissions
- ✅ Docker Compose availability
- ✅ Ettus B210 SDR detection
- ✅ USB permissions and udev rules
- ✅ System resources (RAM, disk, CPU)
- ✅ Required project files
- ✅ Network configuration
- ✅ Python environment

### 2. Setup (if verification fails)

```bash
# If verification fails, run setup to fix issues
sudo ./run.sh setup
```

### 3. Connect Hardware

```bash
# Connect your Ettus B210 SDR via USB 3.0
# Verify detection
lsusb | grep -i ettus

# Should show: Bus XXX Device XXX: ID 2500:0020 Ettus Research LLC USRP B200
```

### 4. Build and Start

```bash
# Build the LTE simulator container
sudo ./run.sh build

# Start the system with interactive TUI
sudo ./run.sh up
```

### 5. Complete Command Reference

```bash
# System verification and setup
./run.sh verify           # Check if system is ready ⭐ NEW!
sudo ./run.sh setup       # Fix configuration issues

# Container management
sudo ./run.sh build       # Build container
sudo ./run.sh up          # Start system (TUI interface)
sudo ./run.sh background  # Start in background
sudo ./run.sh interactive # Run with container shell access
sudo ./run.sh down        # Stop system

# Monitoring and maintenance
sudo ./run.sh status      # Check status
sudo ./run.sh logs        # View logs
sudo ./run.sh clean       # Clean up containers

# Help
./run.sh help            # Show detailed usage
```

### 6. First-Time Setup Workflow

```bash
# Complete first-time setup workflow:

# 1. Verify system readiness
./run.sh verify

# 2. If verification fails, run setup
sudo ./run.sh setup

# 3. Verify again to ensure all issues are resolved
./run.sh verify

# 4. Build the container
sudo ./run.sh build

# 5. Start the system
sudo ./run.sh up
```

### 7. Configure Network

1. **Select Operator**: Choose from Cambodia Smart, Cellcard, Metfone, etc.
2. **Load Cell Data**: Automatically populate Cell ID and LAC
3. **Configure Parameters**: Set MCC, MNC, frequency band
4. **Generate Config**: Create complete network configuration
5. **Start Network**: Launch the LTE network

### 8. Add Subscribers

1. **Navigate to Subscribers Tab**
2. **Add IMSI/Ki/OPc**: Either manually or generate random
3. **Authenticate**: Test subscriber authentication
4. **Monitor**: Watch real-time connection status

---

## 🔧 **System Verification Details**

The new `./run.sh verify` command performs comprehensive checks:

### ✅ **Critical Checks** (Must Pass)
- **Operating System**: Ubuntu 22.04+ required
- **Docker Installation**: Proper Docker setup with running service
- **Docker Compose**: Version 2.0+ availability
- **Ettus B210 Detection**: Hardware presence via USB
- **System Resources**: Minimum 4GB RAM, 10GB disk space
- **Project Structure**: Required files and directories

### ⚠️ **Warning Checks** (Should Address)
- **USB 3.0 Connection**: B210 connected via USB 3.0 vs 2.0
- **Memory**: 8GB+ recommended (minimum 4GB)
- **USB Permissions**: User in usrp group
- **UHD Tools**: Available in system PATH
- **Network Ports**: No conflicting services

### 🔧 **Automatic Fixes Available**

If verification fails, `./run.sh setup` can automatically fix:
- Install Docker and Docker Compose
- Create required directories
- Set up USB permissions and udev rules
- Configure system optimization settings
- Create default configuration files
- Set up systemd services

---

## 📁 **Project Structure**

```
lte-network-simulator/
├── Dockerfile                 # Main container definition
├── docker-compose.yml         # Multi-service orchestration
├── README.md                  # This documentation
├── run.sh                     # Enhanced launcher with verify ⭐ NEW!
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

### System Verification and Troubleshooting

#### Using the Verify Command
```bash
# Run comprehensive system check
./run.sh verify

# Example output for healthy system:
# ✓ Ubuntu 24.04 LTS detected
# ✓ Kernel 6.5.0 (6.x compatible)
# ✓ Docker 24.0.6 installed
# ✓ Docker service is running
# ✓ Docker permissions configured
# ✓ Docker Compose v2.21.0 available
# ✓ Ettus B210 SDR detected
# ✓ USB 3.0 connection detected
# ✓ Memory: 16GB (recommended: 8GB+)
# ✓ System is ready for LTE Network Simulator!
```

#### Common Verification Failures and Solutions

**Docker Not Found**
```bash
# Solution: Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

**Ettus B210 Not Detected**
```bash
# Check USB connection
lsusb | grep -i ettus

# Ensure USB 3.0 connection
lsusb -t | grep -A 10 "ettus"

# Check cable and power
```

**Permission Issues**
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Fix USB permissions
sudo ./run.sh setup
```

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

### Verification-Based Troubleshooting

Start with system verification:
```bash
./run.sh verify
```

This will identify issues and provide specific solutions for each problem.

### Common Issues

#### System Verification Fails
```bash
# If critical issues found:
sudo ./run.sh setup

# Then verify again:
./run.sh verify

# Address remaining warnings as needed
```

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
# Check system resources using verify
./run.sh verify

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

#### Complete System Reset
```bash
# Clean everything and start fresh
sudo ./run.sh clean
sudo ./run.sh setup
./run.sh verify
sudo ./run.sh build
sudo ./run.sh up
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

#### 1. Complete System Verification
```bash
# Comprehensive system check
./run.sh verify

# Expected output should show all green checkmarks
# Address any warnings or critical issues
```

#### 2. SDR Functionality Test
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

#### 3. Network Stack Test
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

#### 4. Subscriber Authentication Test
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

# Verify development environment
./run.sh verify

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
3. **Verify system**: `./run.sh verify`
4. **Write tests** for new functionality
5. **Update documentation** as needed
6. **Submit pull request** with detailed description

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

### Version 1.1.0 ⭐ NEW!
- **Added comprehensive system verification**: `./run.sh verify`
- **Enhanced setup automation**: Better error handling and fixes
- **Improved user experience**: Clear status indicators and help
- **Better troubleshooting**: Specific solutions for common issues
- **Enhanced documentation**: Step-by-step verification workflow

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

## 🚀 **Quick Reference Card**

```bash
# Essential workflow for new users:
./run.sh verify          # ✅ Check system readiness
sudo ./run.sh setup      # 🔧 Fix any issues found
./run.sh verify          # ✅ Verify fixes worked
sudo ./run.sh build      # 🏗️  Build container
sudo ./run.sh up         # 🚀 Start system

# Daily operations:
sudo ./run.sh up         # Start system
sudo ./run.sh background # Start in background  
sudo ./run.sh down       # Stop system
sudo ./run.sh logs       # View logs
sudo ./run.sh status     # Check status
```
