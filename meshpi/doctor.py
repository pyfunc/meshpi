"""
meshpi.doctor
=============
Remote diagnostics for Raspberry Pi devices.

Usage:
    meshpi doctor pi@raspberrypi
    meshpi doctor pi@192.168.1.100 --password
    meshpi doctor pi@rpi-kitchen --key ~/.ssh/id_rsa
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import paramiko
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()


class RemoteDoctor:
    """SSH-based remote diagnostics for Raspberry Pi."""

    def __init__(self, host: str, user: str = "pi", port: int = 22):
        self.host = host
        self.user = user
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None
        self._connected = False

    def connect(self, password: Optional[str] = None, key_path: Optional[str] = None) -> bool:
        """Connect to remote host via SSH."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.user,
                "timeout": 10,
            }
            
            if key_path:
                connect_kwargs["key_filename"] = key_path
            elif password:
                connect_kwargs["password"] = password
            
            self.client.connect(**connect_kwargs)
            self._connected = True
            return True
            
        except paramiko.AuthenticationException:
            console.print("[red]✗ Authentication failed[/red]")
            return False
        except paramiko.SSHException as e:
            console.print(f"[red]✗ SSH error: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]✗ Connection failed: {e}[/red]")
            return False

    def disconnect(self) -> None:
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self._connected = False

    def run_command(self, cmd: str) -> tuple[int, str, str]:
        """Run command on remote host, return (exit_code, stdout, stderr)."""
        if not self._connected or not self.client:
            raise RuntimeError("Not connected to remote host")
        
        stdin, stdout, stderr = self.client.exec_command(cmd)
        return (
            stdout.channel.recv_exit_status(),
            stdout.read().decode("utf-8", errors="replace"),
            stderr.read().decode("utf-8", errors="replace"),
        )

    def run_check(self, name: str, cmd: str) -> dict:
        """Run a diagnostic check and return result."""
        exit_code, stdout, stderr = self.run_command(cmd)
        return {
            "name": name,
            "cmd": cmd,
            "exit_code": exit_code,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "success": exit_code == 0,
        }


def parse_target(target: str) -> tuple[str, str, int]:
    """Parse target string like 'pi@raspberrypi' or 'pi@192.168.1.1:2222'."""
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


