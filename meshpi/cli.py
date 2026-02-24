"""
meshpi.cli
==========
MeshPi command-line interface.

Commands:
  meshpi config              Interactive config wizard (HOST)
  meshpi host                Start host service (HOST)
  meshpi host --agent        Start host + LLM agent REPL
  meshpi scan                First-time scan + apply config (CLIENT)
  meshpi daemon              Persistent WS daemon (CLIENT)
  meshpi diag                Show local diagnostics
  meshpi hw list             List hardware profiles
  meshpi hw apply <id>       Apply hardware profile locally
  meshpi agent               Launch LLM agent REPL (HOST)
  meshpi pendrive export     Export config to USB (HOST)
  meshpi pendrive seed       Seed USB with client key (CLIENT)
  meshpi pendrive apply      Apply config from USB (CLIENT)
  meshpi info                Show local key/config state
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

console = Console()

LOGO = """\
[bold cyan]
  _ __ ___   ___  ___| |__  _ __ (_)
 | '_ ` _ \\ / _ \\/ __| '_ \\| '_ \\| |
 | | | | | |  __/\\__ \\ | | | |_) | |
 |_| |_| |_|\\___||___/_| |_| .__/|_|
                            |_|
[/bold cyan][dim]  Zero-touch Raspberry Pi mesh configurator  |  Apache 2.0[/dim]
"""


@click.group()
def main():
    """MeshPi – zero-touch Raspberry Pi fleet configuration."""
    console.print(LOGO)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi config
# ─────────────────────────────────────────────────────────────────────────────

@main.command("config")
@click.option("--update", is_flag=True, default=False, help="Only prompt for fields not yet set")
def cmd_config(update: bool):
    """
    \b
    HOST: Interactive configuration wizard.
    Creates ~/.meshpi/config.env with all device settings.
    """
    from .config import run_config_wizard
    run_config_wizard(skip_existing=update)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi host
# ─────────────────────────────────────────────────────────────────────────────

@main.command("host")
@click.option("--port", default=7422, show_default=True)
@click.option("--bind", default="0.0.0.0", show_default=True)
@click.option("--agent", is_flag=True, default=False,
              help="Also launch the LLM agent REPL in a background thread")
@click.option("--install", is_flag=True, default=False,
              help="Install as systemd service (meshpi-host.service) and exit")
@click.option("--uninstall", is_flag=True, default=False,
              help="Remove meshpi-host.service")
@click.option("--status", is_flag=True, default=False,
              help="Show systemd service status")
def cmd_host(port: int, bind: str, agent: bool, install: bool, uninstall: bool, status: bool):
    """
    \b
    HOST: Start the MeshPi host service.

    Exposes:
      - REST API + Swagger at /docs
      - Real-time dashboard at /dashboard
      - WebSocket endpoint /ws/{device_id}
      - mDNS advertisement (_meshpi._tcp)

    Use --install to auto-start at boot via systemd.
    """
    if install:
        from .systemd import install_host_service
        install_host_service(port=port, with_agent=agent)
        return
    if uninstall:
        from .systemd import uninstall_service
        uninstall_service("meshpi-host")
        return
    if status:
        from .systemd import service_status
        service_status("meshpi-host")
        return
    from .host import run_host
    run_host(port=port, bind=bind, with_agent=agent)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi scan
# ─────────────────────────────────────────────────────────────────────────────

@main.command("scan")
@click.option("--host", "manual_host", default=None,
              help="Skip mDNS, connect directly to IP/hostname")
@click.option("--port", default=7422, show_default=True)
@click.option("--dry-run", is_flag=True, default=False,
              help="Download config but do not apply it")
def cmd_scan(manual_host, port, dry_run):
    """
    \b
    CLIENT: Scan for MeshPi hosts and download/apply configuration.

    On a freshly imaged RPi with factory defaults:
      pip install meshpi && meshpi scan

    Auto-selects the host if only one is found, otherwise shows a menu.
    Reboots the device after applying config.
    """
    from .client import run_scan
    run_scan(manual_host=manual_host, port=port, dry_run=dry_run)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi daemon
# ─────────────────────────────────────────────────────────────────────────────

@main.command("daemon")
@click.option("--host", "manual_host", default=None)
@click.option("--port", default=7422, show_default=True)
@click.option("--install", is_flag=True, default=False,
              help="Install as systemd service (meshpi-daemon.service) and exit")
@click.option("--uninstall", is_flag=True, default=False,
              help="Remove meshpi-daemon.service")
@click.option("--status", is_flag=True, default=False,
              help="Show systemd service status")
def cmd_daemon(manual_host, port, install, uninstall, status):
    """
    \b
    CLIENT: Run persistent WebSocket daemon.

    After initial setup (meshpi scan), run this to maintain a live
    connection to the host for:
      - Periodic diagnostics push (every 60s)
      - Real-time config updates from host
      - Remote command execution (run_command / apply_profile / reboot)

    Use --install to auto-start at boot via systemd:
      meshpi daemon --install
    """
    if install:
        from .systemd import install_daemon_service
        install_daemon_service(host=manual_host, port=port)
        return
    if uninstall:
        from .systemd import uninstall_service
        uninstall_service("meshpi-daemon")
        return
    if status:
        from .systemd import service_status
        service_status("meshpi-daemon")
        return
    from .client import run_daemon
    run_daemon(manual_host=manual_host, port=port)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi diag
# ─────────────────────────────────────────────────────────────────────────────

@main.command("diag")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output raw JSON")
@click.option("--summary", is_flag=True, default=False, help="Compact text summary")
def cmd_diag(as_json: bool, summary: bool):
    """
    \b
    Show diagnostics for this device (CPU, memory, temp, GPIO, I2C, etc.)
    """
    import json as json_mod
    from .diagnostics import collect, format_summary

    console.print("[bold]Collecting diagnostics...[/bold]")
    diag = collect()

    if as_json:
        console.print_json(json_mod.dumps(diag, default=str))
    elif summary:
        console.print(format_summary(diag))
    else:
        _print_diag_rich(diag)


def _print_diag_rich(diag: dict) -> None:
    from rich.panel import Panel

    sys = diag.get("system", {})
    cpu = diag.get("cpu", {})
    mem = diag.get("memory", {})
    temp = diag.get("temperature", {})
    pwr = diag.get("power", {})
    net = diag.get("network", {})
    wifi = diag.get("wifi", {})
    svc = diag.get("services", {})
    i2c = diag.get("i2c", {})

    content = (
        f"[bold]System[/bold]  {sys.get('rpi_model', 'unknown')} | "
        f"OS: {sys.get('os_release', '')} | Kernel: {sys.get('kernel', '')}\n"
        f"  Hostname: {sys.get('hostname')} | "
        f"Uptime: {int(sys.get('uptime_secs', 0)/3600)}h "
        f"{int((sys.get('uptime_secs', 0)%3600)/60)}m\n\n"
        f"[bold]CPU[/bold]     Load: {cpu.get('load_1m')}/{cpu.get('load_5m')}/{cpu.get('load_15m')} | "
        f"Throttled: {pwr.get('currently_throttled')} | "
        f"Under-V: {pwr.get('under_voltage')}\n\n"
        f"[bold]Memory[/bold]  {mem.get('used_percent')}% used "
        f"({mem.get('used_kb',0)//1024} MB / {mem.get('total_kb',0)//1024} MB)\n\n"
        f"[bold]Temp[/bold]    CPU/GPU: {temp.get('cpu_gpu', temp.get('zone_0', 'n/a'))} °C\n\n"
        f"[bold]WiFi[/bold]    SSID: {wifi.get('ssid', 'n/a')} | "
        f"Signal: {wifi.get('signal', 'n/a')} | "
        f"Internet: {'OK' if net.get('ping_ok') else 'FAIL'}\n\n"
        f"[bold]I2C[/bold]     Buses: {i2c.get('buses', [])} | Devices: {i2c.get('devices', {})}\n\n"
        f"[bold]Services[/bold] Failed: {svc.get('failed_units', [])}"
    )
    console.print(Panel(content, title=f"[bold cyan]MeshPi Diagnostics — {sys.get('hostname')}[/bold cyan]",
                         border_style="cyan"))

    if diag.get("logs"):
        console.print("\n[bold red]Recent system errors:[/bold red]")
        for line in diag["logs"][:10]:
            console.print(f"  [dim]{line}[/dim]")


# ─────────────────────────────────────────────────────────────────────────────
# meshpi hw
# ─────────────────────────────────────────────────────────────────────────────

@main.group("hw")
def cmd_hw():
    """Hardware peripheral profiles — list, inspect, apply."""
    pass


@cmd_hw.command("list")
@click.option("--category", "-c", default=None,
              help="Filter by category: display|gpio|sensor|camera|audio|networking|hat|storage")
@click.option("--tag", "-t", default=None, help="Filter by tag (e.g. 'i2c', 'spi', 'oled')")
def cmd_hw_list(category, tag):
    """List all available hardware profiles."""
    from .hardware.profiles import list_profiles

    profiles = list_profiles(category=category, tag=tag)

    table = Table(title="MeshPi Hardware Profiles", border_style="cyan")
    table.add_column("ID",          style="bold cyan", no_wrap=True)
    table.add_column("Category",    style="dim")
    table.add_column("Name")
    table.add_column("Tags",        style="dim")

    for p in profiles:
        table.add_row(p.id, p.category, p.name, ", ".join(p.tags[:4]))

    console.print(table)
    console.print(f"\n[dim]{len(profiles)} profiles[/dim]")


@cmd_hw.command("show")
@click.argument("profile_id")
def cmd_hw_show(profile_id: str):
    """Show details for a specific hardware profile."""
    from .hardware.profiles import get_profile
    from rich.panel import Panel

    try:
        p = get_profile(profile_id)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        return

    content = (
        f"[bold]{p.name}[/bold] ([dim]{p.category}[/dim])\n\n"
        f"{p.description}\n\n"
        f"[bold]Packages:[/bold]       {', '.join(p.packages) or '—'}\n"
        f"[bold]Kernel modules:[/bold] {', '.join(p.kernel_modules) or '—'}\n"
        f"[bold]DT overlays:[/bold]    {', '.join(p.overlays) or '—'}\n"
        f"[bold]config.txt:[/bold]     {'; '.join(p.config_txt_lines) or '—'}\n"
        f"[bold]Post-commands:[/bold]  {len(p.post_commands)} command(s)\n"
        f"[bold]Config keys:[/bold]    {', '.join(p.config_keys) or '—'}\n"
        f"[bold]Tags:[/bold]           {', '.join(p.tags)}"
    )
    console.print(Panel(content, title=f"[cyan]{p.id}[/cyan]", border_style="cyan"))

    if p.post_commands:
        console.print("\n[bold]Post-install commands:[/bold]")
        for cmd in p.post_commands:
            console.print(f"  [dim]$[/dim] {cmd}")


@cmd_hw.command("apply")
@click.argument("profile_ids", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, default=False)
def cmd_hw_apply(profile_ids: tuple, dry_run: bool):
    """
    \b
    Apply one or more hardware profiles to this RPi.

    Example:
      meshpi hw apply oled_ssd1306_i2c sensor_bme280
    """
    from .hardware.applier import apply_multiple_profiles

    if dry_run:
        from .hardware.profiles import get_profile
        console.print("[yellow]Dry-run: showing what would be installed[/yellow]")
        for pid in profile_ids:
            try:
                p = get_profile(pid)
                console.print(f"\n[bold]{p.name}[/bold]")
                if p.packages:      console.print(f"  apt: {', '.join(p.packages)}")
                if p.overlays:      console.print(f"  overlays: {', '.join(p.overlays)}")
                if p.post_commands: console.print(f"  post: {len(p.post_commands)} command(s)")
            except KeyError as exc:
                console.print(f"[red]{exc}[/red]")
        return

    apply_multiple_profiles(list(profile_ids))


# ─────────────────────────────────────────────────────────────────────────────
# meshpi agent
# ─────────────────────────────────────────────────────────────────────────────

@main.command("agent")
@click.option("--model", default=None, envvar="LITELLM_MODEL",
              help="LiteLLM model string (e.g. gpt-4o, claude-3-5-sonnet, ollama/llama3.2)")
@click.option("--api-base", default=None, envvar="LITELLM_API_BASE",
              help="LiteLLM API base URL (for local models)")
def cmd_agent(model, api_base):
    """
    \b
    HOST: Launch the LLM-powered fleet management agent.

    Requires a LiteLLM-compatible API key in the environment:
      OPENAI_API_KEY / ANTHROPIC_API_KEY / LITELLM_API_KEY

    Or use a local model:
      LITELLM_MODEL=ollama/llama3.2 meshpi agent

    Example NLP commands:
      > show me all online devices
      > what's wrong with rpi-kitchen?
      > enable I2C OLED display on rpi-bedroom
      > push the new WiFi password to all devices
      > reboot rpi-garage in 10 seconds
    """
    import os
    if model:
        os.environ["LITELLM_MODEL"] = model
    if api_base:
        os.environ["LITELLM_API_BASE"] = api_base

    from .llm_agent import run_agent_repl
    run_agent_repl()


# ─────────────────────────────────────────────────────────────────────────────
# meshpi pendrive
# ─────────────────────────────────────────────────────────────────────────────

@main.group("pendrive")
def cmd_pendrive():
    """USB pendrive-based offline configuration."""
    pass


@cmd_pendrive.command("export")
@click.option("--mount", default=None)
@click.option("--client-key", default=None)
def cmd_pendrive_export(mount, client_key):
    """HOST: Export encrypted config to USB pendrive."""
    from .pendrive import export_to_pendrive
    export_to_pendrive(mount_point=mount, client_pub_key_path=client_key)


@cmd_pendrive.command("seed")
@click.option("--mount", default=None)
def cmd_pendrive_seed(mount):
    """CLIENT: Write client public key to USB pendrive."""
    from .pendrive import seed_pendrive
    seed_pendrive(mount_point=mount)


@cmd_pendrive.command("apply")
@click.option("--mount", default=None)
@click.option("--dry-run", is_flag=True, default=False)
def cmd_pendrive_apply(mount, dry_run):
    """CLIENT: Read and apply config from USB pendrive."""
    from .pendrive import apply_from_pendrive
    apply_from_pendrive(mount_point=mount, dry_run=dry_run)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi info
# ─────────────────────────────────────────────────────────────────────────────

@main.command("info")
def cmd_info():
    """Show local meshpi state (keys, config, registry)."""
    from pathlib import Path
    from .crypto import MESHPI_DIR
    from .registry import registry as reg

    console.print("[bold]MeshPi local state:[/bold]")

    items = {
        "Config dir":         MESHPI_DIR,
        "Host private key":   MESHPI_DIR / "host_key.pem",
        "Host public key":    MESHPI_DIR / "host_key_pub.pem",
        "Client private key": MESHPI_DIR / "client_key.pem",
        "Client public key":  MESHPI_DIR / "client_key_pub.pem",
        "Config env":         MESHPI_DIR / "config.env",
        "Device registry":    MESHPI_DIR / "registry.json",
    }
    for label, path in items.items():
        exists = Path(path).exists()
        status = "[green]v[/green]" if exists else "[dim]—[/dim]"
        console.print(f"  {status} {label}: [dim]{path}[/dim]")

    devices = reg.all_devices()
    if devices:
        console.print(f"\n[bold]Known devices ({len(devices)}):[/bold]")
        for d in devices:
            status = "[green]ONLINE[/green]" if d.online else "[dim]offline[/dim]"
            console.print(f"  {status} {d.device_id} @ {d.address} | profiles: {d.applied_profiles}")
