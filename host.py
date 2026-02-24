"""
meshpi.host
===========
Runs the MeshPi configuration HOST service.

- Advertises itself on the local network via mDNS (Zeroconf) as _meshpi._tcp
- Exposes a FastAPI endpoint that:
    1. Accepts the client's RSA public key
    2. Returns the host's RSA public key (for trust verification)
    3. Returns the encrypted configuration payload
"""

from __future__ import annotations

import json
import logging
import socket
import threading
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rich.console import Console
from zeroconf import ServiceInfo, Zeroconf

from .config import load_config
from .crypto import (
    encrypt_config,
    get_or_create_host_keys,
    public_key_from_pem,
    public_key_to_pem,
)

console = Console()
log = logging.getLogger("meshpi.host")

SERVICE_TYPE = "_meshpi._tcp.local."
DEFAULT_PORT = 7422


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="MeshPi Host", version="0.1.0", docs_url=None, redoc_url=None)

_host_private_key = None
_host_public_key = None
_config: Optional[dict] = None


class ConfigRequest(BaseModel):
    client_public_key_pem: str   # PEM-encoded client RSA public key


@app.get("/info")
async def info():
    """Return host public key and basic info for trust verification."""
    return {
        "service": "meshpi-host",
        "version": "0.1.0",
        "host_public_key_pem": public_key_to_pem(_host_public_key).decode(),
        "hostname": socket.gethostname(),
    }


@app.post("/config")
async def get_config(req: ConfigRequest):
    """
    Client POSTs its RSA public key.
    Host returns the config encrypted with that key.
    """
    try:
        client_pub = public_key_from_pem(req.client_public_key_pem.encode())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid public key: {exc}")

    if _config is None:
        raise HTTPException(status_code=503, detail="Host config not loaded yet")

    encrypted = encrypt_config(_config, client_pub)
    return JSONResponse({"payload": encrypted.decode()})


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# mDNS advertisement
# ---------------------------------------------------------------------------

def _advertise_mdns(port: int) -> Zeroconf:
    hostname = socket.gethostname()
    local_ip = _get_local_ip()
    ip_bytes = socket.inet_aton(local_ip)

    info = ServiceInfo(
        type_=SERVICE_TYPE,
        name=f"{hostname}.{SERVICE_TYPE}",
        addresses=[ip_bytes],
        port=port,
        properties={
            b"version": b"0.1.0",
            b"host": hostname.encode(),
        },
        server=f"{hostname}.local.",
    )

    zc = Zeroconf()
    zc.register_service(info)
    console.print(f"[cyan]📡 mDNS:[/cyan] Advertised as [bold]{hostname}.{SERVICE_TYPE}[/bold]")
    return zc


def _get_local_ip() -> str:
    """Best-effort local IP detection."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_host(port: int = DEFAULT_PORT, bind: str = "0.0.0.0") -> None:
    global _host_private_key, _host_public_key, _config

    # Load keys
    _host_private_key, _host_public_key = get_or_create_host_keys()
    console.print("[green]✓[/green] Host RSA key pair ready")

    # Load configuration
    try:
        _config = load_config()
        console.print(f"[green]✓[/green] Loaded config with [bold]{len(_config)}[/bold] fields")
    except FileNotFoundError as exc:
        console.print(f"[red]✗[/red] {exc}")
        return

    local_ip = _get_local_ip()

    console.print(f"\n[bold cyan]MeshPi Host[/bold cyan] starting on [bold]{local_ip}:{port}[/bold]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    # Start mDNS in background thread
    zc = _advertise_mdns(port)

    try:
        uvicorn.run(
            app,
            host=bind,
            port=port,
            log_level="error",
        )
    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[yellow]Shutting down mDNS advertisement…[/yellow]")
        zc.unregister_all_services()
        zc.close()
        console.print("[green]✓[/green] Host stopped cleanly")
