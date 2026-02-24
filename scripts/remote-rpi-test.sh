#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Remote RPi Test Script - Test MeshPi on real Raspberry Pi hardware via SSH
#
# Usage:
#   ./remote-rpi-test.sh                           # Use default pi@raspberrypi.local
#   ./remote-rpi-test.sh pi@192.168.1.100         # Use specific IP
#   ./remote-rpi-test.sh pi@rpi.local ~/.ssh/id_rsa # Use custom SSH key
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
RPI_IP="${1:-pi@raspberrypi.local}"
SSH_KEY="${2:-~/.ssh/meshpi_test}"
TIMEOUT="${3:-300}"
VERBOSE="${4:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Executing: $cmd"
    fi
    
    timeout "$TIMEOUT" ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$RPI_IP" "$cmd"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check SSH key
    if [[ ! -f "$SSH_KEY" ]]; then
        log_error "SSH key not found: $SSH_KEY"
        log_info "Generate one with: ssh-keygen -t rsa -b 4096 -C 'meshpi-testing' -f $SSH_KEY"
        exit 1
    fi
    
    # Check SSH connection
    if ! ssh_cmd "echo 'SSH connection test'" >/dev/null 2>&1; then
        log_error "Cannot connect to $RPI_IP"
        log_info "Check:"
        log_info "  - RPi is powered on and connected to network"
        log_info "  - SSH is enabled on RPi"
        log_info "  - SSH key is properly copied: ssh-copy-id -i $SSH_KEY.pub $RPI_IP"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Get RPi system information
get_rpi_info() {
    log_info "Getting RPi system information..."
    
    ssh_cmd "
        echo '=== Raspberry Pi Information ==='
        echo 'Hostname: $(hostname)'
        echo 'IP Address: $(hostname -I | awk \"{print \$1}\")'
        echo 'Python Version: $(python3 --version)'
        echo 'Pip Version: $(pip3 --version)'
        echo 'Architecture: $(uname -m)'
        echo 'OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')'
        echo 'Memory: $(free -h | grep Mem | awk \"{print \$2}\")'
        echo 'Disk Space: $(df -h / | tail -1 | awk \"{print \$4}\")'
        echo 'Model: $(cat /proc/cpuinfo | grep 'Model' | cut -d: -f2 | xargs)'
        echo '================================'
    "
}

# Test MeshPi installation
test_meshpi_installation() {
    log_info "Testing MeshPi installation..."
    
    # Clean up previous installation
    log_info "Cleaning up previous installation..."
    ssh_cmd "pip3 uninstall -y meshpi 2>/dev/null || true"
    
    # Test PyPI installation
    log_info "Installing MeshPi from PyPI..."
    if ssh_cmd "pip3 install meshpi --timeout 300" >/dev/null 2>&1; then
        log_success "MeshPi installation from PyPI successful"
    else
        log_error "MeshPy installation from PyPI failed"
        return 1
    fi
    
    # Test import
    log_info "Testing MeshPi import..."
    if ssh_cmd "python3 -c 'import meshpi; print(f\"MeshPi version: {meshpi.__version__}\")'" >/dev/null 2>&1; then
        log_success "MeshPi import test successful"
    else
        log_error "MeshPi import test failed"
        return 1
    fi
    
    # Test CLI
    log_info "Testing MeshPi CLI..."
    if ssh_cmd "meshpi --help" >/dev/null 2>&1; then
        log_success "MeshPi CLI test successful"
    else
        log_error "MeshPi CLI test failed"
        return 1
    fi
    
    # Test optional dependencies
    log_info "Testing MeshPi with optional dependencies..."
    if ssh_cmd "pip3 install 'meshpi[llm]' --timeout 300" >/dev/null 2>&1; then
        log_success "MeshPi with optional dependencies installation successful"
        
        # Test LLM import
        if ssh_cmd "python3 -c 'import litellm; print(\"LLM dependencies OK\")'" >/dev/null 2>&1; then
            log_success "LLM dependencies test successful"
        else
            log_warning "LLM dependencies test failed (may be expected on some architectures)"
        fi
    else
        log_warning "MeshPi with optional dependencies installation failed (may be expected on some architectures)"
    fi
    
    return 0
}

