# RPi Architecture Testing Guide

This guide explains how to test MeshPi package installation across different Raspberry Pi architectures using Docker.

## Overview

The testing suite validates MeshPi installation and functionality on:
- **arm32v6** - Raspberry Pi Zero, Zero W
- **arm32v7** - Raspberry Pi 2, 3, Zero 2 W  
- **arm64v8** - Raspberry Pi 4, 5

## Quick Start

### Prerequisites

Before running tests, ensure SSH is properly configured on Raspberry Pi devices for remote testing:

#### SSH Configuration on Raspberry Pi

**Method 1: Using raspi-config**
```bash
sudo raspi-config
# Navigate to Interface Options → SSH → Enable, then reboot
sudo reboot
```

**Method 2: Using systemctl**
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

**Method 3: One-liner**
```bash
sudo systemctl enable --now ssh
```

**Method 4: Manual SSH key setup**
```bash
# Create .ssh directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Generate SSH key if not exists
ssh-keygen -t rsa -b 4096 -C "meshpi-testing" -f ~/.ssh/meshpi_test

# Copy public key to RPi
ssh-copy-id -i ~/.ssh/meshpi_test.pub pi@<rpi-ip-address>
```

#### SSH Testing Verification
```bash
# Test SSH connection
ssh -i ~/.ssh/meshpi_test pi@<rpi-ip-address> "python3 --version"

# Test remote Python execution
ssh -i ~/.ssh/meshpi_test pi@<rpi-ip-address> "pip3 list | grep meshpi"
```

### Local Testing

```bash
# Test all architectures
./run-rpi-tests.sh

# Test specific architecture
./run-rpi-tests.sh --arch arm32v6

# Quick test (skip builds)
./run-rpi-tests.sh --quick

# Clean build
./run-rpi-tests.sh --clean
```

### CI/CD Testing

The GitHub Actions workflow automatically runs tests on:
- Push to main/develop branches
- Pull requests
- Manual workflow dispatch

## Architecture Compatibility

### arm32v6 (RPi Zero/Zero W)
- **Python:** 3.9-3.11 recommended
- **Memory:** 512MB RAM
- **Known Issues:**
  - Limited memory may cause installation timeouts
  - Some compiled packages may not have arm32v6 wheels
  - Slower installation times (5-10 minutes)

### arm32v7 (RPi 2/3/Zero 2 W)
- **Python:** 3.9-3.12 supported
- **Memory:** 1GB RAM (RPi 2), 1GB RAM (RPi 3), 512MB RAM (Zero 2 W)
- **Known Issues:**
  - Generally stable architecture
  - Most packages have compatible wheels
  - Installation times: 2-5 minutes

### arm64v8 (RPi 4/5)
- **Python:** 3.9-3.13 supported
- **Memory:** 2GB-8GB RAM
- **Known Issues:**
  - Most compatible architecture
  - Fastest installation times (1-3 minutes)
  - All packages typically available

## Test Components

### 1. Installation Tests
- **PyPI Installation:** `pip install meshpi`
- **Source Installation:** `pip install -e .`
- **Optional Dependencies:** `pip install meshpi[all]`

### 2. Import Tests
- Core module imports
- Optional dependency imports
- CLI functionality tests

### 3. System Tests
- Python version compatibility
- pip version compatibility
- System resource checks

## Test Results

### Expected Results

| Architecture | Success Rate | Typical Issues |
|--------------|--------------|----------------|
| arm64v8 | 95-100% | Rare dependency conflicts |
| arm32v7 | 90-95% | Memory constraints on Zero 2 W |
| arm32v6 | 80-90% | Missing wheels, timeouts |

### Common Issues and Solutions

#### Missing Wheels
```
ERROR: Could not find a version that satisfies the requirement
```

**Solution:** Use source installation or build from source
```bash
pip install --no-binary :all: meshpi
```

#### Memory Issues
```
MemoryError: Killed
```

**Solution:** Increase swap space or use minimal installation
```bash
pip install meshpi --no-deps
pip install meshpi[core]
```

#### Timeout Issues
```
Timeout during installation
```

**Solution:** Increase timeout and use mirrors
```bash
pip install --timeout 600 --index-url https://pypi.org/simple/ meshpi
```

## Manual Testing

### Docker Commands

```bash
# Build specific architecture
docker-compose -f docker-compose.test-rpi.yml build meshpi-test-arm32v6

# Run tests
docker-compose -f docker-compose.test-rpi.yml run --rm meshpi-test-arm32v6

# View logs
docker-compose -f docker-compose.test-rpi.yml logs meshpi-test-arm32v6
```

### Direct Container Testing

```bash
# Test arm32v6 manually
docker run --rm --platform linux/arm/v6 \
  meshpi-test-arm32v6:latest \
  python test-installation.py --arch arm32v6 --model zero --verbose
```

## Troubleshooting

### Build Issues

**QEMU not available:**
```bash
# Install QEMU
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

**Build fails with platform errors:**
```bash
# Check available platforms
docker buildx inspect --bootstrap

# Enable multi-platform builds
docker buildx create --use --name multiarch
docker buildx inspect --bootstrap
```

### Runtime Issues

**Container won't start:**
```bash
# Check container logs
docker logs meshpi-test-arm32v6

