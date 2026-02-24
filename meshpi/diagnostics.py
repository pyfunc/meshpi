"""
meshpi.diagnostics
==================
Collects comprehensive Raspberry Pi diagnostics and health metrics.

Returns structured dict consumed by:
  - meshpi host manager (WebSocket push)
  - LLM agent for intelligent repair suggestions
  - CLI display
"""

from __future__ import annotations

import glob
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any


def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def collect() -> dict[str, Any]:
    """Collect full system diagnostics. Returns serialisable dict."""
    return {
        "timestamp": time.time(),
        "system":    _system_info(),
        "cpu":       _cpu_info(),
        "memory":    _memory_info(),
        "disk":      _disk_info(),
        "network":   _network_info(),
        "gpio":      _gpio_info(),
        "i2c":       _i2c_info(),
        "spi":       _spi_info(),
        "usb":       _usb_info(),
        "services":  _services_info(),
        "temperature": _temperature_info(),
        "power":     _power_info(),
        "logs":      _recent_logs(),
        "hardware":  _hardware_info(),
        "wifi":      _wifi_info(),
        "processes": _top_processes(),
    }


# ─────────────────────────────────────────────────────────────────────────────

def _system_info() -> dict:
    return {
        "hostname":    socket.gethostname(),
        "platform":    platform.platform(),
        "machine":     platform.machine(),
        "python":      platform.python_version(),
        "uptime_secs": _uptime(),
        "rpi_model":   _rpi_model(),
        "rpi_revision": _run("cat /proc/cpuinfo | grep Revision | awk '{print $3}'"),
        "serial":      _run("cat /proc/cpuinfo | grep Serial | awk '{print $3}'"),
        "os_release":  _run("lsb_release -d -s 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2"),
        "kernel":      _run("uname -r"),
        "firmware":    _run("vcgencmd version 2>/dev/null || echo 'n/a'"),
    }


def _uptime() -> float:
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except Exception:
        return 0.0


def _rpi_model() -> str:
    try:
        model = Path("/proc/device-tree/model").read_bytes().rstrip(b"\x00").decode()
        return model
    except Exception:
        return _run("cat /proc/cpuinfo | grep Model | cut -d: -f2").strip()


