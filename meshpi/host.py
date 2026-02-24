"""
meshpi.host
===========
MeshPi host service — FastAPI server with:

  REST endpoints:
    GET  /info              → host public key + metadata
    POST /config            → encrypted config delivery (initial setup)
    GET  /health

  WebSocket:
    WS   /ws/{device_id}   → persistent bidirectional channel per client

  Management REST (host-side admin):
    GET  /devices                    → list all known clients
    GET  /devices/{id}/diagnostics   → latest diagnostics snapshot
    POST /devices/{id}/push_config   → push config updates in real time
    POST /devices/{id}/command       → push command (run_command/apply_profile/reboot)
    POST /devices/{id}/note          → set device note
    DELETE /devices/{id}             → remove from registry

WebSocket message protocol (JSON):
  Client -> Host:
    {"type": "hello",       "device_id": "...", "address": "..."}
    {"type": "diagnostics", "data": {...}}
    {"type": "command_result", "command_id": "...", "result": {...}}

  Host -> Client:
    {"type": "config_update", "config": {...}}
    {"type": "command",       "command_id": "...", "action": "...", ...}
    {"type": "ping"}
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import uuid
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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
from .registry import registry
from .dashboard import get_dashboard_html

console = Console()
log = logging.getLogger("meshpi.host")

SERVICE_TYPE = "_meshpi._tcp.local."
DEFAULT_PORT = 7422


# ---- WebSocket connection manager ------------------------------------------

class WebSocketManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, device_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[device_id] = ws
        registry.set_websocket_id(device_id, str(id(ws)))
        console.print(f"  [green]WS connected:[/green] [bold]{device_id}[/bold]")

    async def disconnect(self, device_id: str) -> None:
        self._connections.pop(device_id, None)
        registry.mark_offline(device_id)
        console.print(f"  [yellow]WS disconnected:[/yellow] [bold]{device_id}[/bold]")

    async def send(self, device_id: str, message: dict) -> bool:
        ws = self._connections.get(device_id)
        if not ws:
            return False
        try:
            await ws.send_text(json.dumps(message))
            return True
        except Exception:
            await self.disconnect(device_id)
            return False

    async def broadcast(self, message: dict, device_ids: list[str] | None = None) -> dict[str, bool]:
        targets = device_ids or list(self._connections.keys())
        return {did: await self.send(did, message) for did in targets}

    def push_config_update(self, device_ids: list[str], updates: dict) -> dict:
        """Sync wrapper used by LLM agent tool executor."""
        try:
            loop = asyncio.get_running_loop()
            fut = asyncio.ensure_future(
                self.broadcast({"type": "config_update", "config": updates}, device_ids)
            )
            return {"pushed_to": device_ids, "queued": True}
        except RuntimeError:
            return {"pushed_to": device_ids, "status": "no_event_loop"}

    def push_command(self, device_id: str, command_payload: dict) -> dict:
        cmd_id = str(uuid.uuid4())[:8]
        msg = {"type": "command", "command_id": cmd_id, **command_payload}
        try:
            asyncio.ensure_future(self.send(device_id, msg))
            return {"command_id": cmd_id, "delivered": True}
        except RuntimeError:
            return {"command_id": cmd_id, "delivered": False}

    @property
    def online_ids(self) -> list[str]:
        return list(self._connections.keys())


ws_manager = WebSocketManager()


# ---- FastAPI ----------------------------------------------------------------

app = FastAPI(title="MeshPi Host", version="0.2.0", docs_url="/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_host_private_key = None
_host_public_key = None
_config: Optional[dict] = None


class ConfigRequest(BaseModel):
    client_public_key_pem: str


@app.get("/info")
async def info():
    return {
        "service":             "meshpi-host",
        "version":             "0.2.0",
        "host_public_key_pem": public_key_to_pem(_host_public_key).decode(),
        "hostname":            socket.gethostname(),
        "online_clients":      ws_manager.online_ids,
    }


@app.post("/config")
async def get_config(req: ConfigRequest):
    try:
        client_pub = public_key_from_pem(req.client_public_key_pem.encode())
    except Exception as exc:
        raise HTTPException(400, detail=f"Invalid public key: {exc}")
    if _config is None:
        raise HTTPException(503, detail="Host config not loaded")
    encrypted = encrypt_config(_config, client_pub)
    return JSONResponse({"payload": encrypted.decode()})


@app.get("/health")
async def health():
    return {"status": "ok", "online_clients": len(ws_manager.online_ids)}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Real-time device management dashboard."""
    return HTMLResponse(content=get_dashboard_html())


# ---- Device management REST ------------------------------------------------

@app.get("/devices")
async def list_devices():
    return [
        {
            "device_id":        d.device_id,
            "address":          d.address,
            "online":           d.online,
            "last_seen":        d.last_seen,
            "applied_profiles": d.applied_profiles,
            "notes":            d.notes,
            "config_version":   d.config_version,
        }
        for d in registry.all_devices()
    ]