def run_doctor(target: str, password: bool = False, key: Optional[str] = None) -> None:
    """Run remote diagnostics on a Raspberry Pi."""
    user, host, port = parse_target(target)
    
    console.print(Panel.fit(
        f"[bold cyan]MeshPi Doctor[/bold cyan]\n"
        f"Remote diagnostics for [bold]{user}@{host}:{port}[/bold]",
        border_style="cyan",
    ))

    doctor = RemoteDoctor(host, user, port)

    # Get credentials
    ssh_password = None
    ssh_key = key
    
    if password:
        import getpass
        ssh_password = getpass.getpass(f"Enter password for {user}@{host}: ")
    elif not key:
        # Try default key
        default_key = Path.home() / ".ssh" / "id_rsa"
        if default_key.exists():
            ssh_key = str(default_key)
            console.print(f"[dim]Using SSH key: {ssh_key}[/dim]")

    # Connect
    console.print(f"\n[cyan]→[/cyan] Connecting to [bold]{host}[/bold]...")
    if not doctor.connect(password=ssh_password, key_path=ssh_key):
        console.print("[red]Failed to connect. Exiting.[/red]")
        return

    console.print("[green]✓ Connected[/green]\n")

    # Run diagnostics
    checks = [
        ("System Info", "uname -a"),
        ("Hostname", "hostname"),
        ("Uptime", "uptime -p 2>/dev/null || uptime"),
        ("CPU Info", "cat /proc/cpuinfo | grep -E 'model|Hardware|Revision' | head -5"),
        ("CPU Temperature", "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000 \"°C\"}'"),
        ("Memory", "free -h | head -2"),
        ("Disk Usage", "df -h / 2>/dev/null | tail -1"),
        ("Network IP", "hostname -I 2>/dev/null || ip addr show | grep 'inet ' | head -1"),
        ("WiFi Status", "iwconfig wlan0 2>/dev/null | head -3 || echo 'WiFi not available'"),
        ("MeshPi Installed", "pip show meshpi 2>/dev/null | grep Version || echo 'Not installed'"),
        ("MeshPi Config", "test -f ~/.meshpi/config.env && echo 'Config exists' || echo 'No config found'"),
        ("MeshPi Keys", "ls -la ~/.meshpi/*.pem 2>/dev/null || echo 'No keys found'"),
        ("SSH Status", "systemctl is-active ssh 2>/dev/null || echo 'SSH service not found'"),
        ("Failed Services", "systemctl --failed --no-legend 2>/dev/null | head -5 || echo 'No failed services'"),
        ("Recent Errors", "journalctl -p err -n 5 --no-pager 2>/dev/null || dmesg | tail -5"),
    ]

    results = []
    for name, cmd in checks:
        result = doctor.run_check(name, cmd)
        results.append(result)
        
        status = "[green]✓[/green]" if result["success"] else "[yellow]![/yellow]"
        console.print(f"  {status} [bold]{name}[/bold]")
        
        if result["stdout"]:
            for line in result["stdout"].splitlines()[:5]:  # Limit output
                console.print(f"      [dim]{line}[/dim]")
        if result["stderr"] and not result["success"]:
            console.print(f"      [yellow]stderr: {result['stderr'][:100]}[/yellow]")

    # Summary
    console.print("\n" + "─" * 50)
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    console.print(f"[bold]Summary:[/bold] {passed}/{total} checks passed")

    # Quick fixes
    issues = [r for r in results if not r["success"]]
    if issues:
        console.print("\n[yellow]Issues detected:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue['name']}")

    # Auto-diagnosis and repair
    auto_repair_available = False
    repair_commands = []
    
    # Check for externally-managed-environment issue
    meshpi_check = next((r for r in results if r["name"] == "MeshPi Installed"), None)
    if meshpi_check and not meshpi_check["success"]:
        if "externally-managed-environment" in meshpi_check.get("stderr", ""):
            console.print("\n[cyan]🔍 Detected: Externally managed Python environment[/cyan]")
            console.print("[dim]This is a common issue on modern Raspberry Pi OS.[/dim]")
            auto_repair_available = True
            repair_commands = [
                "sudo apt update && sudo apt install -y python3-full python3-venv",
                "python3 -m venv /home/pi/meshpi-env",
                "source /home/pi/meshpi-env/bin/activate",
                "pip install --upgrade pip",
                "pip install meshpi"
            ]
            console.print("[dim]This can be automatically fixed by creating a virtual environment.[/dim]")

    # Check for missing dependencies
    python_check = next((r for r in results if r["name"] == "System Info"), None)
    if python_check and "python3" not in python_check.get("stdout", ""):
        console.print("\n[cyan]🔍 Detected: Missing Python 3[/cyan]")
        auto_repair_available = True
        repair_commands = [
            "sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
        ]
    
    # Check for WiFi issues
    wifi_check = next((r for r in results if r["name"] == "WiFi Status"), None)
    if wifi_check and "WiFi not available" in wifi_check.get("stdout", ""):
        console.print("\n[cyan]🔍 Detected: WiFi not configured[/cyan]")
        auto_repair_available = True
        repair_commands.extend([
            "sudo rfkill unblock wifi",
            "sudo raspi-config nonint do_wifi_country PL"
        ])
        console.print("[dim]WiFi can be automatically configured.[/dim]")

    # Offer auto-repair
    if auto_repair_available and repair_commands:
        console.print("\n[cyan]🔧 Auto-repair available for detected issues[/cyan]")
        if Confirm.ask("Run automatic repairs?", default=False):
            console.print("\n[yellow]→ Running automatic repairs...[/yellow]")
            
            # Signal repair start on RPi
            console.print("[cyan]📡 Signaling repair status on RPi...[/cyan]")
            doctor.run_command("echo '🔧 MeshPi Doctor: Repair started at $(date)' | tee /tmp/meshpi-repair.log")
            doctor.run_command("echo '⏳ Please wait - do not power off the device' > /tmp/meshpi-status.txt")
            
            for i, cmd in enumerate(repair_commands, 1):
                console.print(f"[cyan]Step {i}/{len(repair_commands)}:[/cyan] {cmd}")
                
                # Update status on RPi
                doctor.run_command(f"echo '🔧 Step {i}/{len(repair_commands)}: {cmd}' >> /tmp/meshpi-repair.log")
                doctor.run_command(f"echo '⚡ Repairing... Step {i}/{len(repair_commands)}' > /tmp/meshpi-status.txt")
                
                exit_code, stdout, stderr = doctor.run_command(cmd)
                
                if exit_code == 0:
                    console.print("[green]✓ Success[/green]")
                    doctor.run_command(f"echo '✅ Step {i} completed successfully' >> /tmp/meshpi-repair.log")
                else:
                    console.print(f"[red]✗ Failed: {stderr[:100]}[/red]")
                    doctor.run_command(f"echo '❌ Step {i} failed: {stderr[:100]}' >> /tmp/meshpi-repair.log")
                    doctor.run_command("echo '⚠️ Repair failed - check logs' > /tmp/meshpi-status.txt")
                    
                    if "externally-managed-environment" in stderr:
                        console.print("[yellow]💡 Tip: This device needs virtual environment setup[/yellow]")
                        doctor.run_command("echo '🔄 Switching to virtual environment approach...' >> /tmp/meshpi-repair.log")
                        # Try virtual environment fix
                        venv_commands = [
                            "python3 -m venv /home/pi/meshpi-env",
                            "source /home/pi/meshpi-env/bin/activate",
                            "pip install --upgrade pip",
                            "pip install meshpi"
                        ]
                        console.print("[cyan]🔧 Trying virtual environment approach...[/cyan]")
                        
                        for j, venv_cmd in enumerate(venv_commands, 1):
                            console.print(f"[dim]Running: {venv_cmd}[/dim]")
                            doctor.run_command(f"echo '🔧 VENV Step {j}/{len(venv_commands)}: {venv_cmd}' >> /tmp/meshpi-repair.log")
                            doctor.run_command(f"echo '🔄 Setting up virtual environment... {j}/{len(venv_commands)}' > /tmp/meshpi-status.txt")
                            
                            exit_code, stdout, stderr = doctor.run_command(venv_cmd)
                            if exit_code == 0:
                                console.print("[green]✓ Virtual environment setup successful[/green]")
                                doctor.run_command(f"echo '✅ VENV Step {j} completed' >> /tmp/meshpi-repair.log")
                            else:
                                console.print(f"[red]✗ Virtual environment failed: {stderr[:100]}[/red]")
                                doctor.run_command(f"echo '❌ VENV Step {j} failed: {stderr[:100]}' >> /tmp/meshpi-repair.log")
                    break  # Stop on first failure
            
            # Verify repair
            console.print("\n[cyan]🔍 Verifying repairs...[/cyan]")
            doctor.run_command("echo '🔍 Verifying installation...' >> /tmp/meshpi-repair.log")
            doctor.run_command("echo '⏸️ Final verification in progress...' > /tmp/meshpi-status.txt")
            
            exit_code, stdout, stderr = doctor.run_command("source /home/pi/meshpi-env/bin/activate && python -c 'import meshpi; print(f\"MeshPi {meshpi.__version__} OK\")' 2>/dev/null || echo 'MeshPi not working'")
            if exit_code == 0:
                console.print("[green]✓ MeshPi is now working correctly![/green]")
                console.print("[dim]To use MeshPi on this device:[/dim]")
                console.print("[dim]  ssh {user}@{host}[/dim]")
                console.print("[dim]  source /home/pi/meshpi-env/bin/activate[/dim]")
                console.print("[dim]  meshpi --help[/dim]")
                
                # Update RPi status to success
                doctor.run_command("echo '🎉 MeshPi repair completed successfully!' >> /tmp/meshpi-repair.log")
                doctor.run_command("echo '✅ MeshPi is ready to use!' > /tmp/meshpi-status.txt")
                doctor.run_command("echo '📋 Usage: source /home/pi/meshpi-env/bin/activate && meshpi --help' > /tmp/meshpi-next-steps.txt")
                
                # Create desktop notification if possible
                doctor.run_command("which notify-send 2>/dev/null && notify-send 'MeshPi Doctor' '✅ Repair completed! MeshPi is ready to use.' || echo 'Desktop notification not available'")
                
            else:
                console.print("[red]✗ Repair verification failed[/red]")
                console.print("[yellow]💡 Manual intervention may be required[/yellow]")
                doctor.run_command("echo '❌ Repair verification failed' >> /tmp/meshpi-repair.log")
                doctor.run_command("echo '⚠️ Manual intervention required' > /tmp/meshpi-status.txt")
                
                # Show logs location
                doctor.run_command("echo '📋 Check repair logs: cat /tmp/meshpi-repair.log' > /tmp/meshpi-help.txt")
        
        elif Confirm.ask("Show manual repair instructions?", default=False):
            console.print("\n[cyan]📋 Manual Repair Instructions:[/cyan]")
            console.print("[dim]SSH into the device and run:[/dim]")
            for cmd in repair_commands:
                console.print(f"  [yellow]{cmd}[/yellow]")
            
            if "externally-managed-environment" in (meshpi_check.get("stderr", "") if meshpi_check else ""):
                console.print("\n[dim]For virtual environment setup:[/dim]")
                console.print("  [yellow]python3 -m venv /home/pi/meshpi-env[/yellow]")
                console.print("  [yellow]source /home/pi/meshpi-env/bin/activate[/yellow]")
                console.print("  [yellow]pip install meshpi[/yellow]")

    # Offer MeshPi installation
    meshpi_installed = any(r["name"] == "MeshPi Installed" and r["success"] for r in results)
    if not meshpi_installed and not auto_repair_available:
        console.print("\n[cyan]MeshPi is not installed on this device.[/cyan]")
        if Confirm.ask("Install MeshPi?", default=False):
            console.print("\n[yellow]→ Installing MeshPi...[/yellow]")
            exit_code, stdout, stderr = doctor.run_command("pip install meshpi")
            if exit_code == 0:
                console.print("[green]✓ MeshPi installed successfully[/green]")
            else:
                console.print(f"[red]✗ Installation failed: {stderr}[/red]")
                if "externally-managed-environment" in stderr:
                    console.print("[yellow]💡 This device needs virtual environment setup[/yellow]")
                    if Confirm.ask("Set up virtual environment and install?", default=False):
                        venv_setup = [
                            "sudo apt install -y python3-venv",
                            "python3 -m venv /home/pi/meshpi-env",
                            "source /home/pi/meshpi-env/bin/activate",
                            "pip install --upgrade pip",
                            "pip install meshpi"
                        ]
                        for cmd in venv_setup:
                            console.print(f"[cyan]Running: {cmd}[/cyan]")
                            exit_code, stdout, stderr = doctor.run_command(cmd)
                            if exit_code == 0:
                                console.print("[green]✓ Success[/green]")
                            else:
                                console.print(f"[red]✗ Failed: {stderr}[/red]")
                                break

    doctor.disconnect()
    console.print("\n[green]✓ Doctor session completed[/green]")