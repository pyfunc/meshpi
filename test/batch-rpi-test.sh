#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Batch RPi Test Script - Test multiple Raspberry Pi devices simultaneously
#
# Usage:
#   ./batch-rpi-test.sh                                    # Use default device list
#   ./batch-rpi-test.sh --devices "pi@rpi1.local pi@rpi2.local"  # Custom device list
#   ./batch-rpi-test.sh --key ~/.ssh/custom_key            # Custom SSH key
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
SSH_KEY="${SSH_KEY:-~/.ssh/meshpi_test}"
DEVICES_FILE="${DEVICES_FILE:-rpi-devices.txt}"
TIMEOUT="${TIMEOUT:-300}"
PARALLEL_JOBS="${PARALLEL_JOBS:-5}"
VERBOSE="${VERBOSE:-false}"

# Default device list
DEFAULT_DEVICES=(
    "pi@raspberrypi.local"
    "pi@rpi-zero.local"
    "pi@rpi3.local"
    "pi@rpi4.local"
    "pi@rpi5.local"
)

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
    echo -e "${CYAN}[DEVICE]${NC} $1"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --devices)
                shift
                CUSTOM_DEVICES=($1)
                shift
                ;;
            --key)
                shift
                SSH_KEY="$1"
                shift
                ;;
            --timeout)
                shift
                TIMEOUT="$1"
                shift
                ;;
            --parallel)
                shift
                PARALLEL_JOBS="$1"
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help
show_help() {
    cat << EOF
Batch RPi Test Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --devices "list"     Space-separated list of RPi devices
    --key PATH           SSH private key path (default: ~/.ssh/meshpi_test)
    --timeout SECONDS    Command timeout per device (default: 300)
    --parallel JOBS      Max parallel tests (default: 5)
    --verbose            Enable verbose output
    --help, -h           Show this help

EXAMPLES:
    $0                                          # Use default device list
    $0 --devices "pi@rpi1.local pi@rpi2.local"  # Custom devices
    $0 --key ~/.ssh/id_rsa --parallel 3         # Custom key and parallelism

DEVICE FILE FORMAT:
    Create 'rpi-devices.txt' with one device per line:
    pi@rpi-zero.local
    pi@rpi3.local  
    pi@rpi4.local

PREREQUISITES:
    1. SSH enabled on all RPis:
       sudo systemctl enable --now ssh
    
    2. SSH key distributed to all devices:
       ssh-copy-id -i ~/.ssh/meshpi_test.pub pi@<device>

EOF
}

# Load device list
load_devices() {
    local devices=()
    
    if [[ -n "${CUSTOM_DEVICES:-}" ]]; then
        devices=("${CUSTOM_DEVICES[@]}")
        log_info "Using custom device list: ${#devices[@]} devices"
    elif [[ -f "$DEVICES_FILE" ]]; then
        log_info "Loading devices from file: $DEVICES_FILE"
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -n "$line" && ! "$line" =~ ^# ]] && devices+=("$line")
        done < "$DEVICES_FILE"
        log_info "Loaded ${#devices[@]} devices from file"
    else
        devices=("${DEFAULT_DEVICES[@]}")
        log_info "Using default device list: ${#devices[@]} devices"
        log_info "Create '$DEVICES_FILE' to specify custom devices"
    fi
    
    echo "${devices[@]}"
}

