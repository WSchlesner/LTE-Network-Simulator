#!/bin/bash
#
# LTE Network Simulator Launcher
# 
# This script provides easy launching for the LTE network simulator
# Compatible with Ubuntu 24.04 and kernel 6.x
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Status symbols
CHECKMARK="${GREEN}✓${NC}"
CROSSMARK="${RED}✗${NC}"
WARNING="${YELLOW}⚠${NC}"
INFO="${BLUE}ℹ${NC}"

# Logging functions
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

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Check if running as root for Docker commands
check_docker_permissions() {
    if ! docker ps &> /dev/null; then
        if [[ $EUID -ne 0 ]]; then
            error "Docker requires sudo privileges or user in docker group"
            echo -e -e "Try running: sudo $0"
            echo -e -e "Or add user to docker group: sudo usermod -aG docker \$USER"
            exit 1
        fi
    fi
}

# Comprehensive system verification
verify_system() {
    echo -e -e "========================================"
    echo -e -e "LTE Network Simulator - System Verification"
    echo -e -e "========================================"
    echo -e -e ""
    
    local overall_status=0
    local critical_failures=0
    local warnings=0
    
    echo -e -e "Checking system requirements and configuration..."
    echo -e ""
    
    # 1. Operating System Check
    echo -e "${INFO} Checking Operating System..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            if [[ "$VERSION_ID" == "24.04" ]]; then
                echo -e "  ${CHECKMARK} Ubuntu 24.04 LTS detected"
            elif [[ "$VERSION_ID" == "22.04" ]]; then
                echo -e "  ${CHECKMARK} Ubuntu 22.04 LTS detected"
            elif [[ "$VERSION_ID" < "22.04" ]]; then
                echo -e "  ${CROSSMARK} Ubuntu $VERSION_ID detected - Ubuntu 22.04+ required"
                critical_failures=$((critical_failures + 1))
            else
                echo -e "  ${CHECKMARK} Ubuntu $VERSION_ID detected"
            fi
        else
            echo -e "  ${WARNING} $PRETTY_NAME detected - Ubuntu recommended"
            warnings=$((warnings + 1))
        fi
    else
        echo -e "  ${CROSSMARK} Cannot determine OS version"
        critical_failures=$((critical_failures + 1))
    fi
    
    # 2. Kernel Version Check
    echo -e "${INFO} Checking Kernel Version..."
    kernel_version=$(uname -r)
    kernel_major=$(uname -r | cut -d. -f1)
    if [[ "$kernel_major" -ge 6 ]]; then
        echo -e "  ${CHECKMARK} Kernel $kernel_version (6.x compatible)"
    elif [[ "$kernel_major" -eq 5 ]]; then
        echo -e "  ${CHECKMARK} Kernel $kernel_version (5.x compatible)"
    else
        echo -e "  ${WARNING} Kernel $kernel_version (older kernel, may have issues)"
        warnings=$((warnings + 1))
    fi
    
    # 3. Docker Installation Check
    echo -e "${INFO} Checking Docker Installation..."
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version | grep -oP '\d+\.\d+' | head -1)
        echo -e "  ${CHECKMARK} Docker $docker_version installed"
        
        # Check Docker service status
        if systemctl is-active --quiet docker; then
            echo -e "  ${CHECKMARK} Docker service is running"
        else
            echo -e "  ${CROSSMARK} Docker service is not running"
            echo -e "    Run: sudo systemctl start docker"
            critical_failures=$((critical_failures + 1))
        fi
        
        # Check Docker permissions
        if docker ps &> /dev/null; then
            echo -e "  ${CHECKMARK} Docker permissions configured"
        else
            if [[ $EUID -eq 0 ]]; then
                echo -e "  ${CHECKMARK} Running as root (Docker accessible)"
            else
                echo -e "  ${WARNING} Docker requires sudo or user in docker group"
                echo -e "    Run: sudo usermod -aG docker \$USER && newgrp docker"
                warnings=$((warnings + 1))
            fi
        fi
    else
        echo -e "  ${CROSSMARK} Docker not found"
        echo -e "    Install with: curl -fsSL https://get.docker.com | sh"
        critical_failures=$((critical_failures + 1))
    fi
    
    # 4. Docker Compose Check
    echo -e "${INFO} Checking Docker Compose..."
    if docker compose version &> /dev/null; then
        compose_version=$(docker compose version --short 2>/dev/null || echo -e "v2.x")
        echo -e "  ${CHECKMARK} Docker Compose $compose_version available"
    elif command -v docker-compose &> /dev/null; then
        compose_version=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+')
        echo -e "  ${WARNING} Docker Compose v1 ($compose_version) - v2 recommended"
        warnings=$((warnings + 1))
    else
        echo -e "  ${CROSSMARK} Docker Compose not found"
        echo -e "    Install with: sudo apt update && sudo apt install docker-compose-plugin"
        critical_failures=$((critical_failures + 1))
    fi
    
    # 5. USB/UHD Tools Check
    echo -e "${INFO} Checking UHD Tools Installation..."
    if command -v uhd_find_devices &> /dev/null; then
        uhd_version=$(uhd_find_devices --help 2>&1 | grep -oP 'UHD \K[\d.]+' | head -1 || echo -e "unknown")
        echo -e "  ${CHECKMARK} UHD tools installed (version $uhd_version)"
    else
        echo -e "  ${WARNING} UHD tools not found in system PATH"
        echo -e "    Will be available inside Docker container"
        warnings=$((warnings + 1))
    fi
    
    # 6. Ettus B210 Hardware Detection
    echo -e "${INFO} Checking Ettus B210 SDR Hardware..."
    if lsusb | grep -i ettus &> /dev/null; then
        device_info=$(lsusb | grep -i ettus)
        if echo -e "$device_info" | grep -q "2500:0020"; then
            echo -e "  ${CHECKMARK} Ettus B210 SDR detected"
            echo -e "    Device: $device_info"
            
            # Check USB 3.0 connection
            if lsusb -t | grep -A 10 "ettus\|2500:0020" | grep -q "5000M"; then
                echo -e "  ${CHECKMARK} USB 3.0 connection detected"
            elif lsusb -t | grep -A 10 "ettus\|2500:0020" | grep -q "480M"; then
                echo -e "  ${WARNING} USB 2.0 connection detected - USB 3.0 recommended"
                warnings=$((warnings + 1))
            fi
        else
            echo -e "  ${WARNING} Ettus device detected but not B210"
            echo -e "    Device: $device_info"
            warnings=$((warnings + 1))
        fi
    else
        echo -e "  ${CROSSMARK} Ettus B210 SDR not detected"
        echo -e "    Ensure B210 is connected via USB 3.0"
        echo -e "    Check cable connection and device power"
        critical_failures=$((critical_failures + 1))
    fi
    
    # 7. USB Permissions Check
    echo -e "${INFO} Checking USB Permissions..."
    if [ -f /etc/udev/rules.d/10-ettus.rules ]; then
        echo -e "  ${CHECKMARK} Ettus udev rules installed"
        
        # Check if usrp group exists
        if getent group usrp &> /dev/null; then
            echo -e "  ${CHECKMARK} usrp group exists"
            
            # Check if current user is in usrp group
            if [[ $EUID -eq 0 ]] || groups $USER 2>/dev/null | grep -q usrp; then
                echo -e "  ${CHECKMARK} User has USB permissions"
            else
                echo -e "  ${WARNING} User not in usrp group"
                echo -e "    Run: sudo usermod -aG usrp \$USER && newgrp usrp"
                warnings=$((warnings + 1))
            fi
        else
            echo -e "  ${WARNING} usrp group does not exist"
            warnings=$((warnings + 1))
        fi
    else
        echo -e "  ${WARNING} Ettus udev rules not found"
        echo -e "    Run: sudo ./run.sh setup"
        warnings=$((warnings + 1))
    fi
    
    # 8. System Resources Check
    echo -e "${INFO} Checking System Resources..."
    
    # Memory check
    total_mem=$(free -g | awk 'NR==2{print $2}')
    if [ "$total_mem" -ge 8 ]; then
        echo -e "  ${CHECKMARK} Memory: ${total_mem}GB (recommended: 8GB+)"
    elif [ "$total_mem" -ge 4 ]; then
        echo -e "  ${WARNING} Memory: ${total_mem}GB (minimum: 4GB, recommended: 8GB+)"
        warnings=$((warnings + 1))
    else
        echo -e "  ${CROSSMARK} Memory: ${total_mem}GB (insufficient - minimum 4GB required)"
        critical_failures=$((critical_failures + 1))
    fi
    
    # Disk space check
    available_space=$(df / | awk 'NR==2{print $4}')
    available_gb=$((available_space / 1024 / 1024))
    if [ "$available_gb" -ge 20 ]; then
        echo -e "  ${CHECKMARK} Disk space: ${available_gb}GB available"
    elif [ "$available_gb" -ge 10 ]; then
        echo -e "  ${WARNING} Disk space: ${available_gb}GB available (minimum 10GB)"
        warnings=$((warnings + 1))
    else
        echo -e "  ${CROSSMARK} Disk space: ${available_gb}GB available (insufficient)"
        critical_failures=$((critical_failures + 1))
    fi
    
    # CPU cores check
    cpu_cores=$(nproc)
    if [ "$cpu_cores" -ge 4 ]; then
        echo -e "  ${CHECKMARK} CPU cores: $cpu_cores (recommended: 4+)"
    elif [ "$cpu_cores" -ge 2 ]; then
        echo -e "  ${WARNING} CPU cores: $cpu_cores (minimum, 4+ recommended)"
        warnings=$((warnings + 1))
    else
        echo -e "  ${CROSSMARK} CPU cores: $cpu_cores (insufficient for optimal performance)"
        warnings=$((warnings + 1))
    fi
    
    # 9. Required Directories Check
    echo -e "${INFO} Checking Project Structure..."
    required_dirs=("config" "data" "logs" "scripts" "tui")
    required_files=("Dockerfile" "docker-compose.yml" "README.md")
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo -e "  ${CHECKMARK} Directory: $dir"
        else
            echo -e "  ${WARNING} Directory missing: $dir"
            warnings=$((warnings + 1))
        fi
    done
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "  ${CHECKMARK} File: $file"
        else
            echo -e "  ${CROSSMARK} File missing: $file"
            critical_failures=$((critical_failures + 1))
        fi
    done
    
    # 10. Network Configuration Check
    echo -e "${INFO} Checking Network Configuration..."
    
    # Check if IP forwarding is enabled
    if [ "$(cat /proc/sys/net/ipv4/ip_forward)" = "1" ]; then
        echo -e "  ${CHECKMARK} IP forwarding enabled"
    else
        echo -e "  ${WARNING} IP forwarding disabled"
        echo -e "    Will be configured during network startup"
        warnings=$((warnings + 1))
    fi
    
    # Check for conflicting services
    conflicting_ports=(36412 36422 2152)
    for port in "${conflicting_ports[@]}"; do
        if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
            echo -e "  ${WARNING} Port $port is in use (may conflict with LTE services)"
            warnings=$((warnings + 1))
        fi
    done
    
    # 11. Python Dependencies Check
    echo "${INFO} Checking Python Environment..."
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        echo "  ${CHECKMARK} Python $python_version installed"
        echo "  ${CHECKMARK} Python packages will be available in container"
        for package in "${essential_packages[@]}"; do
            if python3 -c "import $package" 2>/dev/null; then
                echo -e "  ${CHECKMARK} Python package: $package"
            else
                echo -e "  ${WARNING} Python package missing: $package (available in container)"
                warnings=$((warnings + 1))
            fi
        done
    else
        echo -e "  ${WARNING} Python 3 not found (available in container)"
        warnings=$((warnings + 1))
    fi
    
    # Summary
    echo -e ""
    echo -e "========================================"
    echo -e "VERIFICATION SUMMARY"
    echo -e "========================================"
    
    if [ $critical_failures -eq 0 ]; then
        if [ $warnings -eq 0 ]; then
            echo -e "${CHECKMARK} ${GREEN}System is ready for LTE Network Simulator!${NC}"
            echo -e ""
            echo -e "Next steps:"
            echo -e "  1. Build the container: sudo ./run.sh build"
            echo -e "  2. Start the system: sudo ./run.sh up"
            echo -e ""
            echo -e "${CYAN}Happy simulating! 📡${NC}"
            overall_status=0
        else
            echo -e "${WARNING} ${YELLOW}System is mostly ready with $warnings warning(s)${NC}"
            echo -e ""
            echo -e "The system should work, but consider addressing the warnings above."
            echo -e ""
            echo -e "To proceed:"
            echo -e "  1. Build the container: sudo ./run.sh build"
            echo -e "  2. Start the system: sudo ./run.sh up"
            overall_status=0
        fi
    else
        echo -e "${CROSSMARK} ${RED}System has $critical_failures critical issue(s) and $warnings warning(s)${NC}"
        echo -e ""
        echo -e "${RED}Critical issues must be resolved before proceeding.${NC}"
        echo -e ""
        echo -e "To fix these issues:"
        echo -e "  1. Run setup: sudo ./run.sh setup"
        echo -e "  2. Address critical issues listed above"
        echo -e "  3. Run verification again: ./run.sh verify"
        overall_status=1
    fi
    
    echo -e ""
    echo -e "========================================" 
    
    return $overall_status
}

