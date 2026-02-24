"""
meshpi.applier
==============
Applies a decrypted config dict to the local Raspberry Pi system.

Handles:
  - Linux user creation / password change
  - WiFi configuration (wpa_supplicant.conf or NetworkManager)
  - Hostname
  - SSH key injection
  - Locale / timezone / keyboard
  - Optional post-install script download & execution
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from rich.console import Console

console = Console()


def _run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True, **kwargs)


def _sudo(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return _run(["sudo"] + cmd, **kwargs)


def apply_config(config: dict) -> None:
    """
    Apply configuration dictionary to the running system.
    Must be run as root (or with sudo privileges).
    """
    console.print("\n[bold cyan]Applying MeshPi configuration…[/bold cyan]\n")
    errors: list[str] = []

    _apply_hostname(config, errors)
    _apply_user(config, errors)
    _apply_wifi(config, errors)
    _apply_ssh(config, errors)
    _apply_interfaces(config, errors)
    _apply_network(config, errors)
    _apply_locale_timezone(config, errors)
    _apply_keyboard(config, errors)
    _apply_post_script(config, errors)

    if errors:
        console.print("\n[bold red]Errors during configuration:[/bold red]")
        for e in errors:
            console.print(f"  [red]•[/red] {e}")
    else:
        console.print("\n[bold green]✓ All configuration applied successfully![/bold green]")
        console.print("[dim]Rebooting in 5 seconds… (Ctrl+C to cancel)[/dim]")
        try:
            import time
            time.sleep(5)
            _sudo(["reboot"])
        except KeyboardInterrupt:
            console.print("[yellow]Reboot cancelled. Please reboot manually.[/yellow]")


# ---------------------------------------------------------------------------
# Individual applier functions
# ---------------------------------------------------------------------------

def _apply_hostname(config: dict, errors: list) -> None:
    hostname = config.get("RPI_HOSTNAME", "").strip()
    if not hostname:
        return
    try:
        _sudo(["hostnamectl", "set-hostname", hostname])
        # Update /etc/hosts
        hosts = Path("/etc/hosts").read_text()
        if "127.0.1.1" in hosts:
            new_hosts = "\n".join(
                f"127.0.1.1\t{hostname}" if line.startswith("127.0.1.1") else line
                for line in hosts.splitlines()
            )
        else:
            new_hosts = hosts + f"\n127.0.1.1\t{hostname}\n"
        _write_as_root("/etc/hosts", new_hosts)
        console.print(f"  [green]✓[/green] Hostname set to [bold]{hostname}[/bold]")
    except Exception as exc:
        errors.append(f"hostname: {exc}")


def _apply_user(config: dict, errors: list) -> None:
    user = config.get("RPI_USER", "pi").strip()
    password = config.get("RPI_PASSWORD", "").strip()

    if not password:
        console.print(f"  [dim]⚠ RPI_USER password not set, skipping[/dim]")
        return
    try:
        result = _run(["id", user], check=False)
        if result.returncode != 0:
            _sudo(["adduser", "--gecos", "", "--disabled-password", user])
            _sudo(["usermod", "-aG", "sudo,gpio,i2c,spi,video,audio", user])
            console.print(f"  [green]✓[/green] User [bold]{user}[/bold] created")
        chpasswd_input = f"{user}:{password}"
        _sudo(["chpasswd"], input=chpasswd_input)
        console.print(f"  [green]✓[/green] Password set for [bold]{user}[/bold]")
    except Exception as exc:
        errors.append(f"user/password: {exc}")


def _apply_wifi(config: dict, errors: list) -> None:
    ssid = config.get("WIFI_SSID", "").strip()
    password = config.get("WIFI_PASSWORD", "").strip()
    country = config.get("WIFI_COUNTRY", "PL").strip()

    if not ssid:
        console.print("  [dim]⚠ WIFI_SSID not set, skipping WiFi[/dim]")
        return

    try:
        wpa_conf = f"""ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country={country}

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
        _write_as_root("/etc/wpa_supplicant/wpa_supplicant.conf", wpa_conf)
        _sudo(["chmod", "600", "/etc/wpa_supplicant/wpa_supplicant.conf"])
        # Restart wifi
        _sudo(["wpa_cli", "-i", "wlan0", "reconfigure"], check=False)
        console.print(f"  [green]✓[/green] WiFi configured for SSID [bold]{ssid}[/bold]")
    except Exception as exc:
        errors.append(f"wifi: {exc}")


