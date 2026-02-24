#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# RPi Service Manager
#
# This script provides comprehensive service management for MeshPi
# including starting, stopping, restarting, and checking status
#
# Usage:
#   ./rpi-service-manager.sh pi@192.168.188.148
#   ./rpi-service-manager.sh pi@192.168.188.148 start
#   ./rpi-service-manager.sh pi@192.168.188.148 status
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
RPI_IP="${1:-pi@192.168.188.148}"
ACTION="${2:-menu}"
SSH_KEY="${3:-~/.ssh/meshpi_test}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# SSH command wrapper
ssh_cmd() {
    local cmd="$1"
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$RPI_IP" "$cmd"
}

# Check SSH connection
check_connection() {
    log_info "Checking SSH connection to $RPI_IP..."
    
    if ssh_cmd "echo 'SSH connection OK'" >/dev/null 2>&1; then
        log_success "SSH connection established"
        return 0
    else
        log_error "Cannot connect to $RPI_IP"
        return 1
    fi
}

# Get comprehensive service status
get_service_status() {
    log_info "Getting comprehensive service status..."
    
    ssh_cmd "
        echo '=== MESHPI SERVICE STATUS ==='
        
        # Check for MeshPi processes
        echo 'MeshPi Processes:'
        ps aux | grep -E '(meshpi|python.*meshpi)' | grep -v grep || echo 'No MeshPi processes found'
        
        echo ''
        
        # Check systemd services
        echo 'Systemd Services:'
        systemctl list-units --type=service --state=running | grep -i meshpi || echo 'No MeshPi systemd services found'
        
        echo ''
        
        # Check common service names
        echo 'Common Service Checks:'
        for service in meshpi meshpi-host meshpi-daemon meshpi-client; do
            if systemctl is-active --quiet \$service 2>/dev/null; then
                echo \"✅ \$service is running\"
            else
                echo \"❌ \$service is not running\"
            fi
        done
        
        echo ''
        
        # Check if meshpi command is available
        echo 'MeshPi Command Availability:'
        if command -v meshpi >/dev/null 2>&1; then
            echo \"✅ meshpi command available: \$(which meshpi)\"
            echo \"Version: \$(meshpi --version 2>/dev/null || echo 'Unknown')\"
        else
            echo \"❌ meshpi command not found in PATH\"
        fi
        
        echo ''
        
        # Check virtual environment
        echo 'Virtual Environment:'
        if [ -d /home/pi/meshpi-env ]; then
            echo \"✅ Virtual environment exists at /home/pi/meshpi-env\"
            if [ -f /home/pi/meshpi-env/bin/meshpi ]; then
                echo \"✅ meshpi available in virtual environment\"
            else
                echo \"❌ meshpi not found in virtual environment\"
            fi
        else
            echo \"❌ No virtual environment found\"
        fi
        
        echo ''
        
        # Check network connections
        echo 'Network Connections:'
        netstat -tlnp 2>/dev/null | grep -E ':(8080|8000|8443|22)' | head -5 || echo 'No relevant network connections found'
        
        echo '=========================='
    "
}

# Start MeshPi service
start_service() {
    log_info "Starting MeshPi service..."
    
    ssh_cmd "
        echo '=== STARTING MESHPI SERVICE ==='
        
        # Try different methods to start MeshPi
        
        # Method 1: Start systemd service if exists
        if systemctl list-unit-files | grep -q 'meshpi.*service'; then
            echo 'Starting systemd service...'
            sudo systemctl start meshpi 2>/dev/null || sudo systemctl start meshpi-host 2>/dev/null || sudo systemctl start meshpi-daemon 2>/dev/null
            echo 'Systemd service start command sent'
        fi
        
        # Method 2: Start in virtual environment
        if [ -d /home/pi/meshpi-env ]; then
            echo 'Starting in virtual environment...'
            # Create a systemd service if it doesn't exist
            if ! systemctl list-unit-files | grep -q 'meshpi-user.service'; then
                echo 'Creating user service...'
                cat > /tmp/meshpi-user.service << 'EOF'
[Unit]
Description=MeshPi User Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=PATH=/home/pi/meshpi-env/bin
ExecStart=/home/pi/meshpi-env/bin/meshpi host
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
                sudo mv /tmp/meshpi-user.service /etc/systemd/system/
                sudo systemctl daemon-reload
                sudo systemctl enable meshpi-user.service
            fi
            
            sudo systemctl start meshpi-user.service
            echo 'Virtual environment service started'
        fi
        
        # Method 3: Start directly with meshpi command
        if command -v meshpi >/dev/null 2>&1; then
            echo 'Starting meshpi host directly...'
            # Start in background with nohup
            nohup meshpi host > /tmp/meshpi-host.log 2>&1 &
            echo \$! > /tmp/meshpi-host.pid
            echo 'MeshPi host started in background'
        fi
        
        # Method 4: Start with python directly
        if [ -f /home/pi/meshpi-env/bin/python ]; then
            echo 'Starting with Python directly...'
            nohup /home/pi/meshpi-env/bin/python -m meshpi host > /tmp/meshpi-python.log 2>&1 &
            echo \$! > /tmp/meshpi-python.pid
            echo 'MeshPi started with Python directly'
        fi
        
        echo '=========================='
    "
    
    # Check if service started
    sleep 3
    log_info "Checking if service started..."
    get_service_status
}

# Stop MeshPi service
stop_service() {
    log_info "Stopping MeshPi service..."
    
    ssh_cmd "
        echo '=== STOPPING MESHPI SERVICE ==='
        
        # Stop systemd services
        echo 'Stopping systemd services...'
        sudo systemctl stop meshpi 2>/dev/null || true
        sudo systemctl stop meshpi-host 2>/dev/null || true
        sudo systemctl stop meshpi-daemon 2>/dev/null || true
        sudo systemctl stop meshpi-user 2>/dev/null || true
        
        # Kill background processes
        echo 'Stopping background processes...'
        if [ -f /tmp/meshpi-host.pid ]; then
            kill \$(cat /tmp/meshpi-host.pid) 2>/dev/null || true
            rm -f /tmp/meshpi-host.pid
        fi
        
        if [ -f /tmp/meshpi-python.pid ]; then
            kill \$(cat /tmp/meshpi-python.pid) 2>/dev/null || true
            rm -f /tmp/meshpi-python.pid
        fi
        
        # Kill any remaining meshpi processes
        echo 'Killing remaining MeshPi processes...'
        pkill -f 'meshpi.*host' 2>/dev/null || true
        pkill -f 'python.*meshpi' 2>/dev/null || true
        
        echo '=========================='
    "
    
    log_success "MeshPi service stopped"
}

# Restart MeshPi service
restart_service() {
    log_info "Restarting MeshPi service..."
    stop_service
    sleep 2
    start_service
}

# Show interactive menu
show_menu() {
    while true; do
        echo ""
        echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║${NC}                    ${WHITE}RPi Service Manager${NC}                    ${CYAN}║${NC}"
        echo -e "${CYAN}║${NC}                    ${CYAN}Device: $RPI_IP${NC}                    ${CYAN}║${NC}"
        echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
        
        # Get current status
        echo ""
        log_info "Current service status:"
        get_service_status
        
        echo ""
        echo -e "${CYAN}Options:${NC}"
        echo "  [1] Start MeshPi service"
        echo "  [2] Stop MeshPi service"
        echo "  [3] Restart MeshPi service"
        echo "  [4] Show detailed status"
        echo "  [5] Check logs"
        echo "  [6] Install/repair MeshPi"
        echo "  [q] Quit"
        
        read -p $'\n[cyan]Choose an option:[/cyan] ' choice
        
        case $choice in
            1)
                start_service
                ;;
            2)
                stop_service
                ;;
            3)
                restart_service
                ;;
            4)
                get_service_status
                ;;
            5)
                show_logs
                ;;
            6)
                install_meshpi
                ;;
            q|Q)
                log_info "Exiting..."
                break
                ;;
            *)
                log_error "Invalid option"
                ;;
        esac
        
        read -p "Press Enter to continue..."
    done
}

# Show logs
show_logs() {
    log_info "Showing MeshPi logs..."
    
    ssh_cmd "
        echo '=== MESHPI LOGS ==='
        
        # Show systemd logs
        echo 'Systemd Logs:'
        journalctl -u meshpi --no-pager -n 20 2>/dev/null || journalctl -u meshpi-host --no-pager -n 20 2>/dev/null || echo 'No systemd logs found'
        
        echo ''
        
        # Show background process logs
        echo 'Background Process Logs:'
        if [ -f /tmp/meshpi-host.log ]; then
            echo 'MeshPi Host Log:'
            tail -20 /tmp/meshpi-host.log
        else
            echo 'No background process logs found'
        fi
        
        echo '=========================='
    "
}

# Install/repair MeshPi
install_meshpi() {
    log_info "Installing/repairing MeshPi..."
    
    ssh_cmd "
        echo '=== INSTALLING/REPAIRING MESHPI ==='
        
        # Check if virtual environment exists
        if [ ! -d /home/pi/meshpi-env ]; then
            echo 'Creating virtual environment...'
            python3 -m venv /home/pi/meshpi-env
        fi
        
        # Activate virtual environment and install
        echo 'Installing MeshPi in virtual environment...'
        source /home/pi/meshpi-env/bin/activate
        pip install --upgrade pip
        pip install meshpi
        
        echo 'Installation completed'
        echo '=========================='
    "
    
    log_success "MeshPi installation/repair completed"
}

# Main function
main() {
    # Check connection first
    if ! check_connection; then
        log_error "Cannot establish SSH connection"
        exit 1
    fi
    
    case $ACTION in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            get_service_status
            ;;
        logs)
            show_logs
            ;;
        install)
            install_meshpi
            ;;
        menu)
            show_menu
            ;;
        *)
            log_error "Unknown action: $ACTION"
            echo "Usage: $0 <ip> [start|stop|restart|status|logs|install|menu]"
            exit 1
            ;;
    esac
}

# Help function
show_help() {
    cat << EOF
RPi Service Manager

Comprehensive service management for MeshPi on Raspberry Pi devices.

USAGE:
    $0 <ip> [ACTION]

ARGUMENTS:
    ip              Target RPi address (e.g., pi@192.168.1.100)
    ACTION          Action to perform (default: menu)

ACTIONS:
    start           Start MeshPi service
    stop            Stop MeshPi service
    restart         Restart MeshPi service
    status          Show service status
    logs            Show service logs
    install         Install/repair MeshPi
    menu            Interactive menu (default)

EXAMPLES:
    $0 pi@192.168.1.100              # Interactive menu
    $0 pi@192.168.1.100 start        # Start service
    $0 pi@192.168.1.100 restart       # Restart service
    $0 pi@192.168.1.100 status        # Show status

This script handles:
- Multiple service start methods
- Process management
- Virtual environment setup
- Log viewing
- Installation/repair

EOF
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
