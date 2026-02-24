#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Fix RPi MeshPi Installation Issues
#
# This script addresses the specific issues found in the diagnostic:
# 1. Externally managed Python environment (PEP 668)
# 2. Missing python3-full package
# 3. Virtual environment setup
#
# Usage:
#   ./fix-rpi-meshpi.sh pi@192.168.188.148
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
RPI_IP="${1:-pi@192.168.188.148}"
SSH_KEY="${2:-~/.ssh/meshpi_test}"

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
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$RPI_IP" "$cmd"
}

# Main fix procedure
main() {
    log_info "Starting MeshPi installation fix for: $RPI_IP"
    
    # Step 1: Install required packages for virtual environments
    log_info "Step 1: Installing python3-full and venv support..."
    ssh_cmd "
        echo 'Installing python3-full and venv support...'
        sudo apt update
        sudo apt install -y python3-full python3-venv python3-pip
    "
    
    # Step 2: Create virtual environment
    log_info "Step 2: Creating virtual environment..."
    ssh_cmd "
        echo 'Creating virtual environment in /home/pi/meshpi-env...'
        python3 -m venv /home/pi/meshpi-env
        echo 'Virtual environment created successfully'
    "
    
    # Step 3: Activate virtual environment and install MeshPi
    log_info "Step 3: Installing MeshPi in virtual environment..."
    ssh_cmd "
        echo 'Activating virtual environment and installing MeshPi...'
        source /home/pi/meshpi-env/bin/activate
        
        # Upgrade pip in virtual environment
        pip install --upgrade pip
        
        # Install MeshPi
        echo 'Installing MeshPi...'
        pip install meshpi
        
        # Verify installation
        echo 'Verifying MeshPi installation...'
        python -c 'import meshpi; print(f\"MeshPi version: {meshpi.__version__}\")'
        
        # Test CLI
        echo 'Testing MeshPi CLI...'
        meshpi --help
        
        echo 'MeshPi installation completed successfully!'
    "
    
    # Step 4: Create activation script for easy usage
    log_info "Step 4: Creating activation script..."
    ssh_cmd "
        echo '#!/bin/bash
# MeshPi Virtual Environment Activation Script

# Activate virtual environment
source /home/pi/meshpi-env/bin/activate

# Set PATH to include virtual environment
export PATH=\"/home/pi/meshpi-env/bin:\$PATH\"

echo \"MeshPi virtual environment activated\"
echo \"Python: \$(which python)\"
echo \"MeshPi: \$(which meshpi)\"
echo \"Use: meshpi --help for available commands\"

# Keep shell active
exec \"\$@\"
' > /home/pi/activate-meshpi.sh
        
        chmod +x /home/pi/activate-meshpi.sh
        echo 'Activation script created: /home/pi/activate-meshpi.sh'
    "
    
    # Step 5: Create systemd service for auto-activation (optional)
    log_info "Step 5: Creating systemd service for MeshPi..."
    ssh_cmd "
        echo '[Unit]
Description=MeshPi Virtual Environment
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/home/pi/activate-meshpi.sh /bin/true
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
' | sudo tee /etc/systemd/system/meshpi-env.service
        
        sudo systemctl daemon-reload
        sudo systemctl enable meshpi-env.service
        echo 'Systemd service created and enabled'
    "
    
    # Step 6: Test installation
    log_info "Step 6: Testing final installation..."
    ssh_cmd "
        echo 'Testing MeshPi installation...'
        /home/pi/activate-meshpi.sh meshpi info
    "
    
    log_success "MeshPi installation fix completed!"
    log_info "To use MeshPi on the RPi:"
    log_info "  1. SSH into the RPi: ssh pi@192.168.188.148"
    log_info "  2. Activate environment: /home/pi/activate-meshpi.sh"
    log_info "  3. Use MeshPi: meshpi --help"
    
    # Step 7: Create usage instructions
    log_info "Step 7: Creating usage instructions..."
    ssh_cmd "
        echo '# MeshPi Usage Instructions

## Quick Start
1. Activate the MeshPi virtual environment:
   /home/pi/activate-meshpi.sh

2. Use MeshPi commands:
   meshpi --help
   meshpi info
   meshpi scan

## Manual Activation
If you prefer manual activation:
1. source /home/pi/meshpi-env/bin/activate
2. meshpi --help

## Troubleshooting
- If meshpi command not found: ensure virtual environment is activated
- If import errors: try \"pip install --upgrade meshpi\" in the virtual environment
- For WiFi issues: sudo raspi-config to set country code

## Virtual Environment Location
The MeshPi virtual environment is installed at: /home/pi/meshpi-env/
- Python executable: /home/pi/meshpi-env/bin/python
- Pip executable: /home/pi/meshpi-env/bin/pip
- MeshPi location: /home/pi/meshpi-env/lib/python*/site-packages/meshpi/

## Service Management
The meshpi-env systemd service ensures the environment is available on boot.
- Check status: sudo systemctl status meshpi-env
- Restart service: sudo systemctl restart meshpi-env
' > /home/pi/MESHPI-USAGE.md
        
        echo 'Usage instructions created: /home/pi/MESHPI-USAGE.md'
    "
    
    log_success "All fixes applied! Check /home/pi/MESHPI-USAGE.md on the RPi for usage instructions."
}

# Help function
show_help() {
    cat << EOF
RPi MeshPi Installation Fix

This script fixes the \"externally-managed-environment\" issue by:
1. Installing python3-full and venv support
2. Creating a dedicated virtual environment
3. Installing MeshPi in the virtual environment
4. Creating activation scripts and systemd service

USAGE:
    $0 [RPI_IP] [SSH_KEY]

ARGUMENTS:
    RPI_IP         Target RPi address (default: pi@192.168.188.148)
    SSH_KEY        SSH private key path (default: ~/.ssh/meshpi_test)

EXAMPLES:
    $0                                    # Use default IP
    $0 pi@192.168.188.148                 # Specify IP
    $0 pi@192.168.188.148 ~/.ssh/id_rsa   # Custom SSH key

After running this script:
1. SSH into the RPi
2. Run: /home/pi/activate-meshpi.sh
3. Use: meshpi --help

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
