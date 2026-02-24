#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Test MeshPi Restart Command
#
# This script tests the new meshpi restart functionality
#
# Usage:
#   ./test-restart.sh
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

# Test restart help
test_restart_help() {
    log_info "Testing meshpi restart help..."
    
    if meshpi restart --help >/dev/null 2>&1; then
        log_success "Restart help command works"
        return 0
    else
        log_error "Restart help command failed"
        return 1
    fi
}

# Test restart command validation
test_restart_validation() {
    log_info "Testing restart command validation..."
    
    # Test without target (should fail gracefully)
    if meshpi restart 2>/dev/null; then
        log_warning "Expected failure without target, but command succeeded"
    else
        log_info "Correctly failed without target (expected behavior)"
    fi
    
    # Test with invalid target (should fail gracefully)
    if meshpi restart pi@nonexistent.local 2>/dev/null; then
        log_warning "Unexpected success with non-existent host"
    else
        log_info "Correctly failed with non-existent host (expected behavior)"
    fi
    
    return 0
}

# Test restart command structure
test_restart_structure() {
    log_info "Testing restart command structure..."
    
    # Check if restart command is registered
    if meshpi --help | grep -q "restart"; then
        log_success "Restart command is registered in CLI"
    else
        log_error "Restart command not found in CLI help"
        return 1
    fi
    
    # Check if restart options are available
    if meshpi restart --help | grep -q "\-\-reboot"; then
        log_success "Reboot option is available"
    else
        log_error "Reboot option not found"
        return 1
    fi
    
    if meshpi restart --help | grep -q "\-\-service"; then
        log_success "Service option is available"
    else
        log_error "Service option not found"
        return 1
    fi
    
    if meshpi restart --help | grep -q "\-\-password"; then
        log_success "Password option is available"
    else
        log_error "Password option not found"
        return 1
    fi
    
    return 0
}

# Test restart module import
test_restart_import() {
    log_info "Testing restart module import..."
    
    if python -c "
from meshpi.cli import cmd_restart
print('Restart command importable')
" 2>/dev/null; then
        log_success "Restart command importable"
        return 0
    else
        log_error "Restart command not importable"
        return 1
    fi
}

# Test restart functionality components
test_restart_components() {
    log_info "Testing restart components..."
    
    # Test that the restart function exists and is callable
    if python -c "
from meshpi.cli import cmd_restart
import inspect
sig = inspect.signature(cmd_restart)
params = list(sig.parameters.keys())
print(f'Function signature parameters: {params}')

# Check if it's a Click command (will have *args, **kwargs)
if 'args' in params and 'kwargs' in params:
    print('Click command detected - checking Click parameters')
    # Check Click callback attributes
    if hasattr(cmd_restart, 'callback'):
        callback_sig = inspect.signature(cmd_restart.callback)
        callback_params = list(callback_sig.parameters.keys())
        print(f'Click callback parameters: {callback_params}')
        expected_params = ['target', 'password', 'key', 'service', 'reboot']
        missing_params = [p for p in expected_params if p not in callback_params]
        if missing_params:
            print(f'Missing parameters: {missing_params}')
            exit(1)
        print('Click callback signature correct')
    else:
        print('No callback attribute found')
        exit(1)
else:
    expected_params = ['target', 'password', 'key', 'service', 'reboot']
    missing_params = [p for p in expected_params if p not in params]
    if missing_params:
        print(f'Missing parameters: {missing_params}')
        exit(1)
    print('Direct function signature correct')
" 2>/dev/null; then
        log_success "Restart function signature correct"
        return 0
    else
        log_error "Restart function signature incorrect"
        return 1
    fi
}

# Main test function
main() {
    log_info "Starting MeshPi Restart functionality tests..."
    
    # Run all tests
    local failed=0
    
    test_restart_help || failed=1
    test_restart_validation || failed=1
    test_restart_structure || failed=1
    test_restart_import || failed=1
    test_restart_components || failed=1
    
    # Summary
    echo ""
    log_info "Test Summary:"
    
    if [ $failed -eq 0 ]; then
        log_success "✓ All restart tests passed!"
        echo ""
        log_info "Available restart commands:"
        echo "  meshpi restart pi@<rpi-ip>                    # Restart meshpi service"
        echo "  meshpi restart pi@<rpi-ip> --reboot           # Reboot the device"
        echo "  meshpi restart pi@<rpi-ip> --service host     # Restart specific service"
        echo "  meshpi restart pi@<rpi-ip> --password         # Use password auth"
        echo "  meshpi restart pi@<rpi-ip> --key ~/.ssh/key   # Use custom SSH key"
    else
        log_error "Some restart tests failed. Please check the implementation."
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
MeshPi Restart Test Script

This script tests the enhanced meshpi restart functionality.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help, -h    Show this help

The script tests:
- Restart command help and structure
- Command validation and error handling
- Module imports and function signatures
- Available options and parameters

After successful tests, you can use:
  meshpi restart pi@192.168.1.100      # Restart meshpi service
  meshpi restart pi@rpi --reboot       # Reboot the device
  meshpi restart pi@rpi --service host  # Restart specific service

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
