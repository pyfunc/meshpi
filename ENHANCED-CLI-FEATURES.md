# Enhanced MeshPi CLI Features

This document describes the comprehensive enhanced features added to the MeshPi CLI, providing advanced device management, monitoring, and automation capabilities.

## 🚀 New Features Overview

### 🖥️ Enhanced Device Management

#### Auto-Detection
- **Automatic RPi Discovery**: Scans local network for Raspberry Pi devices
- **Smart Filtering**: Excludes network infrastructure (.1, .254 gateways)
- **Strict RPI Detection**: Uses multiple indicators to avoid false positives
- **Auto-Configuration**: Attempts to install and start MeshPi on discovered devices

#### Interactive Device Selection
- **Arrow Key Navigation**: Use ↑↓ to navigate device lists
- **Multi-Selection**: SPACE to select multiple devices
- **Visual Feedback**: Highlighted current selection with indicators
- **Batch Operations**: Perform actions on selected devices

#### Enhanced Device Menu
- **Shell Access**: Direct SSH shell to devices
- **System Management**: Update, upgrade, package installation
- **Service Control**: Start/stop/restart/enable/disable services
- **File Operations**: Upload/download files, directory management

### 📊 Device Monitoring

#### Real-time Monitoring
```bash
meshpi monitor                    # Monitor all devices once
meshpi monitor --continuous       # Continuous monitoring
meshpi monitor --interval 30      # Monitor every 30 seconds
meshpi monitor --group servers    # Monitor specific group
```

#### Monitoring Features
- **System Status**: Uptime, load, memory, temperature
- **MeshPi Status**: Installation and service status
- **Group Monitoring**: Monitor predefined device groups
- **Continuous Updates**: Real-time status refresh

### 👥 Group Management

#### Group Operations
```bash
meshpi group create servers          # Create device group
meshpi group add-device servers pi@rpi  # Add device to group
meshpi group list                   # List all groups
meshpi group status servers          # Check group status
meshpi group exec servers "uptime"   # Execute on group
meshpi group system-update servers   # Update all in group
```

#### Group Features
- **Device Organization**: Logical grouping of devices
- **Batch Operations**: Execute commands on entire groups
- **Group Monitoring**: Status monitoring for groups
- **Persistent Storage**: Groups saved to configuration

### 🔗 Enhanced SSH Management

#### SSH Operations
```bash
meshpi ssh shell pi@192.168.1.100   # Interactive SSH shell
meshpi ssh batch "uptime"           # Batch command execution
meshpi ssh system-update            # Update package lists
meshpi ssh system-upgrade            # Upgrade packages
meshpi ssh transfer file.txt /home/pi/  # File transfer
```

#### SSH Features
- **Interactive Shell**: Direct SSH access with automatic authentication
- **Batch Commands**: Execute commands on multiple devices
- **System Management**: Package updates and upgrades
- **File Transfer**: Upload/download files to/from devices
- **Auto-Authentication**: SSH key and password support

### 🔧 Advanced Features

#### Port Conflict Resolution
- **Automatic Detection**: Identifies processes blocking ports
- **Process Termination**: Safely kills conflicting processes
- **Local & Remote**: Works on both local and remote systems
- **Service Restart**: Automatically restarts services after port cleanup

#### Network Auto-Detection
- **Smart Network Scanning**: Auto-detects local network range
- **Interface Detection**: Uses actual network interface configuration
- **Conservative Scanning**: Only scans relevant subnets
- **Fallback Support**: Graceful fallback to default ranges

## 🎯 Usage Examples

### Device Discovery and Management
```bash
# Auto-discover and manage devices
meshpi ls
→ Auto-detects RPi devices on network
→ Interactive device selection
→ Enhanced management options

# Select device and run diagnostics
→ Navigate with arrow keys
→ SPACE to select device
→ ENTER to confirm
→ Choose from enhanced menu:
  1. Run diagnostics
  2. Restart service
  3. Shell access
  4. System update
  5. Batch operations
```

### Group-Based Operations
```bash
# Create a server group
meshpi group create servers --description "Production servers"

# Add devices to group
meshpi group add-device servers pi@192.168.1.100
meshpi group add-device servers pi@192.168.1.101

# Monitor entire group
meshpi monitor --group servers --continuous

# Update all servers in group
meshpi group system-update servers

# Execute command on group
meshpi group exec servers "sudo apt upgrade -y"
```

