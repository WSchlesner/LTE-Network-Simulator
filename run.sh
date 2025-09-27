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
NC='\033[0m' # No Color

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

# Check if running as root for Docker commands
check_docker_permissions() {
    if ! docker ps &> /dev/null; then
        if [[ $EUID -ne 0 ]]; then
            error "Docker requires sudo privileges or user in docker group"
            echo "Try running: sudo $0"
            echo "Or add user to docker group: sudo usermod -aG docker \$USER"
            exit 1
        fi
    fi
}

# Pre-flight checks
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
        echo "Stop it first with: docker compose down"
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
    echo "Access logs with: docker compose logs -f"
    echo "Stop with: docker compose down"
}

# Interactive mode
interactive_mode() {
    log "Starting LTE Network Simulator in interactive mode..."
    
    # Run with interactive terminal
    docker compose run --rm -it lte-simulator
}

# Show usage
show_usage() {
    echo "LTE Network Simulator Launcher"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build           Build the Docker container"
    echo "  up              Start system (interactive, default)"
    echo "  background      Start system in background"
    echo "  interactive     Run in interactive mode"
    echo "  down            Stop the system"
    echo "  logs            Show system logs"
    echo "  status          Show system status"
    echo "  clean           Clean up containers and images"
    echo "  setup           Run initial setup"
    echo ""
    echo "Examples:"
    echo "  $0 build        # Build container"
    echo "  $0 up           # Start system"
    echo "  $0 interactive  # Run interactively"
    echo ""
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
    echo "=== Container Status ==="
    docker compose ps
    echo ""
    echo "=== System Resources ==="
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
    echo "========================================"
    echo "LTE Network Simulator Launcher"
    echo "Ubuntu 24.04 / Kernel 6.x Compatible"
    echo "========================================"
    echo ""
    
    # Check Docker permissions first
    check_docker_permissions
    
    case "${1:-up}" in
        "build")
            preflight_checks
            build_container
            ;;
        "up")
            preflight_checks
            start_system
            ;;
        "background")
            preflight_checks
            start_system_background
            ;;
        "interactive")
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