<div align="center">

# 🔷 MeshPi

### Zero-Touch Raspberry Pi Fleet Management

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/v/meshpi?logo=pypi&logoColor=white&label=PyPI" alt="PyPI">
  <img src="https://img.shields.io/pypi/dm/meshpi?logo=pypi&logoColor=white&label=Downloads" alt="Downloads">
  <img src="https://img.shields.io/github/actions/workflow/status/pyfunc/meshpi/ci.yml?logo=github&label=CI" alt="CI Status">
  <img src="https://img.shields.io/codecov/c/github/pyfunc/meshpi?logo=codecov&logoColor=white" alt="Coverage">
  <img src="https://img.shields.io/badge/License-Apache%202.0-green?logo=apache" alt="License">
  <img src="https://img.shields.io/badge/code%20style-ruff-black?logo=ruff" alt="Code Style">
</p>

<p align="center">
  <strong>🚀 Configure WiFi, SSH, users, hardware peripherals, and manage devices through encrypted mesh networking</strong>
</p>

<p align="center">
  <a href="#-installation"><strong>Install</strong></a> •
  <a href="#-quick-start"><strong>Quick Start</strong></a> •
  <a href="#-features"><strong>Features</strong></a> •
  <a href="https://github.com/pyfunc/meshpi#readme"><strong>Docs</strong></a> •
  <a href="https://pypi.org/project/meshpi/"><strong>PyPI</strong></a>
</p>

---

</div>

## 📋 Overview

MeshPi eliminates the manual work of configuring Raspberry Pi devices from factory defaults. Whether deploying one device or an entire fleet, MeshPi handles:

- 📶 **WiFi credentials** - No monitor/keyboard needed
- 🔐 **SSH keys** - Secure remote access out of the box  
- 👤 **User accounts** - Create users, set passwords
- 🌍 **Locale & timezone** - Regional settings applied automatically
- 🔧 **Hardware peripherals** - 49+ profiles for displays, sensors, GPIO devices
- 📊 **Real-time monitoring** - CPU, memory, temperature, network status
- 🤖 **LLM-powered management** - Natural language fleet commands

All secured with **RSA-2048 + AES-256-GCM encryption**. No credentials ever travel in plaintext.

---

## ⚡ Quick Start

```bash
# Install
pip install meshpi

# On HOST machine (your PC or a dedicated RPi)
meshpi config    # Interactive configuration wizard
meshpi host      # Start the host service

# On each CLIENT Raspberry Pi (fresh from factory)
meshpi scan      # Auto-discovers host, configures itself, reboots
```

> 🎯 **Done!** Your Raspberry Pi is now configured and ready.

---

## 📱 Client Setup (Raspberry Pi)

### 🔧 Prerequisites Setup

Before running `meshpi scan` on your Raspberry Pi, follow these steps:

#### 1. **Connect to Internet**
```bash
# Connect to WiFi using desktop interface or command line
sudo raspi-config
# Navigate to Network Options → Wi-Fi → Enter SSID and password
```

#### 2. **Update System**
```bash
# Update package lists and upgrade system packages
sudo apt update && sudo apt upgrade -y

# Reboot after updates
sudo reboot
```

#### 3. **Install Python pip**
```bash
# Install pip if not already installed
sudo apt install python3-pip python3-venv -y

# Verify installation
pip3 --version
```

#### 4. **Install MeshPi**
```bash
# Install MeshPi package
pip3 install meshpi

# Or with LLM support for natural language commands
pip3 install "meshpi[llm]"
```

#### 5. **Run MeshPi Scan**
```bash
# Discover and connect to MeshPi host
meshpi scan
```

### 🚀 One-Liner Installation

For experienced users, here's the complete setup in one command:

```bash
sudo apt update && sudo apt upgrade -y && sudo apt install python3-pip -y && pip3 install meshpi && meshpi scan
```

### 📋 What Happens During Scan

When you run `meshpi scan`, the client will:

1. 🔍 **Discover Host** - Uses mDNS to find MeshPi hosts on your network
2. 🔑 **Key Exchange** - Generates RSA key pair and exchanges with host
3. 🔐 **Download Config** - Receives encrypted configuration
4. ⚙️ **Apply Settings** - Configures WiFi, SSH, users, locale
5. 🔄 **Reboot** - Restarts to apply all changes

### 🛠️ Troubleshooting

**No hosts found?**
- Ensure host machine is running `meshpi host`
- Check both devices are on the same network
- Verify firewall allows mDNS (port 5353)

**Installation issues?**
```bash
# Update pip to latest version
pip3 install --upgrade pip

# Install with specific version
pip3 install meshpi==0.1.14
```

---

## ✨ Features