# Pre-flight checks (simplified version of verify)
preflight_checks() {
    log "Running pre-flight checks..."
    
    # Check Ubuntu version
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        info "OS: $PRETTY_NAME"
        
        if [[ "$VERSION_ID" < "22.04" ]]; then
            error "Ubuntu 22.04 or later required"
            exit 1
        fi
    fi
    
    # Check kernel version
    kernel_version=$(uname -r)
    info "Kernel: $kernel_version"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version)
        info "Docker: $docker_version"
    else
        error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if docker compose version &> /dev/null; then
        compose_version=$(docker compose version)
        info "Docker Compose: $compose_version"
    else
        error "Docker Compose not found."
        exit 1
    fi
    
    # Check for B210 SDR
    if lsusb | grep -i ettus &> /dev/null; then
        info "Ettus SDR detected"
    else
        warning "Ettus B210 SDR not detected. Connect device and try again."
    fi
    
    # Check required directories
    for dir in data logs config; do
        if [ ! -d "$dir" ]; then
            info "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done
    
    info "Pre-flight checks completed"
}

# Build the container
build_container() {
    log "Building LTE Simulator container..."
    
    # Build with no cache to ensure latest versions
    docker compose build --no-cache
    
    if [ $? -eq 0 ]; then
        log "Container built successfully"
    else
        error "Container build failed"
        exit 1
    fi
}

