# meshpi

**Zero-touch Raspberry Pi mesh configurator**

`meshpi` automates the initial setup of fresh Raspberry Pi devices on a local network.
Instead of manually typing WiFi credentials, SSH keys, and user passwords on each Pi,
you configure one HOST machine and all client Pis pull their config automatically — securely.

---

## How it works

```
HOST machine (PC or RPi)                CLIENT (fresh RPi, factory defaults)
─────────────────────────────           ──────────────────────────────────────
$ meshpi config                         $ meshpi scan
  ↳ Creates ~/.meshpi/config.env          ↳ Discovers host via mDNS
                                          ↳ Sends its RSA public key to host
$ meshpi host                           ↳ Host encrypts config with client key
  ↳ Starts FastAPI server               ↳ Client decrypts with its private key
  ↳ Advertises via mDNS                 ↳ Applies WiFi, SSH, user, locale, etc.
                                        ↳ Reboots
```

Config is encrypted **end-to-end** using asymmetric RSA + AES-GCM.
Nobody can intercept the WiFi password or SSH key in transit.

---

## Installation

```bash
pip install meshpi
```

Works on any Linux machine (host or RPi). Python 3.9+ required.

---

## Workflow: Network (recommended)

### 1. Set up the HOST

```bash
# First time — interactive wizard
meshpi config

# Start the host service (leave it running)
meshpi host
```

The wizard collects:
- Linux username & password for the Pi
- WiFi SSID & password
- SSH public key (auto-detected from `~/.ssh/id_rsa.pub`)
- Hostname prefix, timezone, locale, keyboard layout
- Optional post-install script URL

### 2. Configure each new CLIENT Pi

Boot the Pi with Raspberry Pi OS (factory defaults).
Connect it to the same network segment (Ethernet or via a hotspot).

```bash
pip install meshpi
meshpi scan
```

If **one host** is found, it connects automatically.
If **multiple hosts** are found, a selection menu appears.

The Pi will configure itself and reboot.

---

## Workflow: USB Pendrive (offline / air-gap)

For setups without network access or where the Pi cannot reach the host directly.

### Step 1 — Seed (on the CLIENT Pi)

Plug a USB stick into the Pi. The Pi writes its public key to it:

```bash
meshpi pendrive seed
```

### Step 2 — Export (on the HOST)

Plug the same USB into the HOST. The HOST encrypts the config with the Pi's public key:

```bash
meshpi pendrive export
```

### Step 3 — Apply (back on the CLIENT Pi)

Plug USB back into the Pi:

```bash
meshpi pendrive apply
```

---

## Commands

| Command | Role | Description |
|---------|------|-------------|
| `meshpi config` | HOST | Interactive config wizard → `~/.meshpi/config.env` |
| `meshpi host` | HOST | Start host service (mDNS + encrypted API) |
| `meshpi scan` | CLIENT | Discover host, download & apply config |
| `meshpi pendrive seed` | CLIENT | Write client public key to USB pendrive |
| `meshpi pendrive export` | HOST | Encrypt config onto USB pendrive |
| `meshpi pendrive apply` | CLIENT | Apply config from USB pendrive |
| `meshpi info` | any | Show local key/config state |

### Options

```
meshpi host --port 7422 --bind 0.0.0.0
meshpi scan --host 192.168.1.100 --port 7422 --dry-run
meshpi pendrive export --mount /media/user/USB --client-key /path/to/rpi_key_pub.pem
meshpi pendrive apply --mount /media/pi/USB --dry-run
meshpi config --update    # only prompt for fields not yet set
```

---

## Security

| Mechanism | Purpose |
|-----------|---------|
| RSA-2048 key pair per device | Identity — no shared secrets |
| AES-256-GCM session key | Encrypted payload, authenticated |
| Session key wrapped with recipient's RSA pub key | Only intended device can decrypt |
| `~/.meshpi/` directory mode `700` | Keys not world-readable |
| `config.env` mode `600` | Credentials not world-readable |
| mDNS service type `_meshpi._tcp` | Network-local discovery only |

The host never sends credentials in plaintext.
Even if someone captures the network traffic, they cannot read the config.

---

## Config fields (`config.env`)

| Field | Description |
|-------|-------------|
| `RPI_USER` | Linux username (default: `pi`) |
| `RPI_PASSWORD` | Linux password |
| `WIFI_SSID` | WiFi network name |
| `WIFI_PASSWORD` | WiFi password |
| `WIFI_COUNTRY` | WiFi country code (e.g. `PL`) |
| `RPI_HOSTNAME` | Hostname for the Pi |
| `SSH_PUBLIC_KEY` | Public key added to `authorized_keys` |
| `RPI_TIMEZONE` | e.g. `Europe/Warsaw` |
| `RPI_LOCALE` | e.g. `pl_PL.UTF-8` |
| `RPI_KEYBOARD` | e.g. `pl` |
| `POST_SCRIPT_URL` | Optional post-install script URL |

---

## Project structure

```
meshpi/
├── meshpi/
│   ├── __init__.py      Package metadata
│   ├── cli.py           CLI entry points (click)
│   ├── config.py        Interactive config wizard & .env loader
│   ├── crypto.py        RSA + AES-GCM encrypt/decrypt
│   ├── host.py          FastAPI host server + mDNS advertisement
│   ├── client.py        mDNS scanner + config downloader
│   ├── applier.py       Applies config to local system
│   └── pendrive.py      USB pendrive workflow
├── pyproject.toml
└── README.md
```

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