def _cpu_info() -> dict:
    load = os.getloadavg()
    freq = _run("vcgencmd measure_clock arm 2>/dev/null | cut -d= -f2") or _run("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    cpu_percent = _run("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
    return {
        "count":          os.cpu_count(),
        "load_1m":        round(load[0], 2),
        "load_5m":        round(load[1], 2),
        "load_15m":       round(load[2], 2),
        "freq_hz":        int(freq) if freq.isdigit() else None,
        "usage_percent":  float(cpu_percent) if cpu_percent else None,
        "governor":       _run("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null"),
        "throttled":      _run("vcgencmd get_throttled 2>/dev/null"),
    }


def _memory_info() -> dict:
    mem = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                val = int(parts[1])
                mem[key] = val
    except Exception:
        pass

    total = mem.get("MemTotal", 0)
    available = mem.get("MemAvailable", 0)
    used = total - available
    swap_total = mem.get("SwapTotal", 0)
    swap_free = mem.get("SwapFree", 0)

    return {
        "total_kb":     total,
        "used_kb":      used,
        "available_kb": available,
        "used_percent": round(used / total * 100, 1) if total else 0,
        "swap_total_kb": swap_total,
        "swap_used_kb":  swap_total - swap_free,
        "gpu_mem_mb":    _run("vcgencmd get_mem gpu 2>/dev/null | sed 's/gpu=//;s/M//'"),
    }


def _disk_info() -> list[dict]:
    results = []
    try:
        lines = _run("df -h --output=source,size,used,avail,pcent,target").splitlines()[1:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 6 and not parts[0].startswith("tmpfs"):
                results.append({
                    "source":     parts[0],
                    "size":       parts[1],
                    "used":       parts[2],
                    "avail":      parts[3],
                    "use_percent": parts[4],
                    "mountpoint": parts[5],
                })
    except Exception:
        pass
    return results


def _network_info() -> dict:
    interfaces = {}
    try:
        out = _run("ip -j addr 2>/dev/null")
        if out:
            for iface in json.loads(out):
                name = iface.get("ifname", "")
                addrs = [a["local"] for a in iface.get("addr_info", []) if "local" in a]
                interfaces[name] = {
                    "addresses": addrs,
                    "state":     iface.get("operstate", "UNKNOWN"),
                    "flags":     iface.get("flags", []),
                }
    except Exception:
        pass

    return {
        "interfaces": interfaces,
        "hostname":   socket.gethostname(),
        "dns":        _run("cat /etc/resolv.conf | grep nameserver | awk '{print $2}' | head -3"),
        "gateway":    _run("ip route | grep default | awk '{print $3}' | head -1"),
        "ping_ok":    _ping_check("8.8.8.8"),
    }


def _ping_check(host: str) -> bool:
    import shutil
    ping_bin = shutil.which("ping")
    if not ping_bin:
        return False
    r = subprocess.run([ping_bin, "-c", "1", "-W", "2", host], capture_output=True)
    return r.returncode == 0


def _gpio_info() -> dict:
    pins = {}
    try:
        out = _run("raspi-gpio get 2>/dev/null | head -30")
        for line in out.splitlines():
            m = re.match(r"GPIO (\d+): level=(\d) func=(\S+)", line)
            if m:
                pins[int(m.group(1))] = {
                    "level": int(m.group(2)),
                    "func":  m.group(3),
                }
    except Exception:
        pass
    return {"pins": pins, "available": bool(pins)}


def _i2c_info() -> dict:
    devices: dict[str, list[str]] = {}
    for bus in glob.glob("/dev/i2c-*"):
        bus_num = bus.replace("/dev/i2c-", "")
        out = _run(f"i2cdetect -y {bus_num} 2>/dev/null")
        addrs = re.findall(r"\b([0-9a-f]{2})\b", out.lower())
        addrs = [a for a in addrs if a not in ("--", "uu") and a.isalnum() and int(a, 16) >= 3]
        if addrs:
            devices[bus] = sorted(set(addrs))
    return {"buses": list(glob.glob("/dev/i2c-*")), "devices": devices}


def _spi_info() -> dict:
    return {
        "devices": glob.glob("/dev/spidev*"),
        "enabled": bool(glob.glob("/dev/spidev*")),
    }


def _usb_info() -> list[dict]:
    devices = []
    try:
        out = _run("lsusb 2>/dev/null")
        for line in out.splitlines():
            m = re.match(r"Bus (\d+) Device (\d+): ID ([\da-f:]+) (.+)", line)
            if m:
                devices.append({
                    "bus":    m.group(1),
                    "device": m.group(2),
                    "id":     m.group(3),
                    "name":   m.group(4),
                })
    except Exception:
        pass
    return devices


def _services_info() -> dict:
    important = [
        "ssh", "NetworkManager", "wpa_supplicant", "dhcpcd",
        "avahi-daemon", "pigpiod", "docker", "mosquitto",
    ]
    statuses = {}
    for svc in important:
        rc = subprocess.run(
            ["systemctl", "is-active", svc],
            capture_output=True, text=True
        ).returncode
        statuses[svc] = "active" if rc == 0 else "inactive"

    # Failed units
    failed = _run("systemctl --failed --no-legend 2>/dev/null | awk '{print $1}' | head -10")
    return {"statuses": statuses, "failed_units": failed.splitlines() if failed else []}


def _temperature_info() -> dict:
    temps: dict[str, float] = {}

    # GPU / CPU via vcgencmd
    gpu_temp = _run("vcgencmd measure_temp 2>/dev/null | sed 's/temp=//;s/.C//'")
    if gpu_temp:
        try:
            temps["cpu_gpu"] = float(gpu_temp)
        except ValueError:
            pass

    # thermal zones
    for zone in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        zone_id = re.search(r"thermal_zone(\d+)", zone)
        try:
            temp_c = int(Path(zone).read_text().strip()) / 1000
            temps[f"zone_{zone_id.group(1) if zone_id else 'x'}"] = temp_c
        except Exception:
            pass

    return temps


def _power_info() -> dict:
    throttled_raw = _run("vcgencmd get_throttled 2>/dev/null")
    throttled_hex = 0
    if "0x" in throttled_raw:
        try:
            throttled_hex = int(throttled_raw.split("=")[1], 16)
        except Exception:
            pass

    voltage = _run("vcgencmd measure_volts core 2>/dev/null | sed 's/volt=//;s/V//'")

    return {
        "throttled_raw":   throttled_raw,
        "under_voltage":   bool(throttled_hex & 0x1),
        "freq_capped":     bool(throttled_hex & 0x2),
        "currently_throttled": bool(throttled_hex & 0x4),
        "soft_temp_limit": bool(throttled_hex & 0x8),
        "core_voltage_v":  float(voltage) if voltage else None,
    }


def _recent_logs() -> list[str]:
    """Last 20 journal error/warning lines."""
    out = _run("journalctl -p err..warning -n 20 --no-pager --output=short 2>/dev/null")
    return out.splitlines() if out else []


def _hardware_info() -> dict:
    return {
        "camera":    bool(_run("vcgencmd get_camera 2>/dev/null | grep 'detected=1'")),
        "bluetooth": bool(glob.glob("/dev/rfcomm*") or Path("/proc/net/rfcomm").exists()),
        "modules_loaded": _run("lsmod | awk 'NR>1{print $1}'").splitlines(),
    }


def _wifi_info() -> dict:
    ssid = _run("iwgetid -r 2>/dev/null")
    quality = _run("iwconfig wlan0 2>/dev/null | grep Quality | awk '{print $2}'")
    signal = _run("iwconfig wlan0 2>/dev/null | grep Signal | sed 's/.*Signal level=//'")
    return {
        "ssid":    ssid,
        "quality": quality,
        "signal":  signal,
        "mode":    _run("iwconfig wlan0 2>/dev/null | grep Mode | awk '{print $1}'"),
    }


def _top_processes() -> list[dict]:
    """Top 10 processes by CPU."""
    out = _run("ps aux --sort=-%cpu | head -11 | tail -10")
    procs = []
    for line in out.splitlines():
        parts = line.split(None, 10)
        if len(parts) >= 11:
            procs.append({
                "user":    parts[0],
                "pid":     parts[1],
                "cpu":     parts[2],
                "mem":     parts[3],
                "command": parts[10][:80],
            })
    return procs


def format_summary(diag: dict) -> str:
    """Return a compact text summary suitable for LLM context."""
    s = diag.get("system", {})
    cpu = diag.get("cpu", {})
    mem = diag.get("memory", {})
    temp = diag.get("temperature", {})
    pwr = diag.get("power", {})
    svc = diag.get("services", {})
    net = diag.get("network", {})
    wifi = diag.get("wifi", {})

    lines = [
        f"Host: {s.get('hostname')} | Model: {s.get('rpi_model', 'unknown')}",
        f"OS: {s.get('os_release', '')} | Kernel: {s.get('kernel', '')}",
        f"Uptime: {int(s.get('uptime_secs', 0) / 3600)}h {int((s.get('uptime_secs', 0) % 3600) / 60)}m",
        f"CPU: load={cpu.get('load_1m')}/{cpu.get('load_5m')}/{cpu.get('load_15m')} | "
        f"freq={cpu.get('freq_hz', 'n/a')} Hz | throttled={pwr.get('currently_throttled')}",
        f"Memory: {mem.get('used_percent')}% used ({mem.get('used_kb', 0)//1024}MB / {mem.get('total_kb', 0)//1024}MB)",
        f"Temp: {temp.get('cpu_gpu', temp.get('zone_0', 'n/a'))}°C | Under-voltage: {pwr.get('under_voltage')}",
        f"WiFi: SSID={wifi.get('ssid', 'disconnected')} | Internet: {'OK' if net.get('ping_ok') else 'FAIL'}",
        f"Services failed: {svc.get('failed_units', [])}",
    ]
    if diag.get("logs"):
        lines.append(f"Recent errors (last 5):")
        for l in diag["logs"][:5]:
            lines.append(f"  {l}")
    return "\n".join(lines)
