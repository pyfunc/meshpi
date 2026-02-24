# RPi Repair Status Monitoring

This document explains how to monitor MeshPi repair progress on the Raspberry Pi side during automatic repairs.

## Overview

When `meshpi doctor` runs automatic repairs, it provides real-time status updates on the RPi itself. This allows users monitoring the device to see what's happening without needing to check the remote terminal.

## Status Files

The repair process creates several status files in `/tmp/`:

- `/tmp/meshpi-status.txt` - Current repair status
- `/tmp/meshpi-repair.log` - Detailed repair log
- `/tmp/meshpi-next-steps.txt` - Usage instructions after completion
- `/tmp/meshpi-help.txt` - Help information for failed repairs

## Monitoring Methods

### 1. Status Monitor Script

```bash
# On the RPi, run this to monitor status
./monitor-repair.sh

# Follow status changes in real-time
./monitor-repair.sh --follow

# Show full repair logs
./monitor-repair.sh --logs

# Show current status only
./monitor-repair.sh --status
```

### 2. Visual Status Display

```bash
# Visual dashboard with progress bar
./show-repair-status.sh

# Continuous monitoring with visual display
./show-repair-status.sh --continuous
```

### 3. Manual Status Check

```bash
# Check current status
cat /tmp/meshpi-status.txt

# View repair log
cat /tmp/meshpi-repair.log

# See next steps after completion
cat /tmp/meshpi-next-steps.txt
```

## Status Indicators

### Repair States

- 🔧 **REPAIRING...** - Repair in progress
- 🔍 **VERIFYING...** - Final verification in progress
- ✅ **COMPLETED** - Repair completed successfully
- ❌ **FAILED** - Repair failed, manual intervention needed

### Progress Tracking

The system tracks progress through multiple steps:
```
🔧 Step 1/5: sudo apt update && sudo apt install -y python3-full python3-venv
🔧 Step 2/5: python3 -m venv /home/pi/meshpi-env
🔧 Step 3/5: source /home/pi/meshpi-env/bin/activate
🔧 Step 4/5: pip install --upgrade pip
🔧 Step 5/5: pip install meshpi
```

## Visual Display Features

The visual status display includes:

- **Status Indicator** - Color-coded repair state
- **Progress Bar** - Visual progress through repair steps
- **Activity Log** - Recent repair activities
- **System Info** - Hostname, uptime, memory, temperature
- **Next Steps** - Instructions after successful completion

## Desktop Notifications

If available, the system sends desktop notifications:

```bash
# Success notification
notify-send 'MeshPi Doctor' '✅ Repair completed! MeshPi is ready to use.'

# This appears automatically when repair completes
```

## Example Output

### During Repair
```
╔══════════════════════════════════════════════════════════════╗
║                    MeshPi Repair Status                    ║
║                    Auto-Diagnostics & Repair                ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────┐
│         🔧  REPAIR IN PROGRESS  🔧         │
│            Please wait...            │
└─────────────────────────────────────────────────┘

Progress: [██████████████████████████████████████████████] 100% (5/5)

┌─────────────────────────────────────────────────┐
│                Activity Log                │
└─────────────────────────────────────────────────┘
  │ 🔧 MeshPi Doctor: Repair started at Mon Feb 24 10:45:12 GMT 2026
  │ ✅ Step 1 completed successfully
  │ ✅ Step 2 completed successfully
  │ ✅ Step 3 completed successfully
  │ ✅ Step 4 completed successfully
  │ ✅ Step 5 completed successfully
```

### After Completion
```
┌─────────────────────────────────────────────────┐
│         ✅  REPAIR COMPLETED  ✅         │
│           MeshPi is ready!           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                Next Steps                │
└─────────────────────────────────────────────────┘
  │ Usage: source /home/pi/meshpi-env/bin/activate && meshpi --help
```

## Troubleshooting

### Status File Not Found
```bash
# If no status file exists, repair may not be running
ls -la /tmp/meshpi-*

# Check if doctor process is running
ps aux | grep meshpi
```

### Repair Failed
```bash
# Check what went wrong
cat /tmp/meshpi-repair.log

# Get help information
cat /tmp/meshpi-help.txt

# Try manual repair
meshpi doctor --local
```

### Stuck Status
```bash
# Check if process is hung
ps aux | grep -E "(meshpi|pip|apt)"

# Kill hung processes if needed
sudo pkill -f meshpi
sudo pkill -f pip
```

## Integration with Doctor

The status monitoring integrates automatically with `meshpi doctor`:

1. **Start**: Doctor creates status files and signals repair start
2. **Progress**: Each repair step updates status and log
3. **Verification**: Final verification updates status
4. **Completion**: Success/failure status and next steps
5. **Cleanup**: Status files remain for review

## Best Practices

1. **Start monitoring early**: Run monitor before starting repair
2. **Use visual display**: Better for monitoring from console
3. **Check logs for issues**: Detailed logs help troubleshoot failures
4. **Follow next steps**: Instructions provided after successful completion
5. **Keep terminal open**: Status updates in real-time during repair

## File Locations

All status files are temporary and located in `/tmp/`:
- Cleared on reboot
- Accessible to all users
- Safe to delete after repair
- Automatically created by doctor process

This comprehensive status monitoring ensures users always know what's happening during MeshPi repairs on their Raspberry Pi devices.