### 🔐 Encrypted Zero-Touch Provisioning
- RSA-2048 key exchange + AES-256-GCM encryption
- No shared secrets, no cleartext on the wire
- mDNS discovery for automatic host detection

### 📡 Real-Time Fleet Management
- WebSocket-based persistent connections
- Push config updates instantly
- Execute shell commands remotely
- Apply hardware profiles on-the-fly
- Trigger reboots with delay

### 🔧 49+ Hardware Profiles with Group Management

| Category | Examples |
|----------|----------|
| 🖥️ Display | OLED SSD1306, TFT ILI9341, e-Paper, HDMI 4K |
| 🎛️ GPIO | Steppers (A4988), relays, servos (PCA9685), distance sensors |
| 🌡️ Sensors | BME280, DS18B20, MPU-6050, INA219 |
| 📷 Camera | RPi Camera v2/HQ, USB UVC, IR night vision |
| 🔊 Audio | HiFiBerry DAC+, I2S MEMS microphone |
| 📡 Networking | CAN, RS-485, LoRa, nRF24L01 |
| 🎩 HATs | Sense HAT, PiSugar UPS, RTC DS3231 |

```bash
# Quick interactive installation
meshpi hw quick-install --interactive

# Browse hardware catalog
meshpi hw catalog --category sensor --popular

# Apply to device groups
meshpi group create sensors
meshpi group add-device sensors pi@192.168.1.100
meshpi group hw-apply sensors sensor_bme280 sensor_ds18b20

# Remote management via SSH
meshpi ssh hw-apply --target pi@192.168.1.100 hat_sense
meshpi ssh hw-search oled --category display
```

**New Features:**
- 🎯 **Quick Install Wizard** - Interactive hardware selection and installation
- 📋 **Hardware Catalog** - Browse and filter 49+ profiles with tags
- 👥 **Device Groups** - Batch operations on multiple devices
- 🔗 **SSH Remote Management** - Control hardware on remote devices
- 🎨 **Custom Profiles** - Create and share your own hardware configurations

### 🤖 LLM-Powered Agent
```bash
pip install "meshpi[llm]"

meshpi agent
> show me all online devices
> what's wrong with rpi-kitchen?
> enable OLED display on rpi-bedroom
> push new WiFi password to all devices
```

Works with OpenAI, Anthropic, Ollama (local), Azure, Groq, and more.

### 📊 Full Diagnostics
```bash
meshpi diag
```
Collects CPU load, memory, temperature, GPIO states, I2C scan, USB devices, WiFi signal, services, logs, and more.

### 💾 USB Offline Workflow
For air-gapped environments:
```bash
meshpi pendrive seed     # Client: write public key to USB
meshpi pendrive export   # Host: encrypt config to USB
meshpi pendrive apply    # Client: apply config from USB
```

---

## 📦 Installation

```bash
# Core package
pip install meshpi

# With LLM agent support
pip install "meshpi[llm]"

# Development dependencies
pip install "meshpi[dev]"

# Everything
pip install "meshpi[all]"
```

**Requirements:** Python 3.9+, Linux (host), Raspberry Pi OS (client)

---

## 🏗️ Architecture

```
HOST (PC / RPi)                    CLIENT (fresh RPi)
─────────────────                  ─────────────────────
meshpi config                      meshpi scan
  → ~/.meshpi/config.env             → mDNS discovery
meshpi host                          → RSA key exchange
  → FastAPI REST API             ←   → Encrypted config
  → WebSocket /ws/{id}           →   → Apply & reboot
  → mDNS advertisement
  → Dashboard /dashboard
                           ↕
                    meshpi daemon
                      → Diagnostics push (60s)
                      → Real-time commands
```

---

## 🛠️ CLI Reference

| Command | Description |
|---------|-------------|
| `meshpi config` | Interactive configuration wizard |
| `meshpi host` | Start host service (FastAPI + mDNS) |
| `meshpi scan` | Discover hosts, download config |
| `meshpi daemon` | Persistent WebSocket connection |
| `meshpi diag` | Show device diagnostics |
| `meshpi hw list` | List hardware profiles |
| `meshpi hw apply <id>` | Apply hardware profile |
| `meshpi agent` | Launch LLM management agent |
| `meshpi info` | Show local keys/config state |
| `meshpi pendrive *` | USB offline workflow |

---

## 🔧 Environment Variables

MeshPi supports extensive configuration through environment variables. Copy `.env.example` to `.env` and customize.

### 🐳 Docker & Deployment

```bash
# Host service
MESHPI_PORT=7422
MESHPI_BIND=0.0.0.0

# Client configuration
MESHPI_HOST_IP=localhost
MESHPI_HOST_PORT=7422
MESHPI_DEVICE_ID=meshpi-client
```

