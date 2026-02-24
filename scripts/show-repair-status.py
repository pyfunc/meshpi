#!/usr/bin/env python3
"""
RPi Repair Status Display Script - Python version

This script creates a visual status display on the RPi during repair.
It shows progress using ASCII art and status indicators.
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime

# Configuration
STATUS_FILE = "/tmp/meshpi-status.txt"
LOG_FILE = "/tmp/meshpi-repair.log"
NEXT_STEPS_FILE = "/tmp/meshpi-next-steps.txt"

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    WHITE = '\033[1;37m'
    DIM = '\033[2m'
    NC = '\033[0m'  # No Color

def clear_screen():
    """Clear the terminal screen"""
    try:
        subprocess.run(['clear'], check=True)
    except:
        print('\033[2J\033[H', end='')

def draw_header():
    """Draw the header"""
    print(f"{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.CYAN}║{Colors.NC}                    {Colors.WHITE}MeshPi Repair Status{Colors.NC}                    {Colors.CYAN}║{Colors.NC}")
    print(f"{Colors.CYAN}║{Colors.NC}                    {Colors.CYAN}Auto-Diagnostics & Repair{Colors.NC}                    {Colors.CYAN}║{Colors.NC}")
    print(f"{Colors.CYAN}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()

def draw_progress_bar(current, total):
    """Draw a progress bar"""
    width = 50
    percentage = (current * 100) // total if total > 0 else 0
    filled = (current * width) // total if total > 0 else 0
    empty = width - filled
    
    print(f"{Colors.CYAN}Progress: [{Colors.NC}", end='')
    print(f"{Colors.GREEN}{'█' * filled}{Colors.NC}", end='')
    print(f"{Colors.DIM}{'░' * empty}{Colors.NC}", end='')
    print(f"{Colors.CYAN}] {Colors.NC}{Colors.WHITE}{percentage}%{Colors.NC} ({current}/{total})")

def draw_status_indicator(status):
    """Draw status indicator based on current status"""
    status_lower = status.lower()
    
    if any(keyword in status_lower for keyword in ['repairing', '⚡']):
        print(f"{Colors.YELLOW}┌─────────────────────────────────────────────────┐{Colors.NC}")
        print(f"{Colors.YELLOW}│{Colors.NC}         {Colors.WHITE}🔧  REPAIR IN PROGRESS  🔧{Colors.NC}         {Colors.YELLOW}│{Colors.NC}")
        print(f"{Colors.YELLOW}│{Colors.NC}            {Colors.YELLOW}Please wait...{Colors.NC}            {Colors.YELLOW}│{Colors.NC}")
        print(f"{Colors.YELLOW}└─────────────────────────────────────────────────┘{Colors.NC}")
    elif any(keyword in status_lower for keyword in ['verifying', '⏸️']):
        print(f"{Colors.BLUE}┌─────────────────────────────────────────────────┐{Colors.NC}")
        print(f"{Colors.BLUE}│{Colors.NC}         {Colors.WHITE}🔍  VERIFYING REPAIR  🔍{Colors.NC}         {Colors.BLUE}│{Colors.NC}")
        print(f"{Colors.BLUE}│{Colors.NC}            {Colors.BLUE}Final checks...{Colors.NC}            {Colors.BLUE}│{Colors.NC}")
        print(f"{Colors.BLUE}└─────────────────────────────────────────────────┘{Colors.NC}")
    elif any(keyword in status_lower for keyword in ['completed', 'ready', '✅']):
        print(f"{Colors.GREEN}┌─────────────────────────────────────────────────┐{Colors.NC}")
        print(f"{Colors.GREEN}│{Colors.NC}         {Colors.WHITE}✅  REPAIR COMPLETED  ✅{Colors.NC}         {Colors.GREEN}│{Colors.NC}")
        print(f"{Colors.GREEN}│{Colors.NC}           {Colors.GREEN}MeshPi is ready!{Colors.NC}           {Colors.GREEN}│{Colors.NC}")
        print(f"{Colors.GREEN}└─────────────────────────────────────────────────┘{Colors.NC}")
    elif any(keyword in status_lower for keyword in ['failed', 'intervention', '❌']):
        print(f"{Colors.RED}┌─────────────────────────────────────────────────┐{Colors.NC}")
        print(f"{Colors.RED}│{Colors.NC}         {Colors.WHITE}❌  REPAIR FAILED  ❌{Colors.NC}         {Colors.RED}│{Colors.NC}")
        print(f"{Colors.RED}│{Colors.NC}          {Colors.RED}Manual help needed{Colors.NC}          {Colors.RED}│{Colors.NC}")
        print(f"{Colors.RED}└─────────────────────────────────────────────────┘{Colors.NC}")
    else:
        print(f"{Colors.CYAN}┌─────────────────────────────────────────────────┐{Colors.NC}")
        print(f"{Colors.CYAN}│{Colors.NC}         {Colors.WHITE}❓  STATUS UNKNOWN  ❓{Colors.NC}         {Colors.CYAN}│{Colors.NC}")
        print(f"{Colors.CYAN}│{Colors.NC}            {Colors.CYAN}Checking...{Colors.NC}            {Colors.CYAN}│{Colors.NC}")
        print(f"{Colors.CYAN}└─────────────────────────────────────────────────┘{Colors.NC}")

def draw_activity_log():
    """Draw activity log"""
    print(f"{Colors.CYAN}┌─────────────────────────────────────────────────┐{Colors.NC}")
    print(f"{Colors.CYAN}│{Colors.NC}                {Colors.WHITE}Activity Log{Colors.NC}                {Colors.CYAN}│{Colors.NC}")
    print(f"{Colors.CYAN}└─────────────────────────────────────────────────┘{Colors.NC}")
    
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                if lines:
                    # Show last 8 lines
                    recent_lines = lines[-8:]
                    for line in recent_lines:
                        print(f"  {Colors.DIM}│{Colors.NC} {line.rstrip()}")
                else:
                    print(f"  {Colors.DIM}│{Colors.NC} {Colors.YELLOW}No activity logged yet{Colors.NC}")
        except Exception as e:
            print(f"  {Colors.DIM}│{Colors.NC} {Colors.YELLOW}Error reading log: {e}{Colors.NC}")
    else:
        print(f"  {Colors.DIM}│{Colors.NC} {Colors.YELLOW}No log file found{Colors.NC}")
    print()

def draw_next_steps():
    """Draw next steps if available"""
    if os.path.exists(NEXT_STEPS_FILE):
        print(f"{Colors.GREEN}┌─────────────────────────────────────────────────┐{Colors.NC}")
        print(f"{Colors.GREEN}│{Colors.NC}                {Colors.WHITE}Next Steps{Colors.NC}                {Colors.GREEN}│{Colors.NC}")
        print(f"{Colors.GREEN}└─────────────────────────────────────────────────┘{Colors.NC}")
        try:
            with open(NEXT_STEPS_FILE, 'r') as f:
                for line in f:
                    print(f"  {Colors.GREEN}│{Colors.NC} {line.rstrip()}")
        except Exception as e:
            print(f"  {Colors.GREEN}│{Colors.NC} Error reading next steps: {e}")
        print()

def draw_system_info():
    """Draw system information"""
    print(f"{Colors.CYAN}┌─────────────────────────────────────────────────┐{Colors.NC}")
    print(f"{Colors.CYAN}│{Colors.NC}                {Colors.WHITE}System Info{Colors.NC}                {Colors.CYAN}│{Colors.NC}")
    print(f"{Colors.CYAN}└─────────────────────────────────────────────────┘{Colors.NC}")
    
    try:
        hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
    except:
        hostname = "Unknown"
    
    try:
        uptime_result = subprocess.run(['uptime', '-p'], capture_output=True, text=True)
        uptime = ' '.join(uptime_result.stdout.strip().split()[1:]) if uptime_result.returncode == 0 else "Unknown"
    except:
        uptime = "Unknown"
    
    try:
        memory_result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        if memory_result.returncode == 0:
            mem_line = [line for line in memory_result.stdout.split('\n') if line.startswith('Mem:')][0]
            memory_parts = mem_line.split()
            memory = f"{memory_parts[2]}/{memory_parts[1]}"
        else:
            memory = "Unknown"
    except:
        memory = "Unknown"
    
    try:
        if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = f.read().strip()
                temp_c = f"{int(temp) / 1000:.1f}°C"
        else:
            temp_c = "Unknown"
    except:
        temp_c = "Unknown"
    
    print(f"  {Colors.CYAN}│{Colors.NC} Hostname: {Colors.WHITE}{hostname}{Colors.NC}")
    print(f"  {Colors.CYAN}│{Colors.NC} Uptime:   {Colors.WHITE}{uptime}{Colors.NC}")
    print(f"  {Colors.CYAN}│{Colors.NC} Memory:   {Colors.WHITE}{memory}{Colors.NC}")
    print(f"  {Colors.CYAN}│{Colors.NC} Temperature: {Colors.WHITE}{temp_c}{Colors.NC}")
    print()

def display_status():
    """Main display function"""
    clear_screen()
    draw_header()
    
    # Get current status
    current_status = "unknown"
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                current_status = f.read().strip()
        except:
            current_status = "unknown"
    
    # Draw status indicator
    draw_status_indicator(current_status)
    print()
    
    # Draw progress (if we can determine it)
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                log_content = f.read()
                total_steps = log_content.count("Step ")
                completed_steps = log_content.count("✅") and log_content.count("completed")
                
                if total_steps > 0:
                    draw_progress_bar(completed_steps, total_steps)
                    print()
        except:
            pass
    
    # Draw activity log
    draw_activity_log()
    
    # Draw next steps if completed
    if any(keyword in current_status.lower() for keyword in ['completed', 'ready']):
        draw_next_steps()
    
    # Draw system info
    draw_system_info()
    
    # Footer
    print(f"{Colors.CYAN}┌─────────────────────────────────────────────────┐{Colors.NC}")
    print(f"{Colors.CYAN}│{Colors.NC}  {Colors.DIM}Last updated: {datetime.now().strftime('%H:%M:%S')}{Colors.NC}              {Colors.CYAN}│{Colors.NC}")
    print(f"{Colors.CYAN}│{Colors.NC}  {Colors.DIM}Press Ctrl+C to exit monitoring{Colors.NC}            {Colors.CYAN}│{Colors.NC}")
    print(f"{Colors.CYAN}└─────────────────────────────────────────────────┘{Colors.NC}")

def continuous_monitor():
    """Continuous monitoring mode"""
    print(f"{Colors.GREEN}Starting continuous monitoring...{Colors.NC}")
    print(f"{Colors.DIM}Press Ctrl+C to stop{Colors.NC}")
    time.sleep(2)
    
    try:
        while True:
            display_status()
            time.sleep(3)
    except KeyboardInterrupt:
        print(f"\n{Colors.DIM}Monitoring stopped by user{Colors.NC}")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="RPi Repair Status Display - Visual status display for MeshPi repair",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
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
    %(prog)s                 # Show current status once
    %(prog)s --continuous    # Monitor status continuously
        """
    )
    
    parser.add_argument('-c', '--continuous', action='store_true',
                       help='Continuous monitoring mode')
    
    args = parser.parse_args()
    
    if args.continuous:
        continuous_monitor()
    else:
        display_status()

if __name__ == "__main__":
    main()
