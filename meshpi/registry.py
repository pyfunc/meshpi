"""
meshpi.registry
===============
In-memory (+ JSON persistence) registry of connected MeshPi clients.
Used by the host server to track devices, push config updates,
receive diagnostics, and issue commands in real time.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Optional


REGISTRY_PATH = Path.home() / ".meshpi" / "registry.json"


@dataclass
class DeviceRecord:
    device_id: str               # hostname or generated UUID
    address: str                 # last seen IP
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    last_diagnostics: dict = field(default_factory=dict)
    applied_profiles: list[str] = field(default_factory=list)
    config_version: int = 0
    notes: str = ""
    online: bool = False
    websocket_id: Optional[str] = None   # active WS connection id

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DeviceRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class DeviceRegistry:
    """Thread-safe registry of known MeshPi client devices."""

    def __init__(self) -> None:
        self._devices: dict[str, DeviceRecord] = {}
        self._lock = Lock()
        self._load()

    def _load(self) -> None:
        if REGISTRY_PATH.exists():
            try:
                data = json.loads(REGISTRY_PATH.read_text())
                for dev_id, rec in data.items():
                    self._devices[dev_id] = DeviceRecord.from_dict(rec)
            except Exception:
                pass

    def _save(self) -> None:
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {dev_id: rec.to_dict() for dev_id, rec in self._devices.items()}
        REGISTRY_PATH.write_text(json.dumps(data, indent=2))

    def register(self, device_id: str, address: str) -> DeviceRecord:
        with self._lock:
            if device_id in self._devices:
                rec = self._devices[device_id]
                rec.address = address
                rec.last_seen = time.time()
                rec.online = True
            else:
                rec = DeviceRecord(device_id=device_id, address=address)
                self._devices[device_id] = rec
            self._save()
            return rec

    def mark_offline(self, device_id: str) -> None:
        with self._lock:
            if device_id in self._devices:
                self._devices[device_id].online = False
                self._devices[device_id].websocket_id = None
                self._save()

    def update_diagnostics(self, device_id: str, diag: dict) -> None:
        with self._lock:
            if device_id in self._devices:
                self._devices[device_id].last_diagnostics = diag
                self._devices[device_id].last_seen = time.time()
                self._save()

    def set_websocket_id(self, device_id: str, ws_id: Optional[str]) -> None:
        with self._lock:
            if device_id in self._devices:
                self._devices[device_id].websocket_id = ws_id
                self._devices[device_id].online = ws_id is not None
                self._save()

    def add_profile(self, device_id: str, profile_id: str) -> None:
        with self._lock:
            if device_id in self._devices:
                if profile_id not in self._devices[device_id].applied_profiles:
                    self._devices[device_id].applied_profiles.append(profile_id)
                self._save()

    def set_note(self, device_id: str, note: str) -> None:
        with self._lock:
            if device_id in self._devices:
                self._devices[device_id].notes = note
                self._save()

    def get(self, device_id: str) -> Optional[DeviceRecord]:
        return self._devices.get(device_id)

    def all_devices(self) -> list[DeviceRecord]:
        return list(self._devices.values())

    def online_devices(self) -> list[DeviceRecord]:
        return [d for d in self._devices.values() if d.online]

    def remove(self, device_id: str) -> bool:
        with self._lock:
            if device_id in self._devices:
                del self._devices[device_id]
                self._save()
                return True
            return False


# Global singleton
registry = DeviceRegistry()