# Check SSH connection to a device
check_device_connection() {
    local device="$1"
    
    if timeout 10 ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$device" "echo 'OK'" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Test single device
test_device() {
    local device="$1"
    local device_id=$(echo "$device" | tr '@.' '_')
    local result_file="batch-test-results-${device_id}-$(date +%Y%m%d-%H%M%S).json"
    
    log_device "Testing device: $device"
    
    # Check connection first
    if ! check_device_connection "$device"; then
        log_warning "Cannot connect to $device - skipping"
        echo "{\"device\":\"$device\",\"status\":\"connection_failed\",\"timestamp\":$(date +%s)}" > "$result_file"
        return 1
    fi
    
    # Run comprehensive test
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$device" "
        set -euo pipefail
        
        # Initialize result
        result='{
            \"device\": \"$device\",
            \"timestamp\": $(date +%s),
            \"status\": \"testing\",
            \"tests\": {}
        }'
        
        # Test basic connectivity
        echo \"Testing basic connectivity...\"
        if python3 --version >/dev/null 2>&1 && pip3 --version >/dev/null 2>&1; then
            result=\$(echo \$result | jq '.tests.basic_connectivity = true')
        else
            result=\$(echo \$result | jq '.tests.basic_connectivity = false')
        fi
        
        # Test MeshPi installation
        echo \"Testing MeshPi installation...\"
        if pip3 uninstall -y meshpi 2>/dev/null && pip3 install meshpi --timeout 300 >/dev/null 2>&1; then
            result=\$(echo \$result | jq '.tests.meshpi_installation = true')
        else
            result=\$(echo \$result | jq '.tests.meshpi_installation = false')
        fi
        
        # Test MeshPi import
        echo \"Testing MeshPi import...\"
        if python3 -c 'import meshpi' >/dev/null 2>&1; then
            version=\$(python3 -c 'import meshpi; print(meshpi.__version__)' 2>/dev/null || echo 'unknown')
            result=\$(echo \$result | jq --arg version \"\$version\" '.tests.meshpi_import = true | .meshpi_version = \$version')
        else
            result=\$(echo \$result | jq '.tests.meshpi_import = false')
        fi
        
        # Test CLI functionality
        echo \"Testing MeshPi CLI...\"
        if meshpi --help >/dev/null 2>&1; then
            result=\$(echo \$result | jq '.tests.meshpi_cli = true')
        else
            result=\$(echo \$result | jq '.tests.meshpi_cli = false')
        fi
        
        # Test optional dependencies
        echo \"Testing optional dependencies...\"
        if pip3 install 'meshpi[llm]' --timeout 300 >/dev/null 2>&1; then
            result=\$(echo \$result | jq '.tests.optional_dependencies = true')
        else
            result=\$(echo \$result | jq '.tests.optional_dependencies = false')
        fi
        
        # Get system info
        echo \"Getting system information...\"
        system_info='{
            \"hostname\": \"\$(hostname)\",
            \"ip_address\": \"\$(hostname -I | awk \"{print \$1}\")\",
            \"python_version\": \"\$(python3 --version)\",
            \"pip_version\": \"\$(pip3 --version)\",
            \"architecture\": \"\$(uname -m)\",
            \"memory_total\": \"\$(free -h | grep Mem | awk \"{print \$2}\")\",
            \"disk_free\": \"\$(df -h / | tail -1 | awk \"{print \$4}\")\"
        }'
        result=\$(echo \$result | jq --argjson info \"\$system_info\" '.system_info = \$info')
        
        # Determine overall status
        passed_tests=\$(echo \$result | jq '.tests | to_entries[] | select(.value == true) | length')
        total_tests=\$(echo \$result | jq '.tests | to_entries | length')
        
        if [[ \$passed_tests -eq \$total_tests ]]; then
            result=\$(echo \$result | jq '.status = \"passed\"')
        elif [[ \$passed_tests -gt \$((total_tests / 2)) ]]; then
            result=\$(echo \$result | jq '.status = \"partial\"')
        else
            result=\$(echo \$result | jq '.status = \"failed\"')
        fi
        
        echo \$result
    " > "$result_file"
    
    # Display result summary
    if [[ -f "$result_file" ]]; then
        local status=$(jq -r '.status' "$result_file" 2>/dev/null || echo "unknown")
        local passed=$(jq -r '.tests | to_entries[] | select(.value == true) | length' "$result_file" 2>/dev/null || echo "0")
        local total=$(jq -r '.tests | to_entries | length' "$result_file" 2>/dev/null || echo "0")
        
        case "$status" in
            "passed")
                log_success "$device: ✅ All tests passed ($passed/$total)"
                ;;
            "partial")
                log_warning "$device: ⚠️  Partial success ($passed/$total)"
                ;;
            "failed")
                log_error "$device: ❌ Tests failed ($passed/$total)"
                ;;
            "connection_failed")
                log_error "$device: ❌ Connection failed"
                ;;
            *)
                log_warning "$device: ❓ Unknown status"
                ;;
        esac
    else
        log_error "$device: ❌ Test execution failed"
    fi
    
    return 0
}

# Aggregate all results
aggregate_results() {
    log_info "Aggregating test results..."
    
    local summary_file="batch-test-summary-$(date +%Y%m%d-%H%M%S).json"
    local report_file="batch-test-report-$(date +%Y%m%d-%H%M%S).md"
    
    # Create JSON summary
    echo "{
        \"timestamp\": $(date +%s),
        \"total_devices\": ${#devices[@]},
        \"results\": []
    }" > "$summary_file"
    
    # Process all result files
    for result_file in batch-test-results-*.json; do
        if [[ -f "$result_file" ]]; then
            jq --slurp '.[0] + .[1]' "$summary_file" "$result_file" > temp.json && mv temp.json "$summary_file"
        fi
    done
    
    # Generate markdown report
    cat > "$report_file" << EOF
# Batch RPi Test Report

**Generated:** $(date)
**Total Devices:** ${#devices[@]}
**SSH Key:** $SSH_KEY

## Results Summary

EOF
    
    # Add device results to report
    if command -v jq &> /dev/null && [[ -f "$summary_file" ]]; then
        jq -r '.results[] | 
"### \(.device | split("@")[1] | split(".")[0])
- **Status:** \(.status | ascii_upcase)
- **Tests Passed:** \(.tests | to_entries[] | select(.value == true) | length)/\(.tests | to_entries | length)
- **MeshPi Version:** \(.meshpi_version // "N/A")
- **Architecture:** \(.system_info.architecture // "N/A")
- **Python:** \(.system_info.python_version // "N/A")
"' "$summary_file" >> "$report_file"
    fi
    
    # Add overall statistics
    cat >> "$report_file" << EOF

## Statistics

EOF
    
    if command -v jq &> /dev/null && [[ -f "$summary_file" ]]; then
        local passed=$(jq '.results | map(select(.status == "passed")) | length' "$summary_file" 2>/dev/null || echo "0")
        local partial=$(jq '.results | map(select(.status == "partial")) | length' "$summary_file" 2>/dev/null || echo "0")
        local failed=$(jq '.results | map(select(.status == "failed")) | length' "$summary_file" 2>/dev/null || echo "0")
        local connection_failed=$(jq '.results | map(select(.status == "connection_failed")) | length' "$summary_file" 2>/dev/null || echo "0")
        
        cat >> "$report_file" << EOF
- ✅ **Passed:** $passed devices
- ⚠️ **Partial:** $partial devices  
- ❌ **Failed:** $failed devices
- 🔌 **Connection Failed:** $connection_failed devices

EOF
    fi
    
    log_success "Results aggregated:"
    log_success "  JSON summary: $summary_file"
    log_success "  Markdown report: $report_file"
}

# Main execution
main() {
    log_info "Starting batch RPi test"
    log_info "SSH Key: $SSH_KEY"
    log_info "Timeout: ${TIMEOUT}s per device"
    log_info "Parallel jobs: $PARALLEL_JOBS"
    
    # Load device list
    local devices=($(load_devices))
    log_info "Found ${#devices[@]} devices to test"
    
    # Test devices in parallel batches
    local batch_size=$PARALLEL_JOBS
    local total=${#devices[@]}
    
    for ((i=0; i<total; i+=batch_size)); do
        local batch=("${devices[@]:i:batch_size}")
        log_info "Testing batch $((i/batch_size + 1)): ${batch[@]}"
        
        # Run tests in parallel
        for device in "${batch[@]}"; do
            test_device "$device" &
        done
        
        # Wait for batch to complete
        wait
    done
    
    # Aggregate results
    aggregate_results
    
    log_success "Batch testing completed!"
}

# Parse arguments and run
parse_args "$@"
main
