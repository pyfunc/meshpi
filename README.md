---
title: "MeshPi — Zero-Touch Raspberry Pi Fleet Management"
date: 2025-02-24
categories: [open-source, iot, raspberry-pi, python]
tags: [meshpi, rpi, automation, llm, gpio, hardware-profiles, fleet-management]
status: active
version: "0.2.0"
repo: https://github.com/pyfunc/meshpi
license: Apache-2.0
---

# MeshPi — Zero-Touch Raspberry Pi Fleet Management

<p align="center">
  <a href="https://pypi.org/project/meshpi/">
    <img src="https://img.shields.io/pypi/v/meshpi.svg" alt="PyPI version">
  </a>
  <a href="https://github.com/pyfunc/meshpi/actions">
    <img src="https://github.com/pyfunc/meshpi/workflows/CI/badge.svg" alt="CI Status">
  </a>
  <a href="https://codecov.io/gh/pyfunc/meshpi">
    <img src="https://codecov.io/gh/pyfunc/meshpi/branch/main/graph/badge.svg" alt="Code coverage">
  </a>
  <a href="https://github.com/pyfunc/meshpi/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License">
  </a>
  <a href="https://pypi.org/project/meshpi/">
    <img src="https://img.shields.io/pypi/pyversions/meshpi.svg" alt="Python versions">
  </a>
  <a href="https://github.com/pyfunc/meshpi/issues">
    <img src="https://img.shields.io/github/issues/pyfunc/meshpi.svg" alt="Issues">
  </a>
</p>

<p align="center">
  <strong>🚀 Zero-touch provisioning for Raspberry Pi fleets</strong><br>
  <em>Configure WiFi, SSH, users, hardware peripherals, and manage devices — all through encrypted mesh networking</em>
</p>

<p align="center">
  <a href="#installation"><strong>Installation</strong></a> •
  <a href="#quick-start"><strong>Quick Start</strong></a> •
  <a href="#features"><strong>Features</strong></a> •
  <a href="#documentation"><strong>Documentation</strong></a>
</p>

## What is MeshPi?

MeshPi is an open-source Python package that eliminates the manual work of configuring Raspberry Pi devices from factory defaults. Whether you are deploying one device or an entire fleet, MeshPi handles WiFi credentials, SSH keys, user accounts, locale settings, hardware peripherals, and ongoing management — all through a single CLI and an encrypted, zero-trust network protocol.

The project is built for embedded systems developers, IoT integrators, and hardware prototyping labs who regularly provision Raspberry Pi hardware and need a repeatable, secure, and automated workflow.

---

## ✨ Quick Start

```bash
# Install MeshPi
pip install meshpi

# On HOST machine (your PC or a dedicated RPi)
meshpi config    # One-time configuration wizard
meshpi host      # Start the host service

# On each CLIENT Raspberry Pi (fresh from factory)
meshpi scan      # Auto-discover host, configure itself, and reboot
```

> 🎯 **That's it!** Your Raspberry Pi is now configured with WiFi, SSH access, user accounts, and ready for hardware automation.

---

## 🏗️ Architecture

MeshPi uses a host–client model with end-to-end RSA+AES-GCM encryption. No credentials ever travel in plaintext.

```
HOST (PC / RPi)                     CLIENT (fresh RPi)
─────────────────                   ──────────────────────────
meshpi config                       meshpi scan
  → ~/.meshpi/config.env              → mDNS discovery
meshpi host                           → sends RSA public key
  → FastAPI + mDNS               ←  host encrypts config
  → WebSocket /ws/{id}           →  client decrypts & applies
  → Dashboard /dashboard              → WiFi, SSH, user, locale
                                      → reboots
                              ↕
                         meshpi daemon
                           → persistent WebSocket
                           → diagnostics push (60s)
                           → executes remote commands
```

The host also exposes a **real-time web dashboard** at `/dashboard` and a full **REST API with Swagger UI** at `/docs`.

---

## 🚀 Key Features

### 🔐 Encrypted Zero-Touch Provisioning
Configuration is encrypted with AES-256-GCM. The session key is wrapped with the client's RSA-2048 public key. No shared secrets. No cleartext on the wire.

### 📡 Real-Time Fleet Management
Once a device runs `meshpi daemon`, the host can push configuration changes, execute shell commands, apply hardware profiles, and trigger reboots — all through the WebSocket channel. The REST endpoint `POST /devices/{id}/push_config` delivers updates instantly without re-provisioning.

### 🔧 49+ Hardware Profiles
MeshPi ships with ready-to-apply profiles covering a wide range of peripherals:

| Category | Examples |
|----------|----------|
| **display** | OLED SSD1306 I2C, TFT ILI9341 SPI, e-Paper Waveshare, HDMI 1080p/4K, DSI Touchscreen |
| **gpio** | A4988/ARM69AK steppers, relay boards, PCA9685 servo controller, HC-SR04 distance sensor |
| **sensor** | BME280 (temp/humidity/pressure), DS18B20 (1-Wire), MPU-6050 (IMU), INA219 (power monitor) |
| **camera** | RPi Camera v2 & HQ, USB UVC, IR night vision |
| **audio** | HiFiBerry DAC+, I2S MEMS microphone |
| **networking** | CAN MCP2515, RS-485/Modbus, LoRa SX127x, nRF24L01 |
| **hat** | Sense HAT, PiSugar UPS, RTC DS3231, PoE+ |
| **storage** | USB boot, NFS, Samba |