# Check if image exists
docker images | grep meshpi-test
```

**Tests fail with import errors:**
```bash
# Check Python version in container
docker run --rm meshpi-test-arm32v6 python --version

# Check installed packages
docker run --rm meshpi-test-arm32v6 pip list
```

## Remote SSH Testing

For testing on actual Raspberry Pi hardware via SSH:

### SSH Test Script

Create a remote test script for direct RPi testing:

```bash
#!/bin/bash
# remote-rpi-test.sh - Test MeshPi on real RPi via SSH

RPI_IP="${1:-pi@raspberrypi.local}"
SSH_KEY="${2:-~/.ssh/meshpi_test}"

echo "Testing MeshPi on real RPi: $RPI_IP"

# Test connection
ssh -i "$SSH_KEY" "$RPI_IP" "echo 'SSH connection OK'"

# Test Python environment
ssh -i "$SSH_KEY" "$RPI_IP" "python3 --version && pip3 --version"

# Test MeshPi installation
ssh -i "$SSH_KEY" "$RPI_IP" "
pip3 uninstall -y meshpi 2>/dev/null || true
pip3 install meshpi
python3 -c 'import meshpi; print(f\"MeshPi version: {meshpi.__version__}\")'
"

# Test CLI functionality
ssh -i "$SSH_KEY" "$RPI_IP" "meshpi --help"

echo "Remote testing completed"
```

### Batch SSH Testing

Test multiple RPi devices simultaneously:

```bash
#!/bin/bash
# batch-rpi-test.sh - Test multiple RPis

RPI_DEVICES=(
    "pi@rpi-zero.local"
    "pi@rpi3.local" 
    "pi@rpi4.local"
)

SSH_KEY="$HOME/.ssh/meshpi_test"

for device in "${RPI_DEVICES[@]}"; do
    echo "Testing $device..."
    ssh -i "$SSH_KEY" "$device" "
        echo '=== $device ==='
        python3 --version
        pip3 install meshpi --quiet
        python3 -c 'import meshpi; print(\"MeshPi OK\")'
    " &
done

wait
echo "All devices tested"
```

### SSH Troubleshooting

**Connection refused:**
```bash
# Check if SSH is running on RPi
ssh pi@<rpi-ip> "sudo systemctl status ssh"

# Start SSH service
ssh pi@<rpi-ip> "sudo systemctl start ssh"
```

**Authentication failed:**
```bash
# Reset SSH keys
ssh-keygen -R <rpi-ip-address>

# Copy key again
ssh-copy-id -i ~/.ssh/meshpi_test.pub pi@<rpi-ip>
```

**Permission denied:**
```bash
# Check file permissions
chmod 600 ~/.ssh/meshpi_test
chmod 644 ~/.ssh/meshpi_test.pub
```

## Performance Benchmarks

### Installation Times (approximate)

| Architecture | PyPI Install | Source Install | With Extras |
|--------------|--------------|----------------|-------------|
| arm64v8 | 1-2 min | 2-3 min | 3-5 min |
| arm32v7 | 2-4 min | 3-5 min | 5-8 min |
| arm32v6 | 5-10 min | 8-12 min | 10-15 min |

### Memory Usage

| Architecture | Peak Memory | Base Memory |
|--------------|-------------|-------------|
| arm64v8 | 200-400MB | 50-100MB |
| arm32v7 | 150-300MB | 40-80MB |
| arm32v6 | 100-200MB | 30-60MB |

## CI/CD Integration

### GitHub Actions
- **Trigger:** Push, PR, manual
- **Parallel:** Yes (3 architectures)
- **Timeout:** 30 minutes per job
- **Artifacts:** Test results, logs, reports

### Local CI
```bash
# Run CI-like tests locally
./run-rpi-tests.sh --clean --sequential

# Generate report
./run-rpi-tests.sh && cat test-results/test-report-*.md
```

## Contributing

When adding new dependencies or features:

1. **Test on all architectures** before merging
2. **Update documentation** with known issues
3. **Add architecture-specific checks** if needed
4. **Update benchmarks** with performance data

### Adding New Tests

```python
# In docker/test-rpi/test-installation.py
def test_new_feature(self) -> Dict:
    """Test new feature across architectures"""
    test_result = {
        "name": "new_feature_test",
        "description": "Test new feature",
        "passed": False,
        "details": {}
    }
    
    try:
        # Test implementation
        test_result["passed"] = True
    except Exception as e:
        test_result["details"]["error"] = str(e)
    
    self.results["tests"].append(test_result)
    return test_result
```

## Support

For issues with RPi architecture testing:

1. **Check logs:** `docker logs <container>`
2. **Verify environment:** `docker run --rm meshpi-test-arm32v6 python --version`
3. **Test manually:** Use direct Docker commands
4. **Report issues:** Include architecture, logs, and system info

## References

- [Docker Multi-Architecture Builds](https://docs.docker.com/buildx/working-with-images/)
- [RPi Hardware Specifications](https://www.raspberrypi.org/documentation/)
- [Python ARM Compatibility](https://www.python.org/downloads/)
- [PyPI Wheel Availability](https://pypi.org/project/meshpi/#files)
