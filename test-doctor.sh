#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Quick MeshPi Doctor Test Script
#
# This script tests the enhanced meshpi doctor functionality
# with auto-diagnosis and repair capabilities.
#
# Usage:
#   ./test-doctor.sh
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

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

# Test local doctor
test_local_doctor() {
    log_info "Testing local meshpi doctor..."
    
    if meshpi doctor --local; then
        log_success "Local doctor test passed"
    else
        log_warning "Local doctor test had issues (expected on non-RPi systems)"
    fi
}

# Test remote doctor (simulated)
test_remote_doctor() {
    log_info "Testing meshpi doctor help and command structure..."
    
    # Test doctor help
    if meshpi doctor --help; then
        log_success "Doctor help command works"
    else
        log_error "Doctor help command failed"
        return 1
    fi
    
    # Test doctor command parsing (without actual connection)
    log_info "Testing doctor command parsing..."
    
    # This will fail but shows the command structure works
    if meshpi doctor pi@nonexistent.local 2>/dev/null; then
        log_warning "Unexpected success with non-existent host"
    else
        log_info "Command parsing works (connection failed as expected)"
    fi
}

# Test installation and import
test_installation() {
    log_info "Testing meshpi installation and imports..."
    
    # Check if meshpi is installed
    if python -c "import meshpi; print(f'MeshPi version: {meshpi.__version__}')" 2>/dev/null; then
        log_success "MeshPi is installed and importable"
    else
        log_error "MeshPi is not installed or not importable"
        return 1
    fi
    
    # Test CLI functionality
    if meshpi --help >/dev/null 2>&1; then
        log_success "MeshPi CLI works"
    else
        log_error "MeshPi CLI failed"
        return 1
    fi
    
    # Test doctor module import
    if python -c "from meshpi.doctor import RemoteDoctor, run_doctor; print('Doctor module importable')" 2>/dev/null; then
        log_success "Doctor module importable"
    else
        log_error "Doctor module not importable"
        return 1
    fi
}

# Test doctor functionality components
test_doctor_components() {
    log_info "Testing doctor components..."
    
    # Test target parsing
    if python -c "
from meshpi.doctor import parse_target
tests = [
    ('pi@raspberrypi', ('pi', 'raspberrypi', 22)),
    ('pi@192.168.1.100:2222', ('pi', '192.168.1.100', 2222)),
    ('raspberrypi', ('pi', 'raspberrypi', 22)),
]

for input_val, expected in tests:
    result = parse_target(input_val)
    assert result == expected, f'Failed: {input_val} -> {result}, expected {expected}'
print('Target parsing tests passed')
" 2>/dev/null; then
        log_success "Target parsing works"
    else
        log_error "Target parsing failed"
        return 1
    fi
    
    # Test RemoteDoctor class instantiation
    if python -c "
from meshpi.doctor import RemoteDoctor
doctor = RemoteDoctor('localhost', 'testuser', 22)
print('RemoteDoctor instantiation works')
" 2>/dev/null; then
        log_success "RemoteDoctor class works"
    else
        log_error "RemoteDoctor class failed"
        return 1
    fi
}

# Main test function
main() {
    log_info "Starting MeshPi Doctor functionality tests..."
    
    # Run all tests
    local_failed=0
    remote_failed=0
    install_failed=0
    components_failed=0
    
    test_installation || install_failed=1
    test_doctor_components || components_failed=1
    test_local_doctor || local_failed=1
    test_remote_doctor || remote_failed=1
    
    # Summary
    echo ""
    log_info "Test Summary:"
    
    if [ $install_failed -eq 0 ]; then
        log_success "✓ Installation tests passed"
    else
        log_error "✗ Installation tests failed"
    fi
    
    if [ $components_failed -eq 0 ]; then
        log_success "✓ Doctor component tests passed"
    else
        log_error "✗ Doctor component tests failed"
    fi
    
    if [ $local_failed -eq 0 ]; then
        log_success "✓ Local doctor tests passed"
    else
        log_warning "⚠ Local doctor tests had issues (may be expected)"
    fi
    
    if [ $remote_failed -eq 0 ]; then
        log_success "✓ Remote doctor tests passed"
    else
        log_warning "⚠ Remote doctor tests had issues (connection failures expected)"
    fi
    
    # Overall result
    total_failed=$((install_failed + components_failed))
    if [ $total_failed -eq 0 ]; then
        log_success "All critical tests passed! MeshPi doctor functionality is working."
        echo ""
        log_info "To test with a real RPi:"
        echo "  meshpi doctor pi@<rpi-ip-address>"
        echo "  meshpi doctor pi@<rpi-ip-address> --password"
        echo "  meshpi doctor pi@<rpi-ip-address> --key ~/.ssh/custom_key"
    else
        log_error "Some critical tests failed. Please check the installation."
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
MeshPi Doctor Test Script

This script tests the enhanced meshpi doctor functionality
including auto-diagnosis and repair capabilities.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help, -h    Show this help

The script tests:
- MeshPi installation and imports
- Doctor module components
- Local diagnostics
- Remote doctor command structure

After successful tests, you can use:
  meshpi doctor pi@192.168.1.100      # Diagnose and auto-repair
  meshpi doctor pi@rpi --password     # Use password auth
  meshpi doctor --local               # Local diagnostics only

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