### SSH Operations
```bash
# Interactive shell access
meshpi ssh shell pi@192.168.1.100
→ Opens SSH shell directly
→ Automatic authentication
→ Return to MeshPi with 'exit'

# Batch operations
meshpi ssh batch "uptime" --target pi@192.168.1.100
meshpi ssh batch "df -h" --parallel

# System management
meshpi ssh system-update --target pi@192.168.1.100
meshpi ssh system-upgrade --target pi@192.168.1.100 --safe
```

### Monitoring
```bash
# One-time monitoring
meshpi monitor
→ Shows status of all devices
→ System information
→ MeshPi status

# Continuous monitoring
meshpi monitor --continuous --interval 30
→ Updates every 30 seconds
→ Real-time status
→ Ctrl+C to stop

# Group monitoring
meshpi monitor --group servers
→ Monitor specific group
→ Group-specific status
```

## 🔧 Technical Implementation

### Auto-Detection Algorithm
1. **Network Discovery**: Detect local network interface and range
2. **SSH Scanning**: Scan for SSH-enabled devices
3. **Infrastructure Filtering**: Exclude routers, gateways, switches
4. **RPI Detection**: Strict verification using multiple indicators
5. **Auto-Configuration**: Install and configure MeshPi if needed

### Interactive Interface
- **Terminal Raw Mode**: Direct keyboard input handling
- **Arrow Key Support**: Full navigation with arrow keys
- **Multi-Selection**: SPACE to toggle selection
- **Visual Feedback**: Real-time interface updates
- **Graceful Exit**: Clean terminal restoration

### Group Management
- **JSON Storage**: Groups stored in `~/.meshpi/groups.json`
- **Device References**: SSH target strings for devices
- **Metadata Support**: Descriptions and creation timestamps
- **Batch Operations**: Parallel execution on group members

### SSH Management
- **Authentication Fallback**: Key → password → manual
- **Connection Pooling**: Efficient connection management
- **Error Handling**: Graceful failure handling
- **Parallel Execution**: Concurrent operations on multiple devices

## 📋 Command Reference

### Device Management
- `meshpi ls` - Enhanced device list with auto-detection
- `meshpi monitor` - Device monitoring
- `meshpi monitor --group <name>` - Group monitoring
- `meshpi monitor --continuous` - Continuous monitoring

### Group Management
- `meshpi group create <name>` - Create group
- `meshpi group list` - List groups
- `meshpi group add-device <name> <target>` - Add device
- `meshpi group status <name>` - Group status
- `meshpi group exec <name> <command>` - Execute on group

### SSH Operations
- `meshpi ssh shell <target>` - Interactive shell
- `meshpi ssh batch <command>` - Batch execution
- `meshpi ssh system-update` - Update packages
- `meshpi ssh system-upgrade` - Upgrade packages
- `meshpi ssh transfer <local> <remote>` - File transfer

### Enhanced Host
- `meshpi host --ssh <target>` - Remote host service
- `meshpi host --ssh <target> --agent` - With agent
- `meshpi host --ssh <target> --port <port>` - Custom port

## 🎉 Benefits

### For System Administrators
- **Centralized Management**: Single interface for all devices
- **Automation**: Batch operations and scripting
- **Monitoring**: Real-time status and alerts
- **Group Operations**: Logical device organization

### For Developers
- **Interactive Interface**: Easy device navigation
- **Shell Access**: Direct SSH integration
- **File Management**: Built-in file operations
- **Service Control**: Complete service management

### For Operations
- **Auto-Discovery**: Automatic device detection
- **Port Management**: Conflict resolution
- **System Updates**: Centralized package management
- **Monitoring**: Continuous health checks

## 🔍 Troubleshooting

### Common Issues
- **SSH Authentication**: Check SSH keys and passwords
- **Network Scanning**: Verify network connectivity
- **Port Conflicts**: Use built-in port cleanup
- **Group Storage**: Check `~/.meshpi/` directory permissions

### Debug Mode
```bash
# Enable verbose output
meshpi ls --verbose
meshpi monitor --debug
meshpi ssh batch --dry-run "command"
```

This enhanced CLI provides a comprehensive solution for Raspberry Pi fleet management with professional-grade features for monitoring, automation, and control.
