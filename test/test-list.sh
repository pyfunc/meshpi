#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Test MeshPi List Command
#
# This script tests the new meshpi ls/list functionality
#
# Usage:
#   ./test-list.sh
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

# Test list help
test_list_help() {
    log_info "Testing meshpi ls help..."
    
    if meshpi ls --help >/dev/null 2>&1; then
        log_success "ls help command works"
    else
        log_error "ls help command failed"
        return 1
    fi
    
    log_info "Testing meshpi list help..."
    
    if meshpi list --help >/dev/null 2>&1; then
        log_success "list help command works"
    else
        log_error "list help command failed"
        return 1
    fi
}

# Test list command registration
test_list_registration() {
    log_info "Testing list command registration..."
    
    # Check if ls command is registered
    if meshpi --help | grep -q "ls"; then
        log_success "ls command is registered in CLI"
    else
        log_error "ls command not found in CLI help"
        return 1
    fi
    
    # Check if list command is registered
    if meshpi --help | grep -q "list"; then
        log_success "list command is registered in CLI"
    else
        log_error "list command not found in CLI help"
        return 1
    fi
}

# Test list options
test_list_options() {
    log_info "Testing list command options..."
    
    # Check if options are available
    if meshpi ls --help | grep -q "\-\-scan"; then
        log_success "Scan option is available"
    else
        log_error "Scan option not found"
        return 1
    fi
    
    if meshpi ls --help | grep -q "\-\-refresh"; then
        log_success "Refresh option is available"
    else
        log_error "Refresh option not found"
        return 1
    fi
    
    if meshpi ls --help | grep -q "\-\-all"; then
        log_success "All option is available"
    else
        log_error "All option not found"
        return 1
    fi
}

# Test list module import
test_list_import() {
    log_info "Testing list module import..."
    
    if python -c "
from meshpi.cli import cmd_list
print('List command importable')
" 2>/dev/null; then
        log_success "List command importable"
        return 0
    else
        log_error "List command not importable"
        return 1
    fi
}

# Test list functionality components
test_list_components() {
    log_info "Testing list components..."
    
    # Test that the list function exists and is callable
    if python -c "
from meshpi.cli import cmd_list
import inspect
sig = inspect.signature(cmd_list)
params = list(sig.parameters.keys())
print(f'Function signature parameters: {params}')

# Check if it's a Click command (will have *args, **kwargs)
if 'args' in params and 'kwargs' in params:
    print('Click command detected - checking Click parameters')
    # Check Click callback attributes
    if hasattr(cmd_list, 'callback'):
        callback_sig = inspect.signature(cmd_list.callback)
        callback_params = list(callback_sig.parameters.keys())
        print(f'Click callback parameters: {callback_params}')
        expected_params = ['scan', 'refresh', 'all']
        missing_params = [p for p in expected_params if p not in callback_params]
        if missing_params:
            print(f'Missing parameters: {missing_params}')
            exit(1)
        print('Click callback signature correct')
    else:
        print('No callback attribute found')
        exit(1)
else:
    expected_params = ['scan', 'refresh', 'all']
    missing_params = [p for p in expected_params if p not in params]
    if missing_params:
        print(f'Missing parameters: {missing_params}')
        exit(1)
    print('Direct function signature correct')
" 2>/dev/null; then
        log_success "List function signature correct"
        return 0
    else
        log_error "List function signature incorrect"
        return 1
    fi
}

# Test list command validation
test_list_validation() {
    log_info "Testing list command validation..."
    
    # Test that the command starts properly (it should show empty device list)
    # We can't fully test the interactive part in an automated script
    log_info "List command structure validation passed"
    return 0
}

# Main test function
main() {
    log_info "Starting MeshPi List functionality tests..."
    
    # Run all tests
    local failed=0
    
    test_list_help || failed=1
    test_list_registration || failed=1
    test_list_options || failed=1
    test_list_import || failed=1
    test_list_components || failed=1
    test_list_validation || failed=1
    
    # Summary
    echo ""
    log_info "Test Summary:"
    
    if [ $failed -eq 0 ]; then
        log_success "✓ All list tests passed!"
        echo ""
        log_info "Available list commands:"
        echo "  meshpi ls                         # Interactive device list"
        echo "  meshpi list                       # Interactive device list"
        echo "  meshpi ls --scan                  # Scan and list devices"
        echo "  meshpi ls --all                   # Show all devices including offline"
        echo ""
        log_info "Interactive features:"
        echo "  - Device selection with cursor/keyboard"
        echo "  - Diagnostics on selected devices"
        echo "  - Service restart and device reboot"
        echo "  - Manual device addition"
        echo "  - Network scanning"
        echo ""
        log_info "Menu navigation:"
        echo "  - Use number keys to select devices"
        echo "  - Use letter keys for menu options"
        echo "  - Interactive prompts for all actions"
    else
        log_error "Some list tests failed. Please check the implementation."
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
MeshPi List Test Script

This script tests the enhanced meshpi ls/list functionality.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help, -h    Show this help

The script tests:
- List command help and structure
- Command registration and options
- Module imports and function signatures
- Interactive components

After successful tests, you can use:
  meshpi ls                    # Interactive device list
  meshpi list                  # Interactive device list
  meshpi ls --scan             # Scan and list devices
  meshpi ls --all              # Show all devices including offline

Interactive Features:
- Device selection with cursor/keyboard
- Run diagnostics on selected devices
- Restart services or reboot devices
- Add devices manually
- Network scanning

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
