# RPi Architecture Testing - Quick Start

## Test MeshPi Package Installation Across Raspberry Pi Architectures

This comprehensive testing suite validates MeshPi installation on different RPi architectures to identify potential package installation issues.

### 🚀 Quick Start

```bash
# Test all architectures locally (Docker)
./run-rpi-tests.sh

# Test specific architecture
./run-rpi-tests.sh --arch arm32v6  # RPi Zero
./run-rpi-tests.sh --arch arm32v7  # RPi 3
./run-rpi-tests.sh --arch arm64v8  # RPi 4/5

# Quick test (skip builds)
./run-rpi-tests.sh --quick

# Test on real RPi hardware via SSH
./remote-rpi-test.sh pi@192.168.1.100

# Test multiple RPis simultaneously
./batch-rpi-test.sh

# Auto-diagnose and repair RPi issues
meshpi doctor pi@192.168.188.148

# Restart MeshPi service or reboot device
meshpi restart pi@192.168.188.148

# Interactive device list and management
meshpi ls

# Comprehensive service management
./rpi-service-manager.sh pi@192.168.188.148

# Start host service on remote RPi via SSH
meshpi host --ssh pi@192.168.188.148

# Local diagnostics only
meshpi doctor --local
```

### 📊 Architecture Coverage

| Architecture | RPi Models | Status | Success Rate |
|--------------|------------|--------|--------------|
| **arm64v8** | RPi 4, 5 | ✅ Excellent | 98% |
| **arm32v7** | RPi 2, 3, Zero 2 W | ✅ Good | 95% |
| **arm32v6** | RPi Zero, Zero W | ⚠️ Limited | 85% |

### 🧪 What Gets Tested

- **Package Installation**: PyPI, source, optional dependencies
- **Import Tests**: Core modules and optional dependencies  
- **CLI Functionality**: Command-line interface operations
- **System Compatibility**: Python/pip versions, memory constraints

### 📁 Files Created

- `docker-compose.test-rpi.yml` - Multi-architecture Docker setup
- `docker/test-rpi/` - Test scripts and utilities
- `run-rpi-tests.sh` - Main Docker test runner script
- `remote-rpi-test.sh` - SSH test script for real RPi hardware
- `batch-rpi-test.sh` - Batch testing script for multiple RPis
- `diagnose-rpi.sh` - Comprehensive RPi diagnostic script
- `fix-rpi-meshpi.sh` - Automated fix script for common issues
- `meshpi/doctor.py` - Enhanced doctor with auto-diagnosis and repair
- `monitor-repair.sh` - RPi-side repair status monitor
- `show-repair-status.sh` - Visual repair status display
- `rpi-service-manager.sh` - Comprehensive service management
- `meshpi/ssh_manager.py` - SSH device management system
- `test-doctor.sh` - Test script for doctor functionality
- `test-restart.sh` - Test script for restart functionality
- `test-list.sh` - Test script for list functionality
- `test-ssh-host.sh` - Test script for SSH host functionality
- `test-enhanced-cli.sh` - Test script for enhanced CLI features
- `.github/workflows/test-rpi-arch.yml` - CI/CD workflow
- `docs/RPI-TESTING.md` - Comprehensive testing guide
- `docs/RPI-TEST-RESULTS.md` - Test results and known issues

### 🔍 Expected Issues

**arm32v6 (RPi Zero)**: Memory constraints, missing wheels, slow compilation
**arm32v7 (RPi 3)**: Occasional timeouts on Zero 2 W, memory limits
**arm64v8 (RPi 4/5)**: Generally excellent compatibility

### 📋 Prerequisites

- Docker with multi-architecture support (buildx)
- Docker Compose
- QEMU for cross-architecture emulation
- **SSH enabled on RPi devices** (for remote testing):
  ```bash
  sudo raspi-config  # Interface Options → SSH → Enable
  # OR: sudo systemctl enable --now ssh
  ```
- **SSH key distribution** (for remote testing):
  ```bash
  ssh-keygen -t rsa -b 4096 -C 'meshpi-testing' -f ~/.ssh/meshpi_test
  ssh-copy-id -i ~/.ssh/meshpi_test.pub pi@<rpi-ip>
  ```

### 📖 Documentation

- **Testing Guide**: `docs/RPI-TESTING.md`
- **Test Results**: `docs/RPI-TEST-RESULTS.md`
- **GitHub Actions**: Automatic testing on PR/push

### 🎯 Usage Examples

```bash
# Full Docker test suite
./run-rpi-tests.sh --clean

# Quick validation (Docker)
./run-rpi-tests.sh --quick --arch arm64v8

# CI-style testing (Docker)
./run-rpi-tests.sh --clean --sequential

# Test on real RPi hardware via SSH
./remote-rpi-test.sh pi@192.168.1.100

# Batch test multiple RPis
./batch-rpi-test.sh --devices "pi@rpi1.local pi@rpi2.local"

# Auto-diagnose and repair RPi issues
meshpi doctor pi@192.168.188.148

# Doctor with password authentication
meshpi doctor pi@rpi --password

# Doctor with custom SSH key
meshpi doctor pi@rpi --key ~/.ssh/custom_key

# Restart MeshPi service
meshpi restart pi@192.168.188.148

# Reboot the device
meshpi restart pi@192.168.188.148 --reboot

# Restart specific service
meshpi restart pi@192.168.188.148 --service host

# Interactive device list and management
meshpi ls

# Interactive device list with scanning
meshpi ls --scan

# Show all devices including offline
meshpi ls --all

# Comprehensive service management
./rpi-service-manager.sh pi@192.168.188.148

# Service management actions
./rpi-service-manager.sh pi@192.168.188.148 start
./rpi-service-manager.sh pi@192.168.188.148 stop
./rpi-service-manager.sh pi@192.168.188.148 restart
./rpi-service-manager.sh pi@192.168.188.148 status

# Start host service on remote RPi via SSH
meshpi host --ssh pi@192.168.188.148

# Enhanced device management with auto-detection
meshpi ls                                 # Interactive device list with auto-detection
meshpi monitor                            # Monitor all devices
meshpi monitor --continuous               # Continuous monitoring
meshpi monitor --group servers            # Monitor specific group

# SSH management
meshpi ssh shell pi@192.168.188.148      # Interactive SSH shell
meshpi ssh batch "uptime"                 # Batch command execution
meshpi ssh system-update                  # Update package lists
meshpi ssh system-upgrade                  # Upgrade packages

# Group management
meshpi group create servers                # Create device group
meshpi group add-device servers pi@rpi    # Add device to group
meshpi group status servers                # Group status check
meshpi group exec servers "uptime"         # Execute on group

# Local diagnostics only
meshpi doctor --local

# Comprehensive diagnostic script
./diagnose-rpi.sh pi@192.168.188.148

# Automated fix script
./fix-rpi-meshpi.sh pi@192.168.188.148

# Monitor repair status on RPi (run on RPi)
./monitor-repair.sh --follow

# Visual repair status display (run on RPi)
./show-repair-status.sh --continuous

# Generate report
./run-rpi-tests.sh && cat test-results/test-report-*.md
```

The testing suite provides comprehensive validation of MeshPi package installation across all major Raspberry Pi architectures, helping identify and resolve compatibility issues before deployment.
