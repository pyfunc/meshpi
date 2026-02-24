"""
meshpi.client
=============
MeshPi client — runs on the Raspberry Pi.

Responsibilities:
  1. Discover MeshPi host via mDNS
  2. Download encrypted config and apply it (initial setup)
  3. Maintain persistent WebSocket to host for:
       - Periodic diagnostics push
       - Receiving real-time config updates
       - Receiving and executing commands (apply_profile / run_command / reboot)
"""

from __future__ import annotations

import asyncio
import json
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import httpx
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

from .crypto import decrypt_config, get_or_create_client_keys, public_key_to_pem
from .diagnostics import collect as collect_diagnostics

console = Console()

SERVICE_TYPE = "_meshpi._tcp.local."
SCAN_TIMEOUT = 8
DEFAULT_PORT = 7422
DIAG_INTERVAL = 60       # seconds between diagnostic pushes


@dataclass
class HostInfo:
    name: str
    address: str
    port: int

    @property
    def base_url(self) -> str:
        return f"http://{self.address}:{self.port}"

    @property
    def ws_url(self) -> str:
        return f"ws://{self.address}:{self.port}"


# ─────────────────────────────────────────────────────────────────────────────
# mDNS discovery
# ─────────────────────────────────────────────────────────────────────────────

class _MeshPiListener(ServiceListener):
    def __init__(self):
        self.hosts: list[HostInfo] = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info and info.addresses:
            import struct
            ip = socket.inet_ntoa(info.addresses[0])
            friendly = name.replace(f".{type_}", "").replace(".local.", "")
            self.hosts.append(HostInfo(name=friendly, address=ip, port=info.port))
            console.print(f"  [cyan]Found:[/cyan] [bold]{friendly}[/bold] @ {ip}:{info.port}")

    def remove_service(self, *_): pass
    def update_service(self, *_): pass


def discover_hosts(timeout: int = SCAN_TIMEOUT) -> list[HostInfo]:
    console.print(f"[bold]Scanning for MeshPi hosts[/bold] ({timeout}s)...\n")
    zc = Zeroconf()
    listener = _MeshPiListener()
    ServiceBrowser(zc, SERVICE_TYPE, listener)
    try:
        time.sleep(timeout)
    finally:
        zc.close()
    return listener.hosts


