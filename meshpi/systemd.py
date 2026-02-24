"""
meshpi.systemd
==============
Install / uninstall systemd services for meshpi daemon and host.

CLIENT:
    meshpi daemon --install
    → installs meshpi-daemon.service (auto-start on boot)

HOST:
    meshpi host --install
    → installs meshpi-host.service (auto-start on boot)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

console = Console()

SYSTEMD_DIR = Path("/etc/systemd/system")
USER_SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"


DAEMON_SERVICE = """\
[Unit]
Description=MeshPi Client Daemon
Documentation=https://github.com/softreck/meshpi
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
ExecStart={meshpi_bin} daemon {extra_args}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=meshpi-daemon
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

HOST_SERVICE = """\
[Unit]
Description=MeshPi Host Service
Documentation=https://github.com/softreck/meshpi
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
ExecStart={meshpi_bin} host --port {port} {extra_args}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=meshpi-host
Environment=PYTHONUNBUFFERED=1
{env_lines}

[Install]
WantedBy=multi-user.target
"""


def _meshpi_bin() -> str:
    """Resolve full path to the meshpi executable."""
    path = shutil.which("meshpi")
    if path:
        return path
    # Fallback: use python -m meshpi.cli
    return f"{sys.executable} -m meshpi.cli"


def _current_user() -> str:
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or "pi"


def _run_sudo(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(["sudo"] + cmd, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def _write_service(name: str, content: str) -> None:
    service_path = SYSTEMD_DIR / name
    # Write via sudo tee
    proc = subprocess.Popen(
        ["sudo", "tee", str(service_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _, err = proc.communicate(content.encode())
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to write {service_path}: {err.decode()}")
    subprocess.run(["sudo", "chmod", "644", str(service_path)])


def install_daemon_service(
    host: str | None = None,
    port: int = 7422,
    user: str | None = None,
    env_vars: dict | None = None,
) -> None:
    """Install and enable meshpi-daemon.service."""
    user = user or _current_user()
    meshpi_bin = _meshpi_bin()
    extra_args = ""
    if host:
        extra_args += f" --host {host}"
    if port != 7422:
        extra_args += f" --port {port}"

    content = DAEMON_SERVICE.format(
        user=user,
        meshpi_bin=meshpi_bin,
        extra_args=extra_args.strip(),
    )

    if not Confirm.ask(
        f"\nInstall [bold]meshpi-daemon.service[/bold] for user [bold]{user}[/bold]?",
        default=True,
    ):
        return

    _write_service("meshpi-daemon.service", content)
    _run_sudo(["systemctl", "daemon-reload"])
    _run_sudo(["systemctl", "enable", "meshpi-daemon.service"])

    if Confirm.ask("Start service now?", default=True):
        rc, out = _run_sudo(["systemctl", "start", "meshpi-daemon.service"])
        if rc == 0:
            console.print("[green]✓[/green] meshpi-daemon.service started")
        else:
            console.print(f"[red]✗[/red] Failed to start: {out}")
    else:
        console.print("[green]✓[/green] meshpi-daemon.service installed and enabled (will start at next boot)")

    console.print("\n[dim]Manage with:[/dim]")
    console.print("  sudo systemctl status meshpi-daemon")
    console.print("  sudo journalctl -fu meshpi-daemon")


def install_host_service(
    port: int = 7422,
    user: str | None = None,
    with_agent: bool = False,
    env_vars: dict | None = None,
) -> None:
    """Install and enable meshpi-host.service."""
    user = user or _current_user()
    meshpi_bin = _meshpi_bin()
    extra_args = "--agent" if with_agent else ""

    env_lines = ""
    if env_vars:
        env_lines = "\n".join(f"Environment={k}={v}" for k, v in env_vars.items())

    content = HOST_SERVICE.format(
        user=user,
        meshpi_bin=meshpi_bin,
        port=port,
        extra_args=extra_args,
        env_lines=env_lines,
    )

    if not Confirm.ask(
        f"\nInstall [bold]meshpi-host.service[/bold] for user [bold]{user}[/bold]?",
        default=True,
    ):
        return

    _write_service("meshpi-host.service", content)
    _run_sudo(["systemctl", "daemon-reload"])
    _run_sudo(["systemctl", "enable", "meshpi-host.service"])

    if Confirm.ask("Start service now?", default=True):
        rc, out = _run_sudo(["systemctl", "start", "meshpi-host.service"])
        if rc == 0:
            console.print("[green]✓[/green] meshpi-host.service started")
        else:
            console.print(f"[red]✗[/red] {out}")
    else:
        console.print("[green]✓[/green] meshpi-host.service installed and enabled")

    console.print("\n[dim]Manage with:[/dim]")
    console.print("  sudo systemctl status meshpi-host")
    console.print("  sudo journalctl -fu meshpi-host")


def uninstall_service(name: str) -> None:
    """Stop, disable and remove a meshpi systemd service."""
    service_name = name if name.endswith(".service") else f"{name}.service"
    service_path = SYSTEMD_DIR / service_name

    if not service_path.exists():
        console.print(f"[yellow]Service {service_name} not found[/yellow]")
        return

    if not Confirm.ask(f"Remove [bold]{service_name}[/bold]?", default=False):
        return

    _run_sudo(["systemctl", "stop", service_name])
    _run_sudo(["systemctl", "disable", service_name])
    _run_sudo(["rm", str(service_path)])
    _run_sudo(["systemctl", "daemon-reload"])
    console.print(f"[green]✓[/green] {service_name} removed")


def service_status(name: str) -> None:
    """Print systemd service status."""
    service_name = name if name.endswith(".service") else f"{name}.service"
    subprocess.run(["systemctl", "status", service_name, "--no-pager"])