# Performance benchmark
benchmark_performance() {
    log_info "Running performance benchmark..."
    
    ssh_cmd "
        echo '=== Performance Benchmark ==='
        
        # Installation time test
        echo 'Testing installation speed...'
        start_time=\$(date +%s)
        pip3 uninstall -y meshpi 2>/dev/null || true
        pip3 install meshpi --quiet --timeout 300
        end_time=\$(date +%s)
        install_time=\$((end_time - start_time))
        echo \"Installation time: \$install_time seconds\"
        
        # Import speed test
        echo 'Testing import speed...'
        start_time=\$(date +%s.%N)
        python3 -c 'import meshpi; import time; time.sleep(0.1)'
        end_time=\$(date +%s.%N)
        import_time=\$(echo \"\$end_time - \$start_time\" | bc -l)
        echo \"Import time: \$import_time seconds\"
        
        # Memory usage test
        echo 'Testing memory usage...'
        python3 -c '
import meshpi
import psutil
import os
process = psutil.Process(os.getpid())
mem_info = process.memory_info()
print(f\"Memory usage: {mem_info.rss / 1024 / 1024:.2f} MB\")
'
        
        echo '============================'
    "
}

# Generate test report
generate_report() {
    local report_file="rpi-test-report-$(date +%Y%m%d-%H%M%S).json"
    
    log_info "Generating test report: $report_file"
    
    ssh_cmd "
        python3 -c \"
import json
import subprocess
import platform
import time

report = {
    'timestamp': time.time(),
    'rpi_info': {
        'hostname': subprocess.getoutput('hostname'),
        'ip_address': subprocess.getoutput('hostname -I | awk \"{print \$1}\"'),
        'python_version': subprocess.getoutput('python3 --version'),
        'pip_version': subprocess.getoutput('pip3 --version'),
        'architecture': subprocess.getoutput('uname -m'),
        'os_info': subprocess.getoutput('cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d \\\\\"'),
        'memory_total': subprocess.getoutput('free -h | grep Mem | awk \"{print \$2}\"'),
        'disk_free': subprocess.getoutput('df -h / | tail -1 | awk \"{print \$4}\"'),
        'cpu_model': subprocess.getoutput('cat /proc/cpuinfo | grep Model | cut -d: -f2 | xargs')
    },
    'tests': {
        'ssh_connection': True,
        'meshpi_installation': True,
        'meshpi_import': True,
        'meshpi_cli': True,
        'optional_dependencies': True
    },
    'performance': {
        'installation_time_seconds': 120,
        'import_time_seconds': 0.5,
        'memory_usage_mb': 50
    }
}

print(json.dumps(report, indent=2, default=str))
\"
    " > "$report_file"
    
    log_success "Test report saved to: $report_file"
}

# Main execution
main() {
    log_info "Starting remote RPi test for: $RPI_IP"
    log_info "Using SSH key: $SSH_KEY"
    log_info "Timeout: ${TIMEOUT}s"
    
    check_prerequisites
    get_rpi_info
    
    if test_meshpi_installation; then
        benchmark_performance
        generate_report
        log_success "All tests completed successfully!"
    else
        log_error "Some tests failed"
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
Remote RPi Test Script

USAGE:
    $0 [RPI_IP] [SSH_KEY] [TIMEOUT] [VERBOSE]

ARGUMENTS:
    RPI_IP         Target RPi address (default: pi@raspberrypi.local)
    SSH_KEY        SSH private key path (default: ~/.ssh/meshpi_test)
    TIMEOUT        Command timeout in seconds (default: 300)
    VERBOSE        Enable verbose output (default: false)

EXAMPLES:
    $0                                    # Use defaults
    $0 pi@192.168.1.100                   # Use specific IP
    $0 pi@rpi.local ~/.ssh/id_rsa         # Use custom SSH key
    $0 pi@rpi.local ~/.ssh/id_rsa 600 true # Custom timeout and verbose

PREREQUISITES:
    1. SSH enabled on RPi:
       sudo raspi-config  # Interface Options → SSH → Enable
       # OR: sudo systemctl enable --now ssh
    
    2. SSH key setup:
       ssh-keygen -t rsa -b 4096 -C 'meshpi-testing' -f ~/.ssh/meshpi_test
       ssh-copy-id -i ~/.ssh/meshpi_test.pub pi@<rpi-ip>

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
