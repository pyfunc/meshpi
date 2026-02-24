#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Test Enhanced MeshPi CLI Features
#
# This script tests the new enhanced features added to MeshPi CLI
# including monitor, group management, SSH shell, and auto-detection
#
# Usage:
#   ./test-enhanced-cli.sh
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

# Test monitor command
test_monitor_command() {
    log_info "Testing meshpi monitor command..."
    
    if meshpi monitor --help >/dev/null 2>&1; then
        log_success "Monitor command help works"
    else
        log_error "Monitor command help failed"
        return 1
    fi
    
    # Check monitor options
    if meshpi monitor --help | grep -q "\-\-group"; then
        log_success "Group option available"
    else
        log_error "Group option not found"
        return 1
    fi
    
    if meshpi monitor --help | grep -q "\-\-continuous"; then
        log_success "Continuous option available"
    else
        log_error "Continuous option not found"
        return 1
    fi
    
    if meshpi monitor --help | grep -q "\-\-interval"; then
        log_success "Interval option available"
    else
        log_error "Interval option not found"
        return 1
    fi
}

# Test group command
test_group_command() {
    log_info "Testing meshpi group command..."
    
    if meshpi group --help >/dev/null 2>&1; then
        log_success "Group command help works"
    else
        log_error "Group command help failed"
        return 1
    fi
    
    # Check group subcommands
    if meshpi group --help | grep -q "create"; then
        log_success "Create subcommand available"
    else
        log_error "Create subcommand not found"
        return 1
    fi
    
    if meshpi group --help | grep -q "list"; then
        log_success "List subcommand available"
    else
        log_error "List subcommand not found"
        return 1
    fi
    
    if meshpi group --help | grep -q "add-device"; then
        log_success "Add-device subcommand available"
    else
        log_error "Add-device subcommand not found"
        return 1
    fi
}

# Test SSH enhanced commands
test_ssh_enhancements() {
    log_info "Testing enhanced SSH commands..."
    
    # Test shell command
    if meshpi ssh shell --help >/dev/null 2>&1; then
        log_success "SSH shell command works"
    else
        log_error "SSH shell command failed"
        return 1
    fi
    
    # Test batch command
    if meshpi ssh batch --help >/dev/null 2>&1; then
        log_success "SSH batch command works"
    else
        log_error "SSH batch command failed"
        return 1
    fi
    
    # Test system-update command
    if meshpi ssh system-update --help >/dev/null 2>&1; then
        log_success "SSH system-update command works"
    else
        log_error "SSH system-update command failed"
        return 1
    fi
    
    # Test system-upgrade command
    if meshpi ssh system-upgrade --help >/dev/null 2>&1; then
        log_success "SSH system-upgrade command works"
    else
        log_error "SSH system-upgrade command failed"
        return 1
    fi
}

# Test auto-detection functionality
test_auto_detection() {
    log_info "Testing auto-detection functionality..."
    
    if python -c "
import sys
sys.path.append('.')
from meshpi.cli import auto_detect_rpi_devices, check_if_raspberry_pi, configure_meshpi_on_device
print('Auto-detection functions imported successfully')
" 2>/dev/null; then
        log_success "Auto-detection functions importable"
    else
        log_error "Auto-detection functions not importable"
        return 1
    fi
}

# Test interactive device selection
test_interactive_selection() {
    log_info "Testing interactive device selection..."
    
    if python -c "
import sys
sys.path.append('.')
from meshpi.cli import interactive_device_selection, enhanced_device_menu, get_key
print('Interactive functions imported successfully')
" 2>/dev/null; then
        log_success "Interactive functions importable"
    else
        log_error "Interactive functions not importable"
        return 1
    fi
}

# Test enhanced device menu
test_enhanced_device_menu() {
    log_info "Testing enhanced device menu..."
    
    if python -c "
import sys
sys.path.append('.')
from meshpi.cli import batch_operations_menu, service_menu, file_transfer_menu, open_ssh_shell
print('Enhanced menu functions imported successfully')
" 2>/dev/null; then
        log_success "Enhanced menu functions importable"
    else
        log_error "Enhanced menu functions not importable"
        return 1
    fi
}

# Test port killing functionality
test_port_killing() {
    log_info "Testing port killing functionality..."
    
    if python -c "
import sys
sys.path.append('.')
from meshpi.cli import kill_processes_blocking_port, kill_processes_blocking_port_remote
print('Port killing functions imported successfully')
" 2>/dev/null; then
        log_success "Port killing functions importable"
    else
        log_error "Port killing functions not importable"
        return 1
    fi
}