# Start the system
start_system() {
    log "Starting LTE Network Simulator..."
    
    # Check if container is already running
    if docker ps | grep lte-network-sim &> /dev/null; then
        warning "LTE simulator is already running"
        echo -e "Stop it first with: docker compose down"
        exit 1
    fi
    
    # Start the system interactively
    docker compose up
}

# Start system in background
start_system_background() {
    log "Starting LTE Network Simulator in background..."
    docker compose up -d
    
    log "System started in background"
    echo -e "Access logs with: docker compose logs -f"
    echo -e "Stop with: docker compose down"
}

# Interactive mode
interactive_mode() {
    log "Starting LTE Network Simulator in interactive mode..."
    
    # Run with interactive terminal
    docker compose run --rm -it lte-simulator
}

# Show usage
show_usage() {
    echo -e "LTE Network Simulator Launcher"
    echo -e ""
    echo -e "Usage: $0 [COMMAND]"
    echo -e ""
    echo -e "Commands:"
    echo -e "  verify          Verify system is ready for LTE simulator"
    echo -e "  build           Build the Docker container"
    echo -e "  up              Start system (interactive, default)"
    echo -e "  background      Start system in background"
    echo -e "  interactive     Run in interactive mode"
    echo -e "  down            Stop the system"
    echo -e "  logs            Show system logs"
    echo -e "  status          Show system status"
    echo -e "  clean           Clean up containers and images"
    echo -e "  setup           Run initial setup"
    echo -e ""
    echo -e "Examples:"
    echo -e "  $0 verify       # Check if system is ready"
    echo -e "  $0 build        # Build container"
    echo -e "  $0 up           # Start system"
    echo -e "  $0 interactive  # Run interactively"
    echo -e ""
    echo -e "First time setup:"
    echo -e "  1. $0 verify    # Check system requirements"
    echo -e "  2. $0 setup     # If verification fails"
    echo -e "  3. $0 build     # Build the container"
    echo -e "  4. $0 up        # Start the system"
    echo -e ""
}

