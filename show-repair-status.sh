#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# RPi Repair Status Display Script
#
# This script creates a visual status display on the RPi during repair.
# It shows progress using ASCII art and status indicators.
#
# Usage:
#   ./show-repair-status.sh
#   ./show-repair-status.sh --continuous
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
STATUS_FILE="/tmp/meshpi-status.txt"
LOG_FILE="/tmp/meshpi-repair.log"
NEXT_STEPS_FILE="/tmp/meshpi-next-steps.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Clear screen function
clear_screen() {
    clear 2>/dev/null || printf '\033[2J\033[H'
}

# Draw header
draw_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}                    ${WHITE}MeshPi Repair Status${NC}                    ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                    ${CYAN}Auto-Diagnostics & Repair${NC}                    ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Draw progress bar
draw_progress_bar() {
    local current=$1
    local total=$2
    local width=50
    
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    echo -e "${CYAN}Progress: [${NC}"
    printf "${GREEN}%*s${NC}" $filled | tr ' ' '█'
    printf "${DIM}%*s${NC}" $empty | tr ' ' '░'
    echo -e "${CYAN}] ${NC}${WHITE}%d%%${NC} ($current/$total)"
}

# Draw status indicator
draw_status_indicator() {
    local status="$1"
    
    case "$status" in
        *"repairing"*|*"Repairing"*|*"⚡"*)
            echo -e "${YELLOW}┌─────────────────────────────────────────────────┐${NC}"
            echo -e "${YELLOW}│${NC}         ${WHITE}🔧  REPAIR IN PROGRESS  🔧${NC}         ${YELLOW}│${NC}"
            echo -e "${YELLOW}│${NC}            ${YELLOW}Please wait...${NC}            ${YELLOW}│${NC}"
            echo -e "${YELLOW}└─────────────────────────────────────────────────┘${NC}"
            ;;
        *"verifying"*|*"Verifying"*|*"⏸️"*)
            echo -e "${BLUE}┌─────────────────────────────────────────────────┐${NC}"
            echo -e "${BLUE}│${NC}         ${WHITE}🔍  VERIFYING REPAIR  🔍${NC}         ${BLUE}│${NC}"
            echo -e "${BLUE}│${NC}            ${BLUE}Final checks...${NC}            ${BLUE}│${NC}"
            echo -e "${BLUE}└─────────────────────────────────────────────────┘${NC}"
            ;;
        *"completed"*|*"ready"*|*"✅"*)
            echo -e "${GREEN}┌─────────────────────────────────────────────────┐${NC}"
            echo -e "${GREEN}│${NC}         ${WHITE}✅  REPAIR COMPLETED  ✅${NC}         ${GREEN}│${NC}"
            echo -e "${GREEN}│${NC}           ${GREEN}MeshPi is ready!${NC}           ${GREEN}│${NC}"
            echo -e "${GREEN}└─────────────────────────────────────────────────┘${NC}"
            ;;
        *"failed"*|*"intervention"*|*"❌"*)
            echo -e "${RED}┌─────────────────────────────────────────────────┐${NC}"
            echo -e "${RED}│${NC}         ${WHITE}❌  REPAIR FAILED  ❌${NC}         ${RED}│${NC}"
            echo -e "${RED}│${NC}          ${RED}Manual help needed${NC}          ${RED}│${NC}"
            echo -e "${RED}└─────────────────────────────────────────────────┘${NC}"
            ;;
        *)
            echo -e "${CYAN}┌─────────────────────────────────────────────────┐${NC}"
            echo -e "${CYAN}│${NC}         ${WHITE}❓  STATUS UNKNOWN  ❓${NC}         ${CYAN}│${NC}"
            echo -e "${CYAN}│${NC}            ${CYAN}Checking...${NC}            ${CYAN}│${NC}"
            echo -e "${CYAN}└─────────────────────────────────────────────────┘${NC}"
            ;;
    esac
}

# Draw activity log
draw_activity_log() {
    echo -e "${CYAN}┌─────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}                ${WHITE}Activity Log${NC}                ${CYAN}│${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────┘${NC}"
    
    if [[ -f "$LOG_FILE" ]]; then
        local log_lines=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
        if [[ "$log_lines" -gt 0 ]]; then
            # Show last 8 lines with formatting
            tail -8 "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do
                echo -e "  ${DIM}│${NC} ${line}"
            done
        else
            echo -e "  ${DIM}│${NC} ${YELLOW}No activity logged yet${NC}"
        fi
    else
        echo -e "  ${DIM}│${NC} ${YELLOW}No log file found${NC}"
    fi
    echo ""
}

