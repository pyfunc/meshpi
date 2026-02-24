"""
meshpi.cli
==========
Command-line interface.

Usage:
  meshpi config              Interactive config wizard (HOST)
  meshpi host                Start the host service (HOST)
  meshpi scan                Scan and apply config (CLIENT)
  meshpi pendrive export     Export config to USB pendrive (HOST)
  meshpi pendrive seed       Seed pendrive with this RPi's public key (CLIENT)
  meshpi pendrive apply      Apply config from USB pendrive (CLIENT)
"""

from __future__ import annotations

import click
from rich.console import Console

console = Console()

LOGO = """\
[bold cyan]
  _ __ ___   ___  ___| |__  _ __ (_)
 | '_ ` _ \\ / _ \\/ __| '_ \\| '_ \\| |
 | | | | | |  __/\\__ \\ | | | |_) | |
 |_| |_| |_|\\___||___/_| |_| .__/|_|
                            |_|
[/bold cyan][dim]  Zero-touch Raspberry Pi mesh configurator[/dim]
"""


@click.group()
def main():
    """MeshPi – zero-touch Raspberry Pi configuration."""
    console.print(LOGO)


# ---------------------------------------------------------------------------
# meshpi config
# ---------------------------------------------------------------------------

@main.command("config")
@click.option("--update", is_flag=True, default=False, help="Only update fields not already set")
def cmd_config(update: bool):
    """
    \b
    Interactive configuration wizard.
    Run this on the HOST machine to set credentials and WiFi details.
    Stores settings in ~/.meshpi/config.env
    """
    from .config import run_config_wizard
    run_config_wizard(skip_existing=update)


# ---------------------------------------------------------------------------
# meshpi host
# ---------------------------------------------------------------------------

@main.command("host")
@click.option("--port", default=7422, show_default=True, help="TCP port to listen on")
@click.option("--bind", default="0.0.0.0", show_default=True, help="Bind address")
def cmd_host(port: int, bind: str):
    """
    \b
    Start the MeshPi host service.
    Advertises itself via mDNS and serves encrypted config to clients.

    Run this on the HOST machine AFTER running: meshpi config
    """
    from .host import run_host
    run_host(port=port, bind=bind)


# ---------------------------------------------------------------------------
# meshpi scan
# ---------------------------------------------------------------------------

@main.command("scan")
@click.option("--host", "manual_host", default=None, help="Skip mDNS, connect directly to IP/hostname")
@click.option("--port", default=7422, show_default=True, help="Host port")
@click.option("--dry-run", is_flag=True, default=False, help="Fetch config but do not apply it")
def cmd_scan(manual_host, port, dry_run):
    """
    \b
    Scan for MeshPi hosts and download configuration.
    Run this on a freshly imaged Raspberry Pi (CLIENT).

    The device will auto-configure itself and reboot.
    """
    from .client import run_scan
    run_scan(manual_host=manual_host, port=port, dry_run=dry_run)


# ---------------------------------------------------------------------------
# meshpi pendrive
# ---------------------------------------------------------------------------

@main.group("pendrive")
def cmd_pendrive():
    """USB pendrive-based configuration (offline alternative to network mode)."""
    pass


@cmd_pendrive.command("export")
@click.option("--mount", default=None, help="Pendrive mount point (auto-detect if omitted)")
@click.option("--client-key", default=None, help="Path to client RSA public key (.pem)")
def cmd_pendrive_export(mount, client_key):
    """
    \b
    HOST: Export encrypted config to USB pendrive.
    The pendrive must already contain the client's public key
    (from: meshpi pendrive seed) or supply --client-key.
    """
    from .pendrive import export_to_pendrive
    export_to_pendrive(mount_point=mount, client_pub_key_path=client_key)


@cmd_pendrive.command("seed")
@click.option("--mount", default=None, help="Pendrive mount point (auto-detect if omitted)")
def cmd_pendrive_seed(mount):
    """
    \b
    CLIENT: Write this device's public key to the pendrive.
    Give the pendrive to the HOST machine, which runs: meshpi pendrive export
    """
    from .pendrive import seed_pendrive
    seed_pendrive(mount_point=mount)


@cmd_pendrive.command("apply")
@click.option("--mount", default=None, help="Pendrive mount point (auto-detect if omitted)")
@click.option("--dry-run", is_flag=True, default=False, help="Show config but do not apply")
def cmd_pendrive_apply(mount, dry_run):
    """
    \b
    CLIENT: Read encrypted config from pendrive and apply to this RPi.
    Reboots automatically when done.
    """
    from .pendrive import apply_from_pendrive
    apply_from_pendrive(mount_point=mount, dry_run=dry_run)


# ---------------------------------------------------------------------------
# meshpi info
# ---------------------------------------------------------------------------

@main.command("info")
def cmd_info():
    """Show local meshpi state (keys, config presence)."""
    from pathlib import Path
    from .crypto import MESHPI_DIR

    console.print("[bold]MeshPi state:[/bold]")
    items = {
        "Config dir":      MESHPI_DIR,
        "Host private key": MESHPI_DIR / "host_key.pem",
        "Host public key":  MESHPI_DIR / "host_key_pub.pem",
        "Client private key": MESHPI_DIR / "client_key.pem",
        "Client public key":  MESHPI_DIR / "client_key_pub.pem",
        "Config env":       MESHPI_DIR / "config.env",
    }
    for label, path in items.items():
        exists = Path(path).exists()
        status = "[green]✓[/green]" if exists else "[dim]—[/dim]"
        console.print(f"  {status} {label}: [dim]{path}[/dim]")