# Stop system
stop_system() {
    log "Stopping LTE Network Simulator..."
    docker compose down
    log "System stopped"
}

# Show logs
show_logs() {
    docker compose logs -f
}

# Show status
show_status() {
    echo -e "=== Container Status ==="
    docker compose ps
    echo -e ""
    echo -e "=== System Resources ==="
    docker stats --no-stream
}

# Clean up
cleanup() {
    log "Cleaning up containers and images..."
    docker compose down --rmi all --volumes --remove-orphans
    docker system prune -f
    log "Cleanup completed"
}

# Run setup
run_setup() {
    log "Running initial setup..."
    
    # Make setup script executable
    chmod +x scripts/setup.sh
    
    # Run setup script
    ./scripts/setup.sh
    
    log "Setup completed"
}

# Main function
main() {
    echo -e "========================================"
    echo -e "LTE Network Simulator Launcher"
    echo -e "Ubuntu 24.04 / Kernel 6.x Compatible"
    echo -e "========================================"
    echo -e ""
    
    case "${1:-up}" in
        "verify")
            verify_system
            exit $?
            ;;
        "build")
            check_docker_permissions
            preflight_checks
            build_container
            ;;
        "up")
            check_docker_permissions
            preflight_checks
            start_system
            ;;
        "background")
            check_docker_permissions
            preflight_checks
            start_system_background
            ;;
        "interactive")
            check_docker_permissions
            preflight_checks
            interactive_mode
            ;;
        "down")
            stop_system
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "clean")
            cleanup
            ;;
        "setup")
            run_setup
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"