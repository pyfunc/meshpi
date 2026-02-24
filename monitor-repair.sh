#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# RPi Repair Status Monitor
#
# This script monitors the repair status on the RPi side and displays
# progress information to the user. Can be run locally on the RPi.
#
# Usage:
#   ./monitor-repair.sh
#   ./monitor-repair.sh --follow
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
STATUS_FILE="/tmp/meshpi-status.txt"
LOG_FILE="/tmp/meshpi-repair.log"
NEXT_STEPS_FILE="/tmp/meshpi-next-steps.txt"
HELP_FILE="/tmp/meshpi-help.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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

log_status() {
    echo -e "${MAGENTA}[STATUS]${NC} $1"
}

# Show current status
show_status() {
    if [[ -f "$STATUS_FILE" ]]; then
        echo -e "${CYAN}Current Repair Status:${NC}"
        echo "----------------------------------------"
        cat "$STATUS_FILE"
        echo "----------------------------------------"
    else
        log_info "No repair status file found. Repair may not be in progress."
    fi
}

# Show repair logs
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        echo -e "${CYAN}Repair Log:${NC}"
        echo "----------------------------------------"
        cat "$LOG_FILE"
        echo "----------------------------------------"
    else
        log_info "No repair log file found."
    fi
}

# Show next steps
show_next_steps() {
    if [[ -f "$NEXT_STEPS_FILE" ]]; then
        echo -e "${GREEN}Next Steps:${NC}"
        echo "----------------------------------------"
        cat "$NEXT_STEPS_FILE"
        echo "----------------------------------------"
    elif [[ -f "$HELP_FILE" ]]; then
        echo -e "${YELLOW}Help Information:${NC}"
        echo "----------------------------------------"
        cat "$HELP_FILE"
        echo "----------------------------------------"
    else
        log_info "No next steps available."
    fi
}

# Monitor status changes
monitor_status() {
    log_info "Monitoring MeshPi repair status..."
    log_info "Press Ctrl+C to stop monitoring"
    
    local last_content=""
    
    while true; do
        if [[ -f "$STATUS_FILE" ]]; then
            local current_content=$(cat "$STATUS_FILE")
            if [[ "$current_content" != "$last_content" ]]; then
                echo -e "\n$(date '+%H:%M:%S') ${CYAN}Status Update:${NC}"
                echo -e "${MAGENTA}$current_content${NC}"
                last_content="$current_content"
                
                # Check for completion
                if [[ "$current_content" =~ ✅|ready|completed ]]; then
                    log_success "Repair appears to be completed!"
                    show_next_steps
                    break
                elif [[ "$current_content" =~ ❌|failed|intervention ]]; then
                    log_warning "Repair appears to have failed!"
                    show_logs
                    break
                fi
            fi
        fi
        
        sleep 2
    done
}

# Create visual status indicator
create_status_indicator() {
    local status="${1:-unknown}"
    
    case "$status" in
        "repairing")
            echo -e "${YELLOW}🔧 REPAIRING...${NC}"
            ;;
        "verifying")
            echo -e "${BLUE}🔍 VERIFYING...${NC}"
            ;;
        "completed")
            echo -e "${GREEN}✅ COMPLETED${NC}"
            ;;
        "failed")
            echo -e "${RED}❌ FAILED${NC}"
            ;;
        *)
            echo -e "${CYAN}❓ UNKNOWN${NC}"
            ;;
    esac
}

# Main function
main() {
    local follow_mode=false
    local show_logs_mode=false
    local show_status_mode=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --follow|-f)
                follow_mode=true
                shift
                ;;
            --logs|-l)
                show_logs_mode=true
                shift
                ;;
            --status|-s)
                show_status_mode=true
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
    
    # Execute based on mode
    if [[ "$show_logs_mode" == true ]]; then
        show_logs
    elif [[ "$show_status_mode" == true ]]; then
        show_status
    elif [[ "$follow_mode" == true ]]; then
        monitor_status
    else
        # Default: show current status and information
        echo -e "${CYAN}MeshPi Repair Status Monitor${NC}"
        echo "=================================="
        
        show_status
        echo ""
        
        if [[ -f "$LOG_FILE" ]]; then
            echo -e "${BLUE}Recent Log Entries:${NC}"
            echo "----------------------------------------"
            tail -10 "$LOG_FILE" 2>/dev/null || echo "No recent log entries"
            echo "----------------------------------------"
            echo ""
        fi
        
        show_next_steps
        
        echo ""
        log_info "Options:"
        echo "  --follow     Monitor status changes in real-time"
        echo "  --logs       Show full repair logs"
        echo "  --status     Show current status only"
        echo "  --help       Show this help"
    fi
}

# Help function
show_help() {
    cat << EOF
RPi Repair Status Monitor

This script monitors and displays the MeshPi repair progress on the RPi.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --follow, -f     Monitor status changes in real-time
    --logs, -l       Show full repair logs
    --status, -s     Show current status only
    --help, -h       Show this help

FILES MONITORED:
    /tmp/meshpi-status.txt     Current repair status
    /tmp/meshpi-repair.log    Detailed repair log
    /tmp/meshpi-next-steps.txt Next steps after completion
    /tmp/meshpi-help.txt      Help information for failed repairs

EXAMPLES:
    $0                           # Show current status and recent logs
    $0 --follow                  # Monitor status in real-time
    $0 --logs                    # Show full repair logs
    $0 --status                  # Show current status only

STATUS INDICATORS:
    🔧 REPAIRING...    Repair in progress
    🔍 VERIFYING...    Verification in progress
    ✅ COMPLETED       Repair completed successfully
    ❌ FAILED          Repair failed

EOF
}

# Run main function with all arguments
main "$@"