def _select_host(hosts: list[HostInfo]) -> Optional[HostInfo]:
    if not hosts:
        return None
    if len(hosts) == 1:
        console.print(f"\n[green]Auto-selecting:[/green] [bold]{hosts[0].name}[/bold]")
        return hosts[0]
    table = Table(title="Available MeshPi Hosts", border_style="cyan")
    table.add_column("#"); table.add_column("Name"); table.add_column("Address"); table.add_column("Port")
    for i, h in enumerate(hosts, 1):
        table.add_row(str(i), h.name, h.address, str(h.port))
    console.print(table)
    choice = Prompt.ask("Select host", choices=[str(i) for i in range(1, len(hosts) + 1)])
    return hosts[int(choice) - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Initial config download
# ─────────────────────────────────────────────────────────────────────────────

def fetch_and_apply_config(host: HostInfo, apply: bool = True) -> dict:
    client_priv, client_pub = get_or_create_client_keys()
    client_pub_pem = public_key_to_pem(client_pub).decode()

    with httpx.Client(base_url=host.base_url, timeout=30) as http:
        info = http.get("/info").json()
        console.print(f"  Host: [bold]{info.get('hostname')}[/bold]")

        response = http.post("/config", json={"client_public_key_pem": client_pub_pem})
        response.raise_for_status()
        payload_str = response.json()["payload"]

    config = decrypt_config(payload_str.encode(), client_priv)
    console.print(f"[green]v[/green] Config received ({len(config)} fields)")

    if apply:
        from .applier import apply_config
        apply_config(config)

    return config


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket persistent connection (daemon mode)
# ─────────────────────────────────────────────────────────────────────────────

async def _ws_daemon(host: HostInfo, device_id: str) -> None:
    """
    Maintain persistent WebSocket connection to host.
    Pushes diagnostics every DIAG_INTERVAL seconds.
    Handles incoming commands.
    """
    try:
        import websockets
    except ImportError:
        console.print("[red]websockets not installed. Run: pip install websockets[/red]")
        return

    ws_url = f"{host.ws_url}/ws/{device_id}"
    console.print(f"[cyan]WS:[/cyan] Connecting to {ws_url}")

    reconnect_delay = 5
    seq = 0

    while True:
        try:
            async with websockets.connect(ws_url, ping_interval=20) as ws:
                reconnect_delay = 5

                # Say hello
                await ws.send(json.dumps({
                    "type": "hello",
                    "device_id": device_id,
                    "address": _get_local_ip(),
                }))

                # Schedule periodic diagnostics
                async def diag_loop():
                    nonlocal seq
                    while True:
                        diag = collect_diagnostics()
                        await ws.send(json.dumps({
                            "type": "diagnostics",
                            "seq": seq,
                            "data": diag,
                        }))
                        seq += 1
                        await asyncio.sleep(DIAG_INTERVAL)

                diag_task = asyncio.ensure_future(diag_loop())

                try:
                    async for raw in ws:
                        msg = json.loads(raw)
                        await _handle_server_message(ws, msg)
                finally:
                    diag_task.cancel()

        except Exception as exc:
            console.print(f"[yellow]WS disconnected:[/yellow] {exc}. Reconnecting in {reconnect_delay}s...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)


def _get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


async def _handle_server_message(ws, msg: dict) -> None:
    msg_type = msg.get("type")

    if msg_type == "config_update":
        config = msg.get("config", {})
        console.print(f"[cyan]Config update received:[/cyan] {list(config.keys())}")
        try:
            from .applier import apply_config
            apply_config(config)
            await ws.send(json.dumps({"type": "command_result", "result": {"success": True, "action": "config_update"}}))
        except Exception as exc:
            await ws.send(json.dumps({"type": "command_result", "result": {"success": False, "error": str(exc)}}))

    elif msg_type == "command":
        cmd_id = msg.get("command_id", "?")
        action = msg.get("action")
        console.print(f"[cyan]Command:[/cyan] {action} (id={cmd_id})")

        result: dict = {"success": False, "action": action}
        try:
            if action == "run_command":
                cmd = msg.get("command", "")
                timeout = msg.get("timeout", 30)
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                result = {
                    "success": proc.returncode == 0,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[:2000],
                    "stderr": proc.stderr[:500],
                    "action": action,
                }

            elif action == "apply_profile":
                from .hardware.applier import apply_hardware_profile
                errors = apply_hardware_profile(msg.get("profile_id", ""))
                result = {"success": not errors, "errors": errors, "action": action}

            elif action == "reboot":
                delay = msg.get("delay_secs", 5)
                await ws.send(json.dumps({"type": "command_result", "command_id": cmd_id, "result": {"success": True, "action": "reboot"}}))
                await asyncio.sleep(1)
                subprocess.Popen(f"sleep {delay} && sudo reboot", shell=True)
                return

            elif action == "restart_service":
                svc = msg.get("service", "")
                proc = subprocess.run(["sudo", "systemctl", "restart", svc], capture_output=True)
                result = {"success": proc.returncode == 0, "service": svc, "action": action}

            else:
                result = {"success": False, "error": f"Unknown action: {action}"}

        except Exception as exc:
            result = {"success": False, "error": str(exc), "action": action}

        await ws.send(json.dumps({
            "type": "command_result",
            "command_id": cmd_id,
            "result": result,
        }))

    elif msg_type == "ping":
        await ws.send(json.dumps({"type": "pong"}))

    elif msg_type == "welcome":
        console.print(f"[green]v[/green] Connected to MeshPi host: [bold]{msg.get('host')}[/bold]")


# ─────────────────────────────────────────────────────────────────────────────
# Public entry points
# ─────────────────────────────────────────────────────────────────────────────

def run_scan(manual_host: Optional[str] = None, port: int = DEFAULT_PORT, dry_run: bool = False) -> None:
    """Initial scan: discover host, download config, apply."""
    if manual_host:
        hosts = [HostInfo(name=manual_host, address=manual_host, port=port)]
    else:
        hosts = discover_hosts()

    if not hosts:
        console.print("[red]x[/red] No MeshPi hosts found. Is 'meshpi host' running?")
        return

    selected = _select_host(hosts)
    if not selected:
        return

    try:
        config = fetch_and_apply_config(selected, apply=not dry_run)
        if dry_run:
            console.print("\n[yellow]Dry-run:[/yellow] config NOT applied")
            for k, v in config.items():
                is_secret = any(x in k.lower() for x in ["password", "key", "secret"])
                console.print(f"  [dim]{k}[/dim] = {'****' if is_secret else v}")
    except Exception as exc:
        console.print(f"[red]x[/red] Failed: {exc}")


def run_daemon(manual_host: Optional[str] = None, port: int = DEFAULT_PORT) -> None:
    """
    After initial scan, run persistent WebSocket daemon.
    Pushes diagnostics every 60s, handles live commands from host.
    """
    if manual_host:
        hosts = [HostInfo(name=manual_host, address=manual_host, port=port)]
    else:
        hosts = discover_hosts()

    if not hosts:
        console.print("[red]x[/red] No MeshPi host found.")
        return

    selected = _select_host(hosts)
    if not selected:
        return

    device_id = socket.gethostname()
    console.print(f"[bold cyan]MeshPi Daemon[/bold cyan] — device_id: [bold]{device_id}[/bold]")
    console.print("[dim]Ctrl+C to stop[/dim]")

    try:
        asyncio.run(_ws_daemon(selected, device_id))
    except KeyboardInterrupt:
        console.print("\n[yellow]Daemon stopped.[/yellow]")