def _apply_ssh(config: dict, errors: list) -> None:
    """Apply SSH configuration: enable/disable, port, password auth, and key injection."""
    ssh_enable = config.get("SSH_ENABLE", "yes").strip().lower() in ("yes", "true", "1")
    ssh_port = config.get("SSH_PORT", "22").strip()
    password_auth = config.get("SSH_PASSWORD_AUTH", "yes").strip().lower() in ("yes", "true", "1")
    key = config.get("SSH_PUBLIC_KEY", "").strip()
    user = config.get("RPI_USER", "pi").strip()

    try:
        # Enable/disable SSH service
        if ssh_enable:
            _sudo(["systemctl", "enable", "ssh"], check=False)
            _sudo(["systemctl", "start", "ssh"], check=False)
            console.print(f"  [green]✓[/green] SSH enabled")
        else:
            _sudo(["systemctl", "disable", "ssh"], check=False)
            _sudo(["systemctl", "stop", "ssh"], check=False)
            console.print(f"  [yellow]✓[/yellow] SSH disabled")
            return  # No need to configure further if disabled

        # Configure SSH port
        if ssh_port != "22":
            sshd_config = Path("/etc/ssh/sshd_config")
            if sshd_config.exists():
                content = sshd_config.read_text()
                if f"Port {ssh_port}" not in content:
                    # Add or replace Port directive
                    lines = []
                    port_set = False
                    for line in content.splitlines():
                        if line.startswith("#Port ") or line.startswith("Port "):
                            lines.append(f"Port {ssh_port}")
                            port_set = True
                        else:
                            lines.append(line)
                    if not port_set:
                        lines.append(f"Port {ssh_port}")
                    _write_as_root(str(sshd_config), "\n".join(lines) + "\n")
                    _sudo(["systemctl", "restart", "ssh"], check=False)
                    console.print(f"  [green]✓[/green] SSH port set to [bold]{ssh_port}[/bold]")

        # Configure password authentication
        sshd_config = Path("/etc/ssh/sshd_config")
        if sshd_config.exists():
            content = sshd_config.read_text()
            auth_value = "yes" if password_auth else "no"
            lines = []
            for line in content.splitlines():
                if line.startswith("#PasswordAuthentication ") or line.startswith("PasswordAuthentication "):
                    lines.append(f"PasswordAuthentication {auth_value}")
                else:
                    lines.append(line)
            _write_as_root(str(sshd_config), "\n".join(lines) + "\n")
            console.print(f"  [green]✓[/green] SSH password auth: [bold]{auth_value}[/bold]")

        # Inject SSH public key
        if key:
            ssh_dir = Path(f"/home/{user}/.ssh")
            _sudo(["mkdir", "-p", str(ssh_dir)])
            authorized = ssh_dir / "authorized_keys"

            existing = ""
            if authorized.exists():
                existing = authorized.read_text()
            if key not in existing:
                _write_as_root(str(authorized), existing + "\n" + key + "\n")

            _sudo(["chown", "-R", f"{user}:{user}", str(ssh_dir)])
            _sudo(["chmod", "700", str(ssh_dir)])
            _sudo(["chmod", "600", str(authorized)])
            console.print(f"  [green]✓[/green] SSH public key injected for [bold]{user}[/bold]")

    except Exception as exc:
        errors.append(f"ssh: {exc}")


