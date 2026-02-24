#!/usr/bin/env python3
"""
RPi Repair Status Monitor - Python version

This script monitors the repair status on the RPi side and displays
progress information to the user. Can be run locally on the RPi.
"""

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
STATUS_FILE = "/tmp/meshpi-status.txt"
LOG_FILE = "/tmp/meshpi-repair.log"
NEXT_STEPS_FILE = "/tmp/meshpi-next-steps.txt"
HELP_FILE = "/tmp/meshpi-help.txt"

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'  # No Color

# Logging functions
def log_info(message):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def log_success(message):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def log_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def log_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def log_status(message):
    print(f"{Colors.MAGENTA}[STATUS]{Colors.NC} {message}")

def show_status():
    """Show current repair status"""
    if os.path.exists(STATUS_FILE):
        print(f"{Colors.CYAN}Current Repair Status:{Colors.NC}")
        print("----------------------------------------")
        with open(STATUS_FILE, 'r') as f:
            print(f.read())
        print("----------------------------------------")
    else:
        log_info("No repair status file found. Repair may not be in progress.")

def show_logs():
    """Show repair logs"""
    if os.path.exists(LOG_FILE):
        print(f"{Colors.CYAN}Repair Log:{Colors.NC}")
        print("----------------------------------------")
        with open(LOG_FILE, 'r') as f:
            print(f.read())
        print("----------------------------------------")
    else:
        log_info("No repair log file found.")

def show_next_steps():
    """Show next steps or help information"""
    if os.path.exists(NEXT_STEPS_FILE):
        print(f"{Colors.GREEN}Next Steps:{Colors.NC}")
        print("----------------------------------------")
        with open(NEXT_STEPS_FILE, 'r') as f:
            print(f.read())
        print("----------------------------------------")
    elif os.path.exists(HELP_FILE):
        print(f"{Colors.YELLOW}Help Information:{Colors.NC}")
        print("----------------------------------------")
        with open(HELP_FILE, 'r') as f:
            print(f.read())
        print("----------------------------------------")
    else:
        log_info("No next steps available.")

def monitor_status():
    """Monitor status changes in real-time"""
    log_info("Monitoring MeshPi repair status...")
    log_info("Press Ctrl+C to stop monitoring")
    
    last_content = ""
    
    try:
        while True:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    current_content = f.read().strip()
                
                if current_content != last_content:
                    print(f"\n{datetime.now().strftime('%H:%M:%S')} {Colors.CYAN}Status Update:{Colors.NC}")
                    print(f"{Colors.MAGENTA}{current_content}{Colors.NC}")
                    last_content = current_content
                    
                    # Check for completion
                    if any(indicator in current_content.lower() for indicator in ['✅', 'ready', 'completed']):
                        log_success("Repair appears to be completed!")
                        show_next_steps()
                        break
                    elif any(indicator in current_content.lower() for indicator in ['❌', 'failed', 'intervention']):
                        log_warning("Repair appears to have failed!")
                        show_logs()
                        break
            
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n{Colors.INFO}Monitoring stopped by user{Colors.NC}")

def create_status_indicator(status="unknown"):
    """Create visual status indicator"""
    indicators = {
        "repairing": f"{Colors.YELLOW}🔧 REPAIRING...{Colors.NC}",
        "verifying": f"{Colors.BLUE}🔍 VERIFYING...{Colors.NC}",
        "completed": f"{Colors.GREEN}✅ COMPLETED{Colors.NC}",
        "failed": f"{Colors.RED}❌ FAILED{Colors.NC}",
    }
    return indicators.get(status, f"{Colors.CYAN}❓ UNKNOWN{Colors.NC}")

def show_recent_logs():
    """Show recent log entries"""
    if os.path.exists(LOG_FILE):
        print(f"{Colors.BLUE}Recent Log Entries:{Colors.NC}")
        print("----------------------------------------")
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:] if len(lines) > 10 else lines
                for line in recent_lines:
                    print(line.rstrip())
        except Exception as e:
            print(f"Error reading log file: {e}")
        print("----------------------------------------")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="RPi Repair Status Monitor - Monitor MeshPi repair progress",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
FILES MONITORED:
    /tmp/meshpi-status.txt     Current repair status
    /tmp/meshpi-repair.log    Detailed repair log
    /tmp/meshpi-next-steps.txt Next steps after completion
    /tmp/meshpi-help.txt      Help information for failed repairs

EXAMPLES:
    %(prog)s                           # Show current status and recent logs
    %(prog)s --follow                  # Monitor status in real-time
    %(prog)s --logs                    # Show full repair logs
    %(prog)s --status                  # Show current status only

STATUS INDICATORS:
    🔧 REPAIRING...    Repair in progress
    🔍 VERIFYING...    Verification in progress
    ✅ COMPLETED       Repair completed successfully
    ❌ FAILED          Repair failed
        """
    )
    
    parser.add_argument('-f', '--follow', action='store_true',
                       help='Monitor status changes in real-time')
    parser.add_argument('-l', '--logs', action='store_true',
                       help='Show full repair logs')
    parser.add_argument('-s', '--status', action='store_true',
                       help='Show current status only')
    
    args = parser.parse_args()
    
    # Execute based on mode
    if args.logs:
        show_logs()
    elif args.status:
        show_status()
    elif args.follow:
        monitor_status()
    else:
        # Default: show current status and information
        print(f"{Colors.CYAN}MeshPi Repair Status Monitor{Colors.NC}")
        print("==================================")
        
        show_status()
        print()
        
        if os.path.exists(LOG_FILE):
            show_recent_logs()
            print()
        
        show_next_steps()
        
        print()
        log_info("Options:")
        print("  --follow     Monitor status changes in real-time")
        print("  --logs       Show full repair logs")
        print("  --status     Show current status only")
        print("  --help       Show this help")

if __name__ == "__main__":
    main()
