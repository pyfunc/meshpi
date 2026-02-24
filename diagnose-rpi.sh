#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Remote RPi Diagnostic Script - Diagnose MeshPi installation issues
#
# Usage:
#   ./diagnose-rpi.sh pi@192.168.188.148
#   ./diagnose-rpi.sh pi@192.168.188.148 ~/.ssh/custom_key
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
RPI_IP="${1:-pi@192.168.188.148}"
SSH_KEY="${2:-~/.ssh/meshpi_test}"
VERBOSE="${VERBOSE:-false}"

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

log_device() {
    echo -e "${CYAN}[RPI]${NC} $1"
}

# SSH command wrapper
ssh_cmd() {
    local cmd="$1"
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Executing: $cmd"
    fi
    
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

# Get comprehensive system information
get_system_info() {
    log_info "Gathering system information..."
    
    ssh_cmd "
        echo '=== SYSTEM INFORMATION ==='
        echo 'Hostname: $(hostname)'
        echo 'IP Address: $(hostname -I | awk \"{print \$1}\")'
        echo 'Kernel: $(uname -r)'
        echo 'Architecture: $(uname -m)'
        echo 'OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')'
        echo 'Uptime: $(uptime -p)'
        echo 'Memory: $(free -h | grep Mem | awk \"{print \$2}\")'
        echo 'Disk: $(df -h / | tail -1 | awk \"{print \$4}\")'
        # CPU
        echo 'CPU: $(cat /proc/cpuinfo | grep "Model" | cut -d: -f2 | xargs)'
        echo 'Temperature: $(vcgencmd measure_temp 2>/dev/null || echo \"N/A\")'
        echo '=========================='
    "
}

# Check Python environment
check_python_env() {
    log_info "Checking Python environment..."
    
    ssh_cmd "
        echo '=== PYTHON ENVIRONMENT ==='
        
        # Python versions
        echo 'Python versions available:'
        ls -1 /usr/bin/python* 2>/dev/null || echo 'No python executables found'
        
        # Default python3
        if command -v python3 >/dev/null 2>&1; then
            echo 'Default python3: $(python3 --version)'
            echo 'Python3 path: $(which python3)'
            echo 'Python3 executable: $(file $(which python3))'
        else
            echo 'ERROR: python3 not found'
            exit 1
        fi
        
        # Pip versions
        echo 'Pip versions available:'
        ls -1 /usr/bin/pip* 2>/dev/null || echo 'No pip executables found'
        
        # Default pip3
        if command -v pip3 >/dev/null 2>&1; then
            echo 'Default pip3: $(pip3 --version)'
            echo 'Pip3 path: $(which pip3)'
        else
            echo 'WARNING: pip3 not found'
        fi
        
        # Python site-packages
        echo 'Site-packages location:'
        python3 -c 'import site; print(site.getsitepackages()[0])' 2>/dev/null || echo 'Cannot determine site-packages'
        
        echo '============================'
    "
}

# Check network connectivity
check_network() {
    log_info "Checking network connectivity..."
    
    ssh_cmd "
        echo '=== NETWORK CONNECTIVITY ==='
        
        # Network interfaces
        echo 'Network interfaces:'
        ip addr show | grep -E '^[0-9]+:' | awk '{print \$2}' | sed 's/://'
        
        # WiFi status
        echo 'WiFi status:'
        if command -v iwconfig >/dev/null 2>&1; then
            iwconfig 2>/dev/null | grep -E 'wlan|ESSID' || echo 'No WiFi interfaces found'
        fi
        
        # rfkill status
        echo 'rfkill status:'
        rfkill list 2>/dev/null || echo 'rfkill not available'
        
        # Internet connectivity
        echo 'Internet connectivity:'
        ping -c 3 8.8.8.8 >/dev/null 2>&1 && echo '✅ Internet OK' || echo '❌ Internet failed'
        
        # PyPI connectivity
        echo 'PyPI connectivity:'
        curl -s --connect-timeout 5 https://pypi.org >/dev/null && echo '✅ PyPI reachable' || echo '❌ PyPI not reachable'
        
        echo '============================'
    "
}

# Check MeshPi installation attempt
check_meshpi_installation() {
    log_info "Testing MeshPi installation..."
    
    ssh_cmd "
        echo '=== MESHPi INSTALLATION TEST ==='
        
        # Check if meshpi is already installed
        if python3 -c 'import meshpi' 2>/dev/null; then
            echo 'MeshPi already installed:'
            python3 -c 'import meshpi; print(f\"Version: {meshpi.__version__}\")'
            echo 'MeshPy location:', \$(python3 -c 'import meshpi; print(meshpi.__file__)')
        else
            echo 'MeshPi not installed - testing installation...'
            
            # Clean pip cache
            pip3 cache purge 2>/dev/null || true
            
            # Try basic installation
            echo 'Attempting basic installation...'
            if pip3 install meshpi --verbose --timeout 120; then
                echo '✅ Basic installation successful'
                python3 -c 'import meshpi; print(f\"Version: {meshpi.__version__}\")'
            else
                echo '❌ Basic installation failed'
                
                # Try with specific options
                echo 'Trying with --no-cache-dir...'
                if pip3 install meshpi --no-cache-dir --timeout 120; then
                    echo '✅ Installation with --no-cache-dir successful'
                else
                    echo '❌ Installation with --no-cache-dir failed'
                    
                    # Check specific error
                    echo 'Checking for specific issues...'
                    pip3 install meshpi --dry-run 2>&1 | head -20
                fi
            fi
        fi
        
        echo '================================'
    "
}

# Check system dependencies
check_dependencies() {
    log_info "Checking system dependencies..."
    
    ssh_cmd "
        echo '=== SYSTEM DEPENDENCIES ==='
        
        # Check build tools
        echo 'Build tools:'
        which gcc gcc g++ make 2>/dev/null || echo 'Missing build tools'
        
        # Check Python headers
        echo 'Python headers:'
        dpkg -l | grep python3-dev 2>/dev/null || echo 'python3-dev not installed'
        
        # Check SSL
        echo 'SSL/TLS:'
        python3 -c 'import ssl; print(f\"SSL version: {ssl.OPENSSL_VERSION}\")' 2>/dev/null || echo 'SSL module issue'
        
        # Check cryptography dependencies
        echo 'Cryptography dependencies:'
        dpkg -l | grep -E 'libssl|libcrypto' 2>/dev/null || echo 'Missing crypto libraries'
        
        # Check disk space
        echo 'Disk space:'
        df -h /
        
        # Check memory
        echo 'Memory usage:'
        free -h
        
        echo '=========================='
    "
}

# Check WiFi issues specifically
check_wifi_issues() {
    log_info "Checking WiFi configuration issues..."
    
    ssh_cmd "
        echo '=== WiFi DIAGNOSTICS ==='
        
        # Check rfkill
        echo 'rfkill status:'
        rfkill list wifi 2>/dev/null || echo 'rfkill wifi not available'
        
        # Check if WiFi is blocked
        if rfkill list wifi 2>/dev/null | grep -q 'Soft blocked: yes'; then
            echo '❌ WiFi is soft blocked - trying to unblock...'
            sudo rfkill unblock wifi
            echo 'WiFi unblocked'
        fi
        
        # Check country code
        echo 'WiFi country code:'
        raspi-config nonint get_wifi_country 2>/dev/null || echo 'Cannot get WiFi country'
        
        # Check wpa_supplicant
        echo 'wpa_supplicant status:'
        sudo systemctl status wpa_supplicant 2>/dev/null | head -5 || echo 'wpa_supplicant not running'
        
        # Check available networks
        echo 'Available networks:'
        sudo iwlist scan 2>/dev/null | grep ESSID | head -5 || echo 'Cannot scan networks'
        
        echo '======================='
    "
}

# Generate recommendations
generate_recommendations() {
    log_info "Generating recommendations..."
    
    ssh_cmd "
        echo '=== RECOMMENDATIONS ==='
        
        # Check common issues
        issues=()
        
        # Check Python version
        python_version=\$(python3 --version 2>&1 | cut -d' ' -f2)
        if [[ \$python_version < 3.9 ]]; then
            issues+=('Python version too old - upgrade to 3.9+')
        fi
        
        # Check pip
        if ! command -v pip3 >/dev/null 2>&1; then
            issues+=('pip3 not installed - run: sudo apt install python3-pip')
        fi
        
        # Check build tools
        if ! command -v gcc >/dev/null 2>&1; then
            issues+=('Missing build tools - run: sudo apt install build-essential')
        fi
        
        # Check WiFi
        if rfkill list wifi 2>/dev/null | grep -q 'Soft blocked: yes'; then
            issues+=('WiFi blocked - run: sudo rfkill unblock wifi')
        fi
        
        # Check disk space
        disk_free=\$(df / | tail -1 | awk '{print \$4}')
        if [[ \$disk_free -lt 1000000 ]]; then  # Less than 1GB
            issues+=('Low disk space - clean up with: sudo apt autoremove && sudo apt autoclean')
        fi
        
        # Output recommendations
        if [[ \${#issues[@]} -eq 0 ]]; then
            echo '✅ No critical issues found'
        else
            echo '❌ Issues found:'
            for issue in \"\${issues[@]}\"; do
                echo \"  - \$issue\"
            done
        fi
        
        echo 'General recommendations:'
        echo '1. Update system: sudo apt update && sudo apt upgrade -y'
        echo '2. Install dependencies: sudo apt install python3-pip python3-dev build-essential -y'
        echo '3. Upgrade pip: pip3 install --upgrade pip'
        echo '4. Set WiFi country: sudo raspi-config nonint do_wifi_country PL'
        echo '5. Unblock WiFi: sudo rfkill unblock wifi'
        
        echo '===================='
    "
}

# Main diagnostic flow
main() {
    log_info "Starting comprehensive RPi diagnostic for: $RPI_IP"
    log_info "Using SSH key: $SSH_KEY"
    
    # Check connection first
    if ! check_connection; then
        log_error "Cannot establish SSH connection"
        exit 1
    fi
    
    # Run all diagnostic checks
    get_system_info
    check_python_env
    check_network
    check_dependencies
    check_wifi_issues
    check_meshpi_installation
    generate_recommendations
    
    log_success "Diagnostic completed!"
    log_info "Review the output above for specific issues and recommendations"
}

# Help function
show_help() {
    cat << EOF
RPi Diagnostic Script

USAGE:
    $0 [RPI_IP] [SSH_KEY]

ARGUMENTS:
    RPI_IP         Target RPi address (default: pi@192.168.188.148)
    SSH_KEY        SSH private key path (default: ~/.ssh/meshpi_test)

EXAMPLES:
    $0                                    # Use default IP
    $0 pi@192.168.188.148                 # Specify IP
    $0 pi@192.168.188.148 ~/.ssh/id_rsa   # Custom SSH key

This script will:
- Check SSH connectivity
- Gather system information
- Analyze Python environment
- Test network connectivity
- Check system dependencies
- Diagnose WiFi issues
- Test MeshPi installation
- Provide specific recommendations

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