def _apply_interfaces(config: dict, errors: list) -> None:
    """Enable/disable hardware interfaces: I2C, SPI, Serial, Camera."""
    interfaces = [
        ("ENABLE_I2C", "i2c", "i2c_arm"),
        ("ENABLE_SPI", "spi", "spi"),
        ("ENABLE_SERIAL", "serial", "serial"),
        ("ENABLE_CAMERA", "camera", "camera"),
    ]
    
    for key, name, config_name in interfaces:
        enable = config.get(key, "no").strip().lower() in ("yes", "true", "1")
        if not enable:
            continue
        try:
            # Use raspi-config for Raspberry Pi
            _sudo(["raspi-config", "nonint", f"do_{name}", "0"], check=False)
            console.print(f"  [green]✓[/green] {name.upper()} interface enabled")
        except Exception as exc:
            errors.append(f"{name}: {exc}")


def _apply_network(config: dict, errors: list) -> None:
    """Configure static IP if specified."""
    static_ip = config.get("STATIC_IP", "").strip()
    gateway = config.get("GATEWAY", "").strip()
    dns = config.get("DNS_SERVERS", "8.8.8.8,8.8.4.4").strip()

    if not static_ip:
        return  # Use DHCP

    try:
        # Determine network interface
        result = _run(["ip", "route"], check=False)
        iface = "eth0"
        for line in result.stdout.splitlines():
            if "dev" in line and "wlan" not in line:
                parts = line.split()
                if "dev" in parts:
                    iface = parts[parts.index("dev") + 1]
                    break

        # Create static IP configuration for dhcpcd
        dhcpcd_conf = f"""
# Static IP configuration (added by MeshPi)
interface {iface}
    static ip_address={static_ip}/24
    static routers={gateway}
    static domain_name_servers={dns.replace(',', ' ')}
"""
        _write_as_root("/etc/dhcpcd.conf", dhcpcd_conf)
        console.print(f"  [green]✓[/green] Static IP configured: [bold]{static_ip}[/bold]")
    except Exception as exc:
        errors.append(f"network: {exc}")


def _apply_locale_timezone(config: dict, errors: list) -> None:
    timezone = config.get("RPI_TIMEZONE", "").strip()
    locale = config.get("RPI_LOCALE", "").strip()

    if timezone:
        try:
            _sudo(["timedatectl", "set-timezone", timezone])
            console.print(f"  [green]✓[/green] Timezone set to [bold]{timezone}[/bold]")
        except Exception as exc:
            errors.append(f"timezone: {exc}")

    if locale:
        try:
            _sudo(["locale-gen", locale], check=False)
            _sudo(["update-locale", f"LANG={locale}", f"LC_ALL={locale}"], check=False)
            console.print(f"  [green]✓[/green] Locale set to [bold]{locale}[/bold]")
        except Exception as exc:
            errors.append(f"locale: {exc}")


def _apply_keyboard(config: dict, errors: list) -> None:
    layout = config.get("RPI_KEYBOARD", "").strip()
    if not layout:
        return
    try:
        _sudo(["raspi-config", "nonint", "do_configure_keyboard", layout], check=False)
        console.print(f"  [green]✓[/green] Keyboard layout set to [bold]{layout}[/bold]")
    except Exception as exc:
        errors.append(f"keyboard: {exc}")


def _apply_post_script(config: dict, errors: list) -> None:
    url = config.get("POST_SCRIPT_URL", "").strip()
    if not url:
        return
    try:
        import httpx
        console.print(f"  [cyan]↓[/cyan] Downloading post-install script from [dim]{url}[/dim]")
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(response.text)
            script_path = f.name

        os.chmod(script_path, 0o755)
        _sudo(["bash", script_path])
        os.unlink(script_path)
        console.print("  [green]✓[/green] Post-install script executed")
    except Exception as exc:
        errors.append(f"post_script: {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_as_root(path: str, content: str) -> None:
    """Write file content using tee via sudo (avoids needing to run whole process as root)."""
    proc = subprocess.Popen(
        ["sudo", "tee", path],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _, err = proc.communicate(content.encode())
    if proc.returncode != 0:
        raise RuntimeError(err.decode())