Each profile installs apt packages, loads kernel modules, patches `/boot/config.txt`, and runs post-install commands — all in one step:

```bash
meshpi hw apply oled_ssd1306_i2c sensor_bme280 gpio_stepper_arm69ak
```

### 🤖 LLM-Powered Management Agent
The optional `meshpi[llm]` extra installs LiteLLM, enabling a conversational agent that understands natural language fleet management commands:

```
You: co jest nie tak z rpi-kuchnia?
Agent: [fetches diagnostics] CPU temperature is 84°C — above safe threshold.
       The throttled flag is set. Recommend improving airflow or adding a heatsink.
       Services: wpa_supplicant is inactive — WiFi may have dropped.
       Suggest: restart wpa_supplicant and check SSID config.

You: zrestartuj usługę WiFi na rpi-kuchnia
Agent: [pushes command] ✓ systemctl restart wpa_supplicant sent to rpi-kuchnia
```

Works with any LiteLLM-compatible provider: OpenAI, Anthropic, Ollama (local), Azure, Groq, and more.

### 💾 USB Pendrive Offline Workflow
For air-gapped environments or devices without network access at first boot:

```bash
# On CLIENT — seed USB with public key
meshpi pendrive seed

# On HOST — encrypt config onto USB  
meshpi pendrive export

# On CLIENT — apply and reboot
meshpi pendrive apply
```

### 📊 Full Device Diagnostics
`meshpi diag` collects CPU load, memory, temperature, GPIO pin states, I2C device scan, SPI status, USB devices, WiFi signal, running services, failed systemd units, recent error logs, top processes, and power/voltage status. All metrics are also pushed to the host automatically by the daemon.

### ⚙️ Systemd Integration
Both the host service and client daemon can be installed as systemd services with a single flag:

```bash
meshpi host --install        # installs meshpi-host.service
meshpi daemon --install      # installs meshpi-daemon.service
```

---

## 📦 Installation

```bash
pip install meshpi                    # core
pip install "meshpi[llm]"             # + LiteLLM NLP agent
```

Python 3.9+ required. Works on any Linux system (host) and Raspberry Pi OS (client).

---

## 🏛️ Project Structure

```
meshpi/
├── meshpi/
│   ├── cli.py          # Click CLI (config/host/scan/daemon/hw/agent/pendrive/info)
│   ├── config.py       # Interactive wizard → config.env
│   ├── crypto.py       # RSA-2048 + AES-256-GCM
│   ├── host.py         # FastAPI + WebSocket + mDNS + dashboard
│   ├── client.py       # mDNS scanner + WS daemon + config applier
│   ├── applier.py      # System configurator (user/WiFi/SSH/locale)
│   ├── diagnostics.py  # Full RPi system diagnostics collector
│   ├── registry.py     # Persistent device registry (JSON)
│   ├── llm_agent.py    # LiteLLM function-calling agent
│   ├── systemd.py      # Systemd service installer
│   ├── pendrive.py     # USB offline workflow
│   └── hardware/
│       ├── profiles.py # 49 hardware profiles
│       └── applier.py  # Profile applicator (apt/modprobe/config.txt)
├── tests/
│   └── test_meshpi.py  # 59 tests (pytest) — 100% passing
├── pyproject.toml
├── LICENSE             # Apache 2.0
└── README.md
```

---

## 🧪 Test Coverage

The v0.2.0 release ships with **59 automated tests** covering:

- Cryptographic primitives (RSA keygen, encrypt/decrypt roundtrip, cross-key isolation)
- Config file parsing and .env writing
- Device registry CRUD operations
- All 49 hardware profile definitions and filters
- System diagnostics collection
- All REST API endpoints (TestClient, no real network needed)
- CLI commands and option handling

```bash
pytest tests/ -v   # 59 passed in ~8s
```

---

## 🐳 Docker Support

MeshPi includes Docker support for testing and deployment:

```bash
# Build the image
docker build -t meshpi .

# Run host service
docker run -p 7422:7422 meshpi meshpi host --bind 0.0.0.0

# Or use docker-compose for full test environment
docker-compose up -d meshpi-host
docker-compose up meshpi-client  # runs scan in dry-run mode
```

---

## 🗺️ Roadmap

The following features are planned for upcoming releases:

- **v0.3** — Web dashboard configuration editor (edit config.env from browser), device grouping and bulk commands
- **v0.4** — Prometheus/Grafana metrics export, webhook notifications on device events
- **v0.5** — OTA update management (apt upgrade via host), config versioning with rollback
- **v1.0** — Stable REST API, PyPI publish, Docker host image

---

## 🔗 Links

- **Repository:** [github.com/pyfunc/meshpi](https://github.com/pyfunc/meshpi)
- **License:** Apache 2.0
- **Author:** [Softreck](https://softreck.dev) — embedded systems, IoT automation, hardware prototyping
- **Related projects:** [Portigen.com](https://portigen.com) (portable power stations), [Prototypowanie.pl](https://prototypowanie.pl) (PCB prototyping)

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## 👤 Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