### 🔧 Configuration (MESHPI_CFG_*)

Environment variables with `MESHPI_CFG_` prefix are automatically converted to `config.env`:

```bash
# WiFi
MESHPI_CFG_WIFI_SSID="MyNetwork"
MESHPI_CFG_WIFI_PASSWORD="MyPassword"
MESHPI_CFG_WIFI_COUNTRY="PL"

# SSH
MESHPI_CFG_RPI_USER="pi"
MESHPI_CFG_RPI_PASSWORD="raspberry"
MESHPI_CFG_SSH_ENABLE="yes"

# System
MESHPI_CFG_RPI_HOSTNAME="meshpi-node"
MESHPI_CFG_RPI_TIMEZONE="Europe/Warsaw"
```

### 🤖 LLM Agent

```bash
# LiteLLM configuration
LITELLM_MODEL=gpt-4o-mini
LITELLM_API_KEY=sk-...
LITELLM_API_BASE=https://api.openai.com/v1

# Alternative providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 📋 Complete Reference

See [`.env.example`](.env.example) for all available variables including:
- **Docker & Deployment**: Port, binding, client settings
- **Configuration**: SSH, WiFi, hostname, hardware interfaces
- **LLM Agent**: Multiple provider support
- **Testing**: Test devices, SSH keys, timeouts
- **Security**: Key paths, crypto settings
- **Monitoring**: Log levels, file paths

### 📚 **Standard Documentation**

For standardized documentation on device groups and hardware profiles, see:
- **[Standard Documentation](docs/STANDARD_DOCUMENTATION.md)** - Complete guide to groups (devices) and profiles (OS/drivers)
- **[Hardware Group Management](docs/HARDWARE-GROUP-MANAGEMENT.md)** - Advanced group operations
- **[SSH Hardware Management](docs/SSH-HARDWARE-MANAGEMENT.md)** - Remote hardware control

---

## 📁 Repository Organization

```
meshpi/
├── test/                    # Test scripts and utilities
│   ├── batch-rpi-test.sh    # Batch testing for multiple RPis
│   ├── test-doctor.sh       # Doctor functionality tests
│   ├── test-enhanced-cli.sh # CLI feature tests
│   ├── test-list.sh         # List functionality tests
│   ├── test-restart.sh      # Restart functionality tests
│   ├── test-ssh-host.sh     # SSH host tests
│   ├── test-ssh-scan-identify.sh # SSH scan tests
│   └── run-rpi-tests.sh     # Main Docker test runner
├── scripts/                 # Tooling and utility scripts
│   ├── diagnose-rpi.sh      # Comprehensive RPi diagnostics
│   ├── fix-rpi-meshpi.sh    # Automated common issue fixes
│   ├── monitor-repair.py    # Real-time repair status monitor (Python)
│   ├── project.py           # Code analysis tool (Python)
│   ├── remote-rpi-test.sh   # Remote RPi testing via SSH
│   ├── rpi-service-manager.sh # Service management
│   └── show-repair-status.py # Visual repair status display (Python)
├── meshpi/                  # Core Python package
├── docker/                  # Docker configurations
├── docs/                    # Documentation
└── tests/                   # Unit tests
```

---

## 🧪 Development

```bash
# Clone and setup
git clone https://github.com/pyfunc/meshpi.git
cd meshpi
make venv
make dev

# Run tests
make test

# Build package
make build

# Publish to PyPI
make publish
```

---

## 🐳 Docker

```bash
# Build image
docker build -t meshpi .

# Run host
docker run -p 7422:7422 meshpi

# Docker Compose
docker-compose up -d meshpi-host
```

---

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Tom Sapletta**  
📧 [tom@sapletta.com](mailto:tom@sapletta.com)  
🏢 [Softreck](https://softreck.dev) - Embedded systems, IoT automation

---

## 🔗 Links

- 📦 **PyPI:** [pypi.org/project/meshpi](https://pypi.org/project/meshpi/)
- 💻 **GitHub:** [github.com/pyfunc/meshpi](https://github.com/pyfunc/meshpi)
- 📖 **Documentation:** [github.com/pyfunc/meshpi#readme](https://github.com/pyfunc/meshpi#readme)
- 🐛 **Issues:** [github.com/pyfunc/meshpi/issues](https://github.com/pyfunc/meshpi/issues)
- 💝 **Sponsor:** [github.com/sponsors/pyfunc](https://github.com/sponsors/pyfunc)

---

<div align="center">

**[⬆ Back to Top](#-meshpi)**

Made with ❤️ for the Raspberry Pi community

</div>

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