# Draw next steps
draw_next_steps() {
    if [[ -f "$NEXT_STEPS_FILE" ]]; then
        echo -e "${GREEN}┌─────────────────────────────────────────────────┐${NC}"
        echo -e "${GREEN}│${NC}                ${WHITE}Next Steps${NC}                ${GREEN}│${NC}"
        echo -e "${GREEN}└─────────────────────────────────────────────────┘${NC}"
        while IFS= read -r line; do
            echo -e "  ${GREEN}│${NC} ${line}"
        done < "$NEXT_STEPS_FILE"
        echo ""
    fi
}

# Draw system info
draw_system_info() {
    echo -e "${CYAN}┌─────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}                ${WHITE}System Info${NC}                ${CYAN}│${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────┘${NC}"
    
    local hostname=$(hostname 2>/dev/null || echo "Unknown")
    local uptime=$(uptime -p 2>/dev/null | cut -d' ' -f2- || echo "Unknown")
    local memory=$(free -h | grep Mem | awk '{print $3 "/" $2}' 2>/dev/null || echo "Unknown")
    local temp=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000 "°C"}' || echo "Unknown")
    
    echo -e "  ${CYAN}│${NC} Hostname: ${WHITE}$hostname${NC}"
    echo -e "  ${CYAN}│${NC} Uptime:   ${WHITE}$uptime${NC}"
    echo -e "  ${CYAN}│${NC} Memory:   ${WHITE}$memory${NC}"
    echo -e "  ${CYAN}│${NC} Temperature: ${WHITE}$temp${NC}"
    echo ""
}

# Main display function
display_status() {
    clear_screen
    draw_header
    
    # Get current status
    local current_status="unknown"
    if [[ -f "$STATUS_FILE" ]]; then
        current_status=$(cat "$STATUS_FILE" 2>/dev/null || echo "unknown")
    fi
    
    # Draw status indicator
    draw_status_indicator "$current_status"
    echo ""
    
    # Draw progress (if we can determine it)
    if [[ -f "$LOG_FILE" ]]; then
        local total_steps=$(grep -c "Step " "$LOG_FILE" 2>/dev/null || echo "0")
        local completed_steps=$(grep -c "✅.*completed" "$LOG_FILE" 2>/dev/null || echo "0")
        
        if [[ "$total_steps" -gt 0 ]]; then
            draw_progress_bar "$completed_steps" "$total_steps"
            echo ""
        fi
    fi
    
    # Draw activity log
    draw_activity_log
    
    # Draw next steps if completed
    if [[ "$current_status" =~ completed|ready ]]; then
        draw_next_steps
    fi
    
    # Draw system info
    draw_system_info
    
    # Footer
    echo -e "${CYAN}┌─────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}  ${DIM}Last updated: $(date '+%H:%M:%S')${NC}              ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${DIM}Press Ctrl+C to exit monitoring${NC}            ${CYAN}│${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────┘${NC}"
}

# Continuous monitoring
continuous_monitor() {
    echo -e "${GREEN}Starting continuous monitoring...${NC}"
    echo -e "${DIM}Press Ctrl+C to stop${NC}"
    sleep 2
    
    while true; do
        display_status
        sleep 3
    done
}

# Help function
show_help() {
    cat << EOF
RPi Repair Status Display

This script shows a visual status display of MeshPi repair progress.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --continuous, -c    Continuous monitoring mode
    --help, -h          Show this help

DISPLAY FEATURES:
    - Visual status indicators with colors
    - Progress bar for multi-step repairs
    - Real-time activity log
    - System information
    - Next steps after completion

STATUS INDICATORS:
    🔧 REPAIRING...    Repair in progress
    🔍 VERIFYING...    Verification in progress
    ✅ COMPLETED       Repair completed successfully
    ❌ FAILED          Repair failed

EXAMPLES:
    $0                 # Show current status once
    $0 --continuous    # Monitor status continuously

EOF
}

# Main execution
main() {
    local continuous_mode=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --continuous|-c)
                continuous_mode=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    if [[ "$continuous_mode" == true ]]; then
        continuous_monitor
    else
        display_status
    fi
}

# Define DIM color if not set
DIM='\033[2m'

# Run main function
main "$@"
