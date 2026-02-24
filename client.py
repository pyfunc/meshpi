"""
meshpi.client
=============
Scans the local network for MeshPi host services via mDNS,
downloads encrypted configuration, decrypts it and applies it locally.
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Optional

import httpx
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

from .crypto import (
    decrypt_config,
    get_or_create_client_keys,
    public_key_to_pem,
)

console = Console()

SERVICE_TYPE = "_meshpi._tcp.local."
SCAN_TIMEOUT = 8  # seconds
DEFAULT_PORT = 7422


# ---------------------------------------------------------------------------
# mDNS discovery
# ---------------------------------------------------------------------------

@dataclass
class HostInfo:
    name: str
    address: str
    port: int

    @property
    def base_url(self) -> str:
        return f"http://{self.address}:{self.port}"


class _MeshPiListener(ServiceListener):
    def __init__(self):
        self.hosts: list[HostInfo] = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info and info.addresses:
            ip = socket.inet_ntoa(info.addresses[0])
            friendly = name.replace(f".{type_}", "").replace(".local.", "")
            self.hosts.append(HostInfo(name=friendly, address=ip, port=info.port))
            console.print(f"  [cyan]Found:[/cyan] [bold]{friendly}[/bold] @ {ip}:{info.port}")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass


def discover_hosts(timeout: int = SCAN_TIMEOUT) -> list[HostInfo]:
    """Scan the local network for MeshPi hosts. Returns list of found hosts."""
    console.print(f"[bold]Scanning for MeshPi hosts[/bold] (up to {timeout}s)…\n")
    zc = Zeroconf()
    listener = _MeshPiListener()
    browser = ServiceBrowser(zc, SERVICE_TYPE, listener)

    try:
        time.sleep(timeout)
    finally:
        zc.close()

    return listener.hosts


# ---------------------------------------------------------------------------
# Config download & apply
# ---------------------------------------------------------------------------

def _select_host(hosts: list[HostInfo]) -> Optional[HostInfo]:
    """Auto-select if single host, prompt if multiple."""
    if not hosts:
        return None
    if len(hosts) == 1:
        console.print(f"\n[green]Auto-selecting[/green] the only host: [bold]{hosts[0].name}[/bold]")
        return hosts[0]

    table = Table(title="Available MeshPi Hosts", border_style="cyan")
    table.add_column("#", style="bold")
    table.add_column("Name")
    table.add_column("Address")
    table.add_column("Port")
    for i, h in enumerate(hosts, 1):
        table.add_row(str(i), h.name, h.address, str(h.port))
    console.print(table)

    choice = Prompt.ask(
        "Select host number",
        choices=[str(i) for i in range(1, len(hosts) + 1)],
    )
    return hosts[int(choice) - 1]


def fetch_and_apply_config(host: HostInfo, apply: bool = True) -> dict:
    """
    1. Generate (or load) client RSA key pair
    2. Fetch host public key for display/verification
    3. POST client public key to host, receive encrypted config
    4. Decrypt config
    5. Optionally apply to local system
    """
    client_priv, client_pub = get_or_create_client_keys()
    client_pub_pem = public_key_to_pem(client_pub).decode()

    with httpx.Client(base_url=host.base_url, timeout=30) as http:
        # Step 1: Get host info & public key
        console.print(f"\n[cyan]→[/cyan] Connecting to [bold]{host.base_url}[/bold]")
        info = http.get("/info").json()
        console.print(f"  Host: [bold]{info.get('hostname')}[/bold]  version: {info.get('version')}")

        # Step 2: Request encrypted config
        console.print("[cyan]→[/cyan] Requesting encrypted configuration…")
        response = http.post(
            "/config",
            json={"client_public_key_pem": client_pub_pem},
        )
        response.raise_for_status()
        payload_str = response.json()["payload"]

    # Step 3: Decrypt
    console.print("[cyan]→[/cyan] Decrypting configuration…")
    config = decrypt_config(payload_str.encode(), client_priv)
    console.print(f"[green]✓[/green] Received [bold]{len(config)}[/bold] configuration fields")

    if apply:
        from .applier import apply_config
        apply_config(config)

    return config


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_scan(manual_host: Optional[str] = None, port: int = DEFAULT_PORT, dry_run: bool = False) -> None:
    """
    Main scan entry point.

    Args:
        manual_host: If given, skip mDNS and connect directly (IP or hostname).
        port: Port override.
        dry_run: If True, fetch config but don't apply it.
    """
    if manual_host:
        hosts = [HostInfo(name=manual_host, address=manual_host, port=port)]
    else:
        hosts = discover_hosts()

    if not hosts:
        console.print("\n[red]✗[/red] No MeshPi hosts found on the local network.")
        console.print("[dim]Make sure the host is running: [bold]meshpi host[/bold][/dim]")
        return

    selected = _select_host(hosts)
    if not selected:
        return

    try:
        config = fetch_and_apply_config(selected, apply=not dry_run)
        if dry_run:
            console.print("\n[yellow]Dry-run mode:[/yellow] config received but NOT applied")
            for k, v in config.items():
                is_secret = any(x in k.lower() for x in ["password", "key", "secret"])
                console.print(f"  [dim]{k}[/dim] = {'****' if is_secret else v}")
    except Exception as exc:
        console.print(f"\n[red]✗[/red] Failed to fetch config: {exc}")