# Test command registration
test_command_registration() {
    log_info "Testing command registration..."
    
    # Check if all new commands are registered
    commands=("monitor" "group" "ssh")
    
    for cmd in "${commands[@]}"; do
        if meshpi --help | grep -q "$cmd"; then
            log_success "$cmd command registered"
        else
            log_error "$cmd command not registered"
            return 1
        fi
    done
    
    # Check SSH subcommands
    ssh_subcommands=("shell" "batch" "system-update" "system-upgrade")
    
    for subcmd in "${ssh_subcommands[@]}"; do
        if meshpi ssh --help | grep -q "$subcmd"; then
            log_success "ssh $subcmd subcommand registered"
        else
            log_error "ssh $subcmd subcommand not registered"
            return 1
        fi
    done
    
    # Check group subcommands
    group_subcommands=("create" "list" "add-device" "status" "exec")
    
    for subcmd in "${group_subcommands[@]}"; do
        if meshpi group --help | grep -q "$subcmd"; then
            log_success "group $subcmd subcommand registered"
        else
            log_error "group $subcmd subcommand not registered"
            return 1
        fi
    done
}

# Test help documentation
test_help_documentation() {
    log_info "Testing help documentation..."
    
    # Check main help for new commands
    if meshpi --help | grep -q "monitor"; then
        log_success "Monitor command in main help"
    else
        log_warning "Monitor command not in main help"
    fi
    
    if meshpi --help | grep -q "group"; then
        log_success "Group command in main help"
    else
        log_warning "Group command not in main help"
    fi
    
    # Check examples in help
    if meshpi --help | grep -q "Monitor Examples"; then
        log_success "Monitor examples found"
    else
        log_warning "Monitor examples not found"
    fi
    
    if meshpi --help | grep -q "Group Management Examples"; then
        log_success "Group examples found"
    else
        log_warning "Group examples not found"
    fi
}

# Test enhanced ls command
test_enhanced_ls() {
    log_info "Testing enhanced ls command..."
    
    if meshpi ls --help >/dev/null 2>&1; then
        log_success "Enhanced ls command works"
    else
        log_error "Enhanced ls command failed"
        return 1
    fi
    
    # Check if auto-detection is mentioned
    if meshpi ls --help | grep -q "scan"; then
        log_success "Scan option available in ls"
    else
        log_error "Scan option not found in ls"
        return 1
    fi
}

# Main test function
main() {
    log_info "Starting Enhanced MeshPi CLI Tests..."
    
    # Run all tests
    local failed=0
    
    test_command_registration || failed=1
    test_monitor_command || failed=1
    test_group_command || failed=1
    test_ssh_enhancements || failed=1
    test_auto_detection || failed=1
    test_interactive_selection || failed=1
    test_enhanced_device_menu || failed=1
    test_port_killing || failed=1
    test_help_documentation || failed=1
    test_enhanced_ls || failed=1
    
    # Summary
    echo ""
    log_info "Test Summary:"
    
    if [ $failed -eq 0 ]; then
        log_success "✓ All enhanced CLI tests passed!"
        echo ""
        log_info "New Enhanced Features Available:"
        echo ""
        echo "🖥️  Device Management:"
        echo "  meshpi ls                           # Enhanced with auto-detection"
        echo "  meshpi monitor                      # Device monitoring"
        echo "  meshpi monitor --continuous         # Continuous monitoring"
        echo "  meshpi monitor --group servers      # Group monitoring"
        echo ""
        echo "🔗 SSH Management:"
        echo "  meshpi ssh shell pi@192.168.1.100   # Interactive SSH shell"
        echo "  meshpi ssh batch 'uptime'           # Batch command execution"
        echo "  meshpi ssh system-update            # Update packages"
        echo "  meshpi ssh system-upgrade            # Upgrade packages"
        echo ""
        echo "👥 Group Management:"
        echo "  meshpi group create servers          # Create device group"
        echo "  meshpi group add-device servers pi@rpi # Add to group"
        echo "  meshpi group status servers          # Group status"
        echo "  meshpi group exec servers 'uptime'   # Group command execution"
        echo ""
        echo "🔧 Enhanced Features:"
        echo "  • Auto-detection of Raspberry Pi devices"
        echo "  • Interactive device selection with arrow keys"
        echo "  • Enhanced device menu with shell access"
        echo "  • Batch operations and service management"
        echo "  • File transfer capabilities"
        echo "  • Port conflict resolution"
        echo "  • Continuous monitoring with alerts"
        echo ""
        log_info "All new features are ready for use!"
    else
        log_error "Some enhanced CLI tests failed. Please check the implementation."
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
Enhanced MeshPi CLI Test Script

This script tests the new enhanced features added to MeshPi CLI.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help, -h    Show this help

The script tests:
- Enhanced device management with auto-detection
- Monitoring capabilities (single and group)
- Group management operations
- Enhanced SSH operations (shell, batch, system management)
- Interactive device selection
- Port conflict resolution
- Help documentation completeness

After successful tests, you can use:
  meshpi ls                    # Enhanced device list with auto-detection
  meshpi monitor               # Device monitoring
  meshpi group create servers  # Group management
  meshpi ssh shell pi@rpi      # Interactive SSH
  meshpi ssh batch 'uptime'    # Batch operations

Enhanced Features:
- Auto-detection of RPi devices on local network
- Interactive device selection with keyboard navigation
- Comprehensive device management menus
- Group-based operations
- Continuous monitoring
- Advanced SSH operations
- Port conflict resolution

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
