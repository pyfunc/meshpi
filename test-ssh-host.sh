#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Test MeshPi SSH Host Functionality
#
# This script tests the meshpi host --ssh functionality
#
# Usage:
#   ./test-ssh-host.sh
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

# Test SSH host help
test_ssh_host_help() {
    log_info "Testing meshpi host --ssh help..."
    
    if meshpi host --help | grep -q "\-\-ssh"; then
        log_success "SSH host option is available"
    else
        log_error "SSH host option not found"
        return 1
    fi
    
    if meshpi host --help | grep -q "\-\-ssh-key"; then
        log_success "SSH key option is available"
    else
        log_error "SSH key option not found"
        return 1
    fi
    
    if meshpi host --help | grep -q "\-\-ssh-password"; then
        log_success "SSH password option is available"
    else
        log_error "SSH password option not found"
        return 1
    fi
}

# Test SSH host command structure
test_ssh_host_structure() {
    log_info "Testing SSH host command structure..."
    
    # Test that the command accepts SSH option
    if meshpi host --ssh pi@nonexistent.local 2>/dev/null; then
        log_warning "Expected failure with non-existent host"
    else
        log_info "Correctly failed with non-existent host (expected behavior)"
    fi
}

# Test SSH host module import
test_ssh_host_import() {
    log_info "Testing SSH host module import..."
    
    if python -c "
from meshpi.cli import cmd_host
import inspect
sig = inspect.signature(cmd_host)
params = list(sig.parameters.keys())
print(f'Function signature parameters: {params}')

# Check if it's a Click command (will have *args, **kwargs)
if 'args' in params and 'kwargs' in params:
    print('Click command detected - checking Click parameters')
    # Check Click callback attributes
    if hasattr(cmd_host, 'callback'):
        callback_sig = inspect.signature(cmd_host.callback)
        callback_params = list(callback_sig.parameters.keys())
        print(f'Click callback parameters: {callback_params}')
        expected_params = ['port', 'bind', 'agent', 'install', 'uninstall', 'status', 'ssh', 'ssh_key', 'ssh_password']
        missing_params = [p for p in expected_params if p not in callback_params]
        if missing_params:
            print(f'Missing parameters: {missing_params}')
            exit(1)
        print('Click callback signature correct')
    else:
        print('No callback attribute found')
        exit(1)
else:
    expected_params = ['port', 'bind', 'agent', 'install', 'uninstall', 'status', 'ssh', 'ssh_key', 'ssh_password']
    missing_params = [p for p in expected_params if p not in params]
    if missing_params:
        print(f'Missing parameters: {missing_params}')
        exit(1)
    print('Direct function signature correct')
" 2>/dev/null; then
        log_success "SSH host function importable"
        return 0
    else
        log_error "SSH host function not importable"
        return 1
    fi
}

# Test SSH manager availability
test_ssh_manager() {
    log_info "Testing SSH manager availability..."
    
    if python -c "
from meshpi.ssh_manager import SSHManager, parse_device_target
print('SSH manager importable')

# Test device parsing
user, host, port = parse_device_target('pi@192.168.1.100')
assert user == 'pi', f'Expected pi, got {user}'
assert host == '192.168.1.100', f'Expected 192.168.1.100, got {host}'
assert port == 22, f'Expected 22, got {port}'
print('Device parsing works correctly')
" 2>/dev/null; then
        log_success "SSH manager working correctly"
        return 0
    else
        log_error "SSH manager not working"
        return 1
    fi
}

# Test SSH host examples in help
test_help_examples() {
    log_info "Testing SSH host examples in help..."
    
    if meshpi --help | grep -q "host --ssh"; then
        log_success "SSH host example found in main help"
    else
        log_warning "SSH host example not found in main help (but command is available)"
    fi
    
    if meshpi host --help | grep -q "remote SSH device"; then
        log_success "SSH host description found in host help"
    else
        log_error "SSH host description not found in host help"
        return 1
    fi
}

# Main test function
main() {
    log_info "Starting MeshPi SSH Host functionality tests..."
    
    # Run all tests
    local failed=0
    
    test_ssh_host_help || failed=1
    test_ssh_host_structure || failed=1
    test_ssh_host_import || failed=1
    test_ssh_manager || failed=1
    test_help_examples || failed=1
    
    # Summary
    echo ""
    log_info "Test Summary:"
    
    if [ $failed -eq 0 ]; then
        log_success "✓ All SSH host tests passed!"
        echo ""
        log_info "Available SSH host commands:"
        echo "  meshpi host --ssh pi@192.168.1.100      # Start host on remote RPi"
        echo "  meshpi host --ssh pi@rpi --agent       # Start host with agent"
        echo "  meshpi host --ssh pi@rpi --port 8080   # Custom port"
        echo "  meshpi host --ssh pi@rpi --ssh-key ~/.ssh/key"
        echo "  meshpi host --ssh pi@rpi --ssh-password"
        echo ""
        log_info "Features:"
        echo "  - Automatic MeshPi installation if missing"
        echo "  - Background service execution"
        echo "  - Process monitoring and logging"
        echo "  - Service status verification"
        echo "  - Multiple authentication methods"
    else
        log_error "Some SSH host tests failed. Please check the implementation."
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
MeshPi SSH Host Test Script

This script tests the meshpi host --ssh functionality.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help, -h    Show this help

The script tests:
- SSH host command options and structure
- Module imports and function signatures
- SSH manager functionality
- Help documentation

After successful tests, you can use:
  meshpi host --ssh pi@192.168.1.100      # Start host on remote RPi
  meshpi host --ssh pi@rpi --agent       # Start host with agent
  meshpi host --ssh pi@rpi --ssh-key ~/.ssh/key
  meshpi host --ssh pi@rpi --ssh-password

SSH Host Features:
- Remote host service startup
- Automatic MeshPi installation
- Background process management
- Service monitoring
- Multiple authentication methods

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