@app.get("/devices/{device_id}/diagnostics")
async def get_diagnostics(device_id: str):
    rec = registry.get(device_id)
    if not rec:
        raise HTTPException(404, detail=f"Device '{device_id}' not found")
    return rec.last_diagnostics or {}


class ConfigUpdateRequest(BaseModel):
    config: dict


@app.post("/devices/{device_id}/push_config")
async def push_config_endpoint(device_id: str, req: ConfigUpdateRequest):
    if device_id == "*":
        ids = ws_manager.online_ids
    else:
        ids = [device_id]
    results = await ws_manager.broadcast({"type": "config_update", "config": req.config}, ids)
    return {"pushed_to": ids, "results": results}


class CommandRequest(BaseModel):
    action: str
    command: Optional[str] = None
    profile_id: Optional[str] = None
    service: Optional[str] = None
    delay_secs: int = 5
    timeout: int = 30


@app.post("/devices/{device_id}/command")
async def push_command_endpoint(device_id: str, req: CommandRequest):
    cmd_id = str(uuid.uuid4())[:8]
    msg = {"type": "command", "command_id": cmd_id, **req.model_dump()}
    ok = await ws_manager.send(device_id, msg)
    if not ok:
        raise HTTPException(503, detail=f"Device '{device_id}' not connected")
    return {"command_id": cmd_id, "delivered": True}


class NoteRequest(BaseModel):
    note: str


@app.post("/devices/{device_id}/note")
async def set_note(device_id: str, req: NoteRequest):
    registry.set_note(device_id, req.note)
    return {"ok": True}


@app.delete("/devices/{device_id}")
async def remove_device(device_id: str):
    removed = registry.remove(device_id)
    return {"removed": removed}


# ---- WebSocket endpoint ----------------------------------------------------

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(ws: WebSocket, device_id: str):
    await ws_manager.connect(device_id, ws)
    client_ip = ws.client.host if ws.client else "unknown"
    registry.register(device_id, client_ip)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "hello":
                registry.register(device_id, msg.get("address", client_ip))
                await ws.send_text(json.dumps({"type": "welcome", "host": socket.gethostname()}))

            elif msg_type == "diagnostics":
                registry.update_diagnostics(device_id, msg.get("data", {}))
                await ws.send_text(json.dumps({"type": "ack", "seq": msg.get("seq")}))

            elif msg_type == "command_result":
                result = msg.get("result", {})
                console.print(
                    f"  [green]cmd_result[/green] {device_id} "
                    f"#{msg.get('command_id')}: "
                    f"{'OK' if result.get('success') else 'FAIL'}"
                )

            elif msg_type == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))

            elif msg_type == "log":
                level = msg.get("level", "info").upper()
                console.print(f"  [dim][{device_id}][/dim] {level}: {msg.get('message', '')}")

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(device_id)


# ---- mDNS ------------------------------------------------------------------

def _get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def _advertise_mdns(port: int) -> Zeroconf:
    hostname = socket.gethostname()
    ip_bytes = socket.inet_aton(_get_local_ip())
    info = ServiceInfo(
        type_=SERVICE_TYPE,
        name=f"{hostname}.{SERVICE_TYPE}",
        addresses=[ip_bytes],
        port=port,
        properties={b"version": b"0.2.0", b"host": hostname.encode()},
        server=f"{hostname}.local.",
    )
    zc = Zeroconf()
    zc.register_service(info)
    console.print(f"[cyan]mDNS:[/cyan] [bold]{hostname}.{SERVICE_TYPE}[/bold]")
    return zc


# ---- Entry point -----------------------------------------------------------

def run_host(port: int = DEFAULT_PORT, bind: str = "0.0.0.0", with_agent: bool = False) -> None:
    global _host_private_key, _host_public_key, _config

    _host_private_key, _host_public_key = get_or_create_host_keys()
    console.print("[green]v[/green] Host RSA key pair ready")

    try:
        _config = load_config()
        console.print(f"[green]v[/green] Config loaded ({len(_config)} fields)")
    except FileNotFoundError as exc:
        console.print(f"[red]x[/red] {exc}")
        return

    local_ip = _get_local_ip()
    console.print(f"\n[bold cyan]MeshPi Host v0.2[/bold cyan]")
    console.print(f"  API:       http://{local_ip}:{port}/docs")
    console.print(f"  Dashboard: http://{local_ip}:{port}/dashboard")
    console.print(f"  Devices:   http://{local_ip}:{port}/devices")
    console.print(f"  WS:        ws://{local_ip}:{port}/ws/{{device_id}}")
    console.print("[dim]Ctrl+C to stop[/dim]\n")

    zc = _advertise_mdns(port)

    if with_agent:
        import threading
        from .llm_agent import run_agent_repl
        threading.Thread(target=run_agent_repl, args=(ws_manager,), daemon=True).start()

    try:
        uvicorn.run(app, host=bind, port=port, log_level="error")
    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[yellow]Shutting down...[/yellow]")
        zc.unregister_all_services()
        zc.close()
        console.print("[green]v[/green] Stopped")
