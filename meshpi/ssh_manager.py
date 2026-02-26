"""
meshpi.ssh_manager
==================
SSH device management for Raspberry Pi fleet.

Provides comprehensive SSH-based management capabilities:
- Device discovery and scanning
- Batch command execution
- File transfer operations
- Service management
- System updates
- Configuration deployment
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import paramiko
import psutil
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.text import Text

console = Console()


class SSHDevice:
    """Represents a managed SSH device."""
    
    def __init__(self, host: str, user: str = "pi", port: int = 22, 
                 name: Optional[str] = None, tags: Optional[List[str]] = None,
                 meta: Optional[Dict[str, Any]] = None):
        self.host = host
        self.user = user
        self.port = port
        self.name = name or host
        self.tags = tags or []
        self.meta: Dict[str, Any] = meta or {}
        self.client: Optional[paramiko.SSHClient] = None
        self._connected = False
        self._info: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return f"{self.user}@{self.host}:{self.port}"
    
    def __repr__(self) -> str:
        return f"SSHDevice(host='{self.host}', user='{self.user}', port={self.port})"


class SSHManager:
    """Manages multiple SSH devices with batch operations."""
    
    def __init__(self):
        self.devices: List[SSHDevice] = []
        self.default_key_path = Path.home() / ".ssh" / "id_rsa"

    @staticmethod
    def detect_primary_network() -> tuple[Optional[str], Optional[str]]:
        """Return (cidr, gateway_ip) for the primary (routed) IPv4 network.

        Prefers the interface used by the default route and ignores common
        virtual/container interfaces.
        """
        exclude_prefixes = (
            "lo",
            "docker",
            "br-",
            "veth",
            "cni",
            "flannel",
            "virbr",
            "podman",
            "zt",
            "tailscale",
            "wg",
        )

        try:
            gateway_ip: Optional[str] = None
            iface: Optional[str] = None

            with open("/proc/net/route", "r") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) < 8:
                        continue
                    ifname, dest_hex, gateway_hex, flags_hex, _, _, _, mask_hex = parts[:8]
                    if dest_hex != "00000000" or mask_hex != "00000000":
                        continue
                    if any(ifname.startswith(p) for p in exclude_prefixes):
                        continue
                    try:
                        flags = int(flags_hex, 16)
                        if flags & 0x2 == 0:
                            continue
                    except Exception:
                        continue

                    iface = ifname
                    try:
                        gw_int = int(gateway_hex, 16)
                        gateway_ip = ".".join(str((gw_int >> (8 * i)) & 0xFF) for i in range(4))
                    except Exception:
                        gateway_ip = None
                    break

            if not iface:
                return None, None

            addrs = psutil.net_if_addrs().get(iface, [])
            ipv4 = next((a for a in addrs if getattr(a, "family", None) and int(a.family) == 2), None)
            if not ipv4 or not ipv4.address or not ipv4.netmask:
                return None, gateway_ip

            import ipaddress

            network = ipaddress.IPv4Interface(f"{ipv4.address}/{ipv4.netmask}").network
            return str(network), gateway_ip
        except Exception:
            return None, None

    @staticmethod
    def ip_neighbors() -> Dict[str, str]:
        """Return mapping ip -> mac from the local neighbor table (ip neigh)."""
        try:
            result = subprocess.run(
                ["ip", "neigh"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode != 0:
                return {}
            mapping: Dict[str, str] = {}
            for line in result.stdout.splitlines():
                # Example: 192.168.188.1 dev wlp90s0 lladdr 68:1d:ef:30:74:48 REACHABLE
                parts = line.split()
                if not parts:
                    continue
                ip = parts[0]
                if "lladdr" in parts:
                    idx = parts.index("lladdr")
                    if idx + 1 < len(parts):
                        mac = parts[idx + 1]
                        if ":" in mac:
                            mapping[ip] = mac.lower()
            return mapping
        except Exception:
            return {}

    @staticmethod
    def mac_vendor(mac: Optional[str]) -> Optional[str]:
        if not mac:
            return None
        try:
            from manuf import manuf

            parser = manuf.MacParser()
            return parser.get_manuf(mac) or None
        except Exception:
            return None

    def add_device(self, device: SSHDevice) -> None:
        """Add a device to management."""
        if device not in self.devices:
            self.devices.append(device)
            console.print(f"[green]✓[/green] Added device: [bold]{device}[/bold]")

    def remove_device(self, device: SSHDevice) -> None:
        """Remove a device from management."""
        if device in self.devices:
            self.devices.remove(device)
            console.print(f"[yellow]✓[/yellow] Removed device: [bold]{device}[/bold]")

    def scan_network(self, network: str = "192.168.1.0/24", 
                     user: str = "pi", port: int = 22,
                     timeout: int = 5) -> List[SSHDevice]:
        """Scan network for SSH-enabled devices."""
        console.print(f"[cyan]→[/cyan] Scanning network [bold]{network}[/bold] for SSH devices...")
        
        # Use nmap if available, otherwise simple port scan
        try:
            result = subprocess.run(
                ["nmap", "-p", str(port), "--open", network],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return self._parse_nmap_output(result.stdout, user, port)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to simple port scan
        return self._simple_port_scan(network, port, user, timeout)

    def _parse_nmap_output(self, output: str, user: str, port: int) -> List[SSHDevice]:
        """Parse nmap output to find open SSH ports."""
        devices = []
        lines = output.split('\n')
        for line in lines:
            if "Nmap scan report for" in line:
                parts = line.split()
                for part in parts:
                    if '(' in part and ')' in part:
                        ip = part.strip('()')
                        devices.append(SSHDevice(ip, user, port))
                        break
        return devices

    def _simple_port_scan(self, network: str, port: int, user: str, timeout: int) -> List[SSHDevice]:
        """Simple port scan using Python sockets."""
        import socket
        from ipaddress import ip_network
        
        devices = []
        net = ip_network(network, strict=False)
        
        with Progress() as progress:
            task = progress.add_task("Scanning IPs...", total=len(net))
            
            for ip in net:
                progress.update(task, advance=1)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                try:
                    result = sock.connect_ex((str(ip), port))
                    if result == 0:
                        devices.append(SSHDevice(str(ip), user, port))
                except Exception:
                    pass
                finally:
                    sock.close()
        
        return devices

    def connect_to_device(self, device: SSHDevice, 
                         password: Optional[str] = None,
                         key_path: Optional[str] = None) -> bool:
        """Connect to a specific device."""
        try:
            device.client = paramiko.SSHClient()
            device.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": device.host,
                "port": device.port,
                "username": device.user,
                "timeout": 10,
            }
            
            if key_path:
                connect_kwargs["key_filename"] = key_path
            elif password:
                connect_kwargs["password"] = password
            elif self.default_key_path.exists():
                connect_kwargs["key_filename"] = str(self.default_key_path)
            
            device.client.connect(**connect_kwargs)
            device._connected = True
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Failed to connect to {device}: {e}[/red]")
            return False

    def disconnect_device(self, device: SSHDevice) -> None:
        """Disconnect from a device."""
        if device.client:
            device.client.close()
            device._connected = False

    def get_device_info(self, device: SSHDevice) -> Dict[str, Any]:
        """Collect device information."""
        if not device._connected:
            return {}
        
        info = {}
        commands = {
            "hostname": "hostname",
            "uname": "uname -a",
            "uptime": "uptime",
            "cpu_temp": "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000 \"°C\"}' || echo 'N/A'",
            "memory": "free -h | head -2",
            "disk": "df -h / | tail -1",
            "ip": "hostname -I 2>/dev/null || ip route get 8.8.8.8 | awk '{print $7}'",
            "meshpi_version": "pip show meshpi 2>/dev/null | grep Version || echo 'Not installed'",
        }
        
        for key, cmd in commands.items():
            try:
                stdin, stdout, stderr = device.client.exec_command(cmd)
                info[key] = stdout.read().decode().strip()
            except Exception:
                info[key] = "Error"
        
        device._info = info
        return info

    def run_command_on_device(self, device: SSHDevice, command: str) -> tuple[int, str, str]:
        """Run command on specific device."""
        if not device._connected or not device.client:
            raise RuntimeError(f"Not connected to {device}")
        
        stdin, stdout, stderr = device.client.exec_command(command)
        return (
            stdout.channel.recv_exit_status(),
            stdout.read().decode("utf-8", errors="replace"),
            stderr.read().decode("utf-8", errors="replace"),
        )

    def run_command_on_all(self, command: str, 
                           parallel: bool = True) -> Dict[SSHDevice, tuple[int, str, str]]:
        """Run command on all connected devices."""
        results = {}
        
        if parallel:
            # Use threading for parallel execution
            import threading
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def run_on_device(device):
                return device, self.run_command_on_device(device, command)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(run_on_device, device) for device in self.devices if device._connected]
                for future in as_completed(futures):
                    device, result = future.result()
                    results[device] = result
        else:
            # Sequential execution
            for device in self.devices:
                if device._connected:
                    results[device] = self.run_command_on_device(device, command)
        
        return results

    def transfer_file_to_device(self, device: SSHDevice, 
                                local_path: str, remote_path: str) -> bool:
        """Transfer file to device using SCP."""
        if not device._connected or not device.client:
            raise RuntimeError(f"Not connected to {device}")
        
        try:
            sftp = device.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            return True
        except Exception as e:
            console.print(f"[red]✗ File transfer failed to {device}: {e}[/red]")
            return False

    def transfer_file_from_device(self, device: SSHDevice,
                                remote_path: str, local_path: str) -> bool:
        """Transfer file from device using SCP."""
        if not device._connected or not device.client:
            raise RuntimeError(f"Not connected to {device}")
        
        try:
            sftp = device.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            return True
        except Exception as e:
            console.print(f"[red]✗ File transfer failed from {device}: {e}[/red]")
            return False

    def install_meshpi_on_device(self, device: SSHDevice, 
                                 method: str = "pip") -> bool:
        """Install MeshPi on remote device."""
        if not device._connected:
            return False
        
        console.print(f"[cyan]→[/cyan] Installing MeshPi on {device} using {method}...")
        
        if method == "pip":
            commands = [
                "sudo apt update",
                "sudo apt install -y python3-pip python3-venv",
                "pip3 install meshpi",
            ]
        elif method == "venv":
            commands = [
                "sudo apt update", 
                "sudo apt install -y python3-pip python3-venv",
                "python3 -m venv /home/pi/meshpi-env",
                "source /home/pi/meshpi-env/bin/activate",
                "pip install --upgrade pip",
                "pip install meshpi",
            ]
        else:
            console.print(f"[red]✗ Unknown installation method: {method}[/red]")
            return False
        
        for cmd in commands:
            exit_code, stdout, stderr = self.run_command_on_device(device, cmd)
            if exit_code != 0:
                console.print(f"[red]✗ Command failed: {cmd}[/red]")
                console.print(f"[dim]stderr: {stderr[:200]}[/dim]")
                return False
        
        console.print(f"[green]✓[/green] MeshPi installed on {device}")
        return True

    def update_meshpi_on_device(self, device: SSHDevice) -> bool:
        """Update MeshPi on remote device."""
        if not device._connected:
            return False
        
        console.print(f"[cyan]→[/cyan] Updating MeshPi on {device}...")
        
        commands = [
            "pip3 install --upgrade meshpi",
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.run_command_on_device(device, cmd)
            if exit_code != 0:
                console.print(f"[red]✗ Update failed: {cmd}[/red]")
                return False
        
        console.print(f"[green]✓[/green] MeshPi updated on {device}")
        return True

    def restart_meshpi_on_device(self, device: SSHDevice, 
                                service: str = "meshpi-daemon") -> bool:
        """Restart MeshPi service on remote device."""
        if not device._connected:
            return False
        
        console.print(f"[cyan]→[/cyan] Restarting {service} on {device}...")
        
        # Try different service names
        services = [service, "meshpi-host", "meshpi-daemon", "meshpi"]
        
        for svc in services:
            exit_code, stdout, stderr = self.run_command_on_device(device, f"systemctl is-active {svc}")
            if exit_code == 0:
                exit_code, stdout, stderr = self.run_command_on_device(device, f"sudo systemctl restart {svc}")
                if exit_code == 0:
                    console.print(f"[green]✓[/green] {svc} restarted on {device}")
                    return True
        
        console.print(f"[yellow]⚠[/yellow] No MeshPi service found on {device}")
        return False

    def list_devices_table(self) -> None:
        """Display all devices in a table."""
        table = Table(title="Managed SSH Devices", border_style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Host", style="dim")
        table.add_column("User", style="dim")
        table.add_column("Port", style="dim")
        table.add_column("Status", style="bold")
        table.add_column("Tags", style="dim")
        table.add_column("Type", style="dim")
        table.add_column("Vendor", style="dim")
        
        for device in self.devices:
            status = "[green]Connected[/green]" if device._connected else "[dim]Disconnected[/dim]"
            tags_str = ", ".join(device.tags) if device.tags else "—"
            dtype = str(device.meta.get("type", "—"))
            vendor = str(device.meta.get("vendor", "—"))
            table.add_row(
                device.name,
                device.host,
                device.user,
                str(device.port),
                status,
                tags_str,
                dtype,
                vendor,
            )
        
        console.print(table)

    def save_device_list(self, filepath: str) -> None:
        """Save device list to JSON file."""
        devices_data = []
        for device in self.devices:
            devices_data.append({
                "host": device.host,
                "user": device.user,
                "port": device.port,
                "name": device.name,
                "tags": device.tags,
                "meta": device.meta,
            })
        
        Path(filepath).write_text(json.dumps(devices_data, indent=2))
        console.print(f"[green]✓[/green] Device list saved to [bold]{filepath}[/bold]")

    def load_device_list(self, filepath: str) -> None:
        """Load device list from JSON file."""
        if not Path(filepath).exists():
            console.print(f"[red]✗ File not found: {filepath}[/red]")
            return
        
        try:
            devices_data = json.loads(Path(filepath).read_text())
            self.devices.clear()
            
            for device_data in devices_data:
                device = SSHDevice(
                    host=device_data["host"],
                    user=device_data.get("user", "pi"),
                    port=device_data.get("port", 22),
                    name=device_data.get("name"),
                    tags=device_data.get("tags", []),
                    meta=device_data.get("meta", {}),
                )
                self.devices.append(device)
            
            console.print(f"[green]✓[/green] Loaded {len(self.devices)} devices from [bold]{filepath}[/bold]")
        except Exception as e:
            console.print(f"[red]✗ Failed to load device list: {e}[/red]")


def parse_device_target(target: str) -> tuple[str, str, int]:
    """Parse device target like 'pi@192.168.1.100' or 'pi@rpi:2222'."""
    if "@" in target:
        user, host_part = target.split("@", 1)
    else:
        user = "pi"
        host_part = target
    
    if ":" in host_part:
        host, port_str = host_part.rsplit(":", 1)
        port = int(port_str)
    else:
        host = host_part
        port = 22
    
    return user, host, port
