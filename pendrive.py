"""
meshpi.pendrive
===============
Alternative to network-based config delivery:
  - HOST: exports encrypted config bundle to a USB pendrive
  - CLIENT: reads config from mounted pendrive and applies it

File layout on pendrive:
  /meshpi/
    config.enc        ← AES-encrypted config (session key wrapped in RPi's pub key)
    rpi_key_pub.pem   ← RPi's RSA public key (generated at package install time)
    host_pub.pem      ← Host RSA public key (for optional trust verification)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt

from .applier import apply_config
from .config import load_config
from .crypto import (
    decrypt_config,
    encrypt_config,
    get_or_create_client_keys,
    get_or_create_host_keys,
    load_public_key,
    public_key_to_pem,
    save_public_key,
)

console = Console()

PENDRIVE_DIR_NAME = "meshpi"
CONFIG_FILE = "config.enc"
HOST_PUB_FILE = "host_pub.pem"
CLIENT_PUB_FILE = "rpi_key_pub.pem"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_pendrive_mounts() -> list[Path]:
    """Detect likely USB mount points (Linux)."""
    candidates: list[Path] = []
    for base in [Path("/media"), Path("/mnt")]:
        if base.exists():
            for child in base.iterdir():
                if child.is_dir():
                    for sub in (list(child.iterdir()) or [child]):
                        if (sub / PENDRIVE_DIR_NAME).exists() or sub == child:
                            candidates.append(sub)
    return candidates


def _select_mount(candidates: list[Path]) -> Optional[Path]:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    console.print("Multiple mount points found:")
    for i, p in enumerate(candidates, 1):
        console.print(f"  {i}. {p}")
    choice = Prompt.ask("Select", choices=[str(i) for i in range(1, len(candidates) + 1)])
    return candidates[int(choice) - 1]


# ---------------------------------------------------------------------------
# HOST: export config to pendrive
# ---------------------------------------------------------------------------

def export_to_pendrive(mount_point: Optional[str] = None, client_pub_key_path: Optional[str] = None) -> None:
    """
    Export encrypted config to pendrive.

    If client_pub_key_path is given, use that public key to encrypt.
    Otherwise the pendrive must already contain rpi_key_pub.pem (pre-seeded by the RPi).
    """
    # Resolve mount point
    if mount_point:
        mount = Path(mount_point)
    else:
        candidates = _find_pendrive_mounts()
        mount = _select_mount(candidates)
        if not mount:
            console.print("[red]✗[/red] No pendrive mount found. Plug in USB and try again.")
            return

    pendrive_dir = mount / PENDRIVE_DIR_NAME
    pendrive_dir.mkdir(parents=True, exist_ok=True)

    # Load host keys and config
    host_priv, host_pub = get_or_create_host_keys()
    config = load_config()

    # Determine client public key
    if client_pub_key_path:
        client_pub = load_public_key(Path(client_pub_key_path))
    else:
        client_pub_file = pendrive_dir / CLIENT_PUB_FILE
        if not client_pub_file.exists():
            console.print(
                "[red]✗[/red] No client public key found on pendrive.\n"
                "Either seed the RPi first with [bold]meshpi pendrive seed[/bold] "
                "or supply [bold]--client-key[/bold]."
            )
            return
        client_pub = load_public_key(client_pub_file)

    # Encrypt config
    encrypted = encrypt_config(config, client_pub)
    (pendrive_dir / CONFIG_FILE).write_bytes(encrypted)

    # Save host public key so client can optionally verify
    save_public_key(host_pub, pendrive_dir / HOST_PUB_FILE)

    console.print(f"[green]✓[/green] Encrypted config written to [bold]{pendrive_dir / CONFIG_FILE}[/bold]")


# ---------------------------------------------------------------------------
# CLIENT: seed pendrive with own public key
# ---------------------------------------------------------------------------

def seed_pendrive(mount_point: Optional[str] = None) -> None:
    """
    Write client's RSA public key to pendrive so host can encrypt config for it.
    Run this on the RPi BEFORE giving the pendrive to the host machine.
    """
    if mount_point:
        mount = Path(mount_point)
    else:
        candidates = _find_pendrive_mounts()
        mount = _select_mount(candidates)
        if not mount:
            console.print("[red]✗[/red] No pendrive mount found.")
            return

    pendrive_dir = mount / PENDRIVE_DIR_NAME
    pendrive_dir.mkdir(parents=True, exist_ok=True)

    _, client_pub = get_or_create_client_keys()
    save_public_key(client_pub, pendrive_dir / CLIENT_PUB_FILE)

    console.print(
        f"[green]✓[/green] Client public key saved to [bold]{pendrive_dir / CLIENT_PUB_FILE}[/bold]\n"
        "[dim]Give this pendrive to the host machine to encrypt the config.[/dim]"
    )


# ---------------------------------------------------------------------------
# CLIENT: apply config from pendrive
# ---------------------------------------------------------------------------

def apply_from_pendrive(mount_point: Optional[str] = None, dry_run: bool = False) -> None:
    """Read encrypted config from pendrive and apply to this RPi."""
    if mount_point:
        mount = Path(mount_point)
    else:
        candidates = _find_pendrive_mounts()
        mount = _select_mount(candidates)
        if not mount:
            console.print("[red]✗[/red] No pendrive mount found.")
            return

    pendrive_dir = mount / PENDRIVE_DIR_NAME
    enc_file = pendrive_dir / CONFIG_FILE

    if not enc_file.exists():
        console.print(f"[red]✗[/red] No config found at [bold]{enc_file}[/bold]")
        return

    client_priv, _ = get_or_create_client_keys()
    payload = enc_file.read_bytes()

    console.print("[cyan]→[/cyan] Decrypting config from pendrive…")
    config = decrypt_config(payload, client_priv)
    console.print(f"[green]✓[/green] Decrypted [bold]{len(config)}[/bold] fields")

    if dry_run:
        console.print("[yellow]Dry-run: not applying[/yellow]")
        for k, v in config.items():
            is_secret = any(x in k.lower() for x in ["password", "key", "secret"])
            console.print(f"  [dim]{k}[/dim] = {'****' if is_secret else v}")
    else:
        apply_config(config)
