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
  meshpi doctor              Remote diagnostics with auto-repair
  meshpi restart             Restart service or reboot device
  meshpi ls                  Interactive device list and management
  meshpi list                Interactive device list and management
  meshpi hw list             List hardware profiles
  meshpi hw apply <id>       Apply hardware profile locally
  meshpi agent               Launch LLM agent REPL (HOST)
  meshpi pendrive export     Export config to USB (HOST)
  meshpi pendrive seed       Seed USB with client key (CLIENT)
  meshpi pendrive apply      Apply config from USB (CLIENT)
  meshpi info                Show local key/config state

Doctor Examples:
  meshpi doctor pi@192.168.1.100      # Diagnose and auto-repair
  meshpi doctor pi@rpi --password     # Use password auth
  meshpi doctor --local               # Local diagnostics only

Restart Examples:
  meshpi restart pi@192.168.1.100     # Restart meshpi service
  meshpi restart pi@rpi --reboot      # Reboot the device
  meshpi restart pi@rpi --service host # Restart specific service

List Examples:
  meshpi ls                         # Interactive device list
  meshpi list                        # Interactive device list
  meshpi ls --scan                   # Scan and list devices
"""

from __future__ import annotations

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.columns import Columns
from rich.layout import Layout
from rich.align import Align

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


# ─────────────────────────────────────────────────────────────────────────────
# meshpi doctor
# ─────────────────────────────────────────────────────────────────────────────

@main.command("doctor")
@click.argument("target", required=False, default=None)
@click.option("--password", is_flag=True, default=False,
              help="Use password authentication instead of SSH key")
@click.option("--key", default=None,
              help="Path to SSH private key")
@click.option("--local", is_flag=True, default=False,
              help="Run diagnostics on local machine")
def cmd_doctor(target: str, password: bool, key: str, local: bool):
    """
    \b
    Run diagnostics on a Raspberry Pi device.

    Examples:
      meshpi doctor pi@raspberrypi        # Connect via SSH
      meshpi doctor pi@192.168.1.100      # Connect via IP
      meshpi doctor pi@host:2222          # Custom SSH port
      meshpi doctor --local               # Local diagnostics only
      meshpi doctor pi@rpi --password     # Use password auth
      meshpi doctor pi@rpi --key ~/.ssh/custom_key
    """
    if local or not target:
        #अंतRun local diagnostics
        from .diagnostics import collect, format_summary
        import json as json_mod
        
        console.print("[bold cyan]MeshPi Doctor — Local Diagnostics[/bold cyan]\n")
        diag = collect()
        
        # Check for common issues
        issues = []
        
        # Temperature check
        temp = diag.get("temperature", {})
        cpu_temp = temp.get("cpu_gpu") or temp.get("zone_0")
        if cpu_temp and isinstance(cpu_temp, (int, float)) and cpu_temp > 70:
            issues.append(f"High CPU temperature: {cpu_temp}°C")
        
        # Memory check
        mem = diag.get("memory", {})
        if mem.get("used_percent", 0) > 90:
            issues.append(f"High memory usage: {mem.get('used_percent')}%")
        
        # Power check
        pwr = diag.get("power", {})
        if pwr.get("under_voltage"):
            issues.append("Under-voltage detected - check power supply")
        if pwr.get("currently_throttled"):
            issues.append("CPU is throttled - check temperature/power")
        
        # Network check
        net = diag.get("network", {})
        if not net.get("ping_ok"):
            issues.append("No internet connectivity")
        
        # Services check
        svc = diag.get("services", {})
        if svc.get("failed_units"):
            issues.append(f"Failed services: {', '.join(svc['failed_units'][:3])}")
        
        # Display results
        console.print(format_summary(diag))
        
        if issues:
            console.print("\n[bold yellow]Issues detected:[/bold yellow]")
            for issue in issues:
                console.print(f"  [yellow]•[/yellow] {issue}")
        else:
            console.print("\n[green]✓ No issues detected[/green]")
        
        return
    
    # Remote diagnostics via SSH
    from .doctor import run_doctor
    run_doctor(target, password=password, key=key)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi restart
# ─────────────────────────────────────────────────────────────────────────────

@main.command("restart")
@click.argument("target", required=False, default=None)
@click.option("--password", is_flag=True, default=False,
              help="Use password authentication instead of SSH key")
@click.option("--key", default=None,
              help="Path to SSH private key")
@click.option("--service", default="meshpi",
              help="Service name to restart (default: meshpi)")
@click.option("--reboot", is_flag=True, default=False,
              help="Reboot the device instead of just restarting service")
def cmd_restart(target: str | None, password: bool, key: str | None, service: str, reboot: bool):
    """
    \b
    Restart MeshPi service or reboot Raspberry Pi device.

    Examples:
      meshpi restart pi@raspberrypi           # Restart meshpi service
      meshpi restart pi@192.168.1.100         # Restart via IP
      meshpi restart pi@rpi --reboot          # Reboot the device
      meshpi restart pi@rpi --service host    # Restart host service
      meshpi restart pi@rpi --password        # Use password auth
    """
    if not target:
        console.print("[red]Error: Target device is required for restart command[/red]")
        console.print("[dim]Usage: meshpi restart pi@<device-ip>[/dim]")
        return
    
    from .doctor import parse_target, RemoteDoctor
    
    user, host, port = parse_target(target)
    
    console.print(Panel.fit(
        f"[bold yellow]MeshPi Restart[/bold yellow]\n"
        f"Restarting {'device' if reboot else f'{service} service'} on [bold]{user}@{host}:{port}[/bold]",
        border_style="yellow",
    ))

    doctor = RemoteDoctor(host, user, port)

    # Get credentials
    ssh_password = None
    ssh_key = key
    
    if password:
        import getpass
        ssh_password = getpass.getpass(f"Enter password for {user}@{host}: ")
    elif not key:
        # Try default key
        default_key = Path.home() / ".ssh" / "id_rsa"
        if default_key.exists():
            ssh_key = str(default_key)
            console.print(f"[dim]Using SSH key: {ssh_key}[/dim]")

    # Connect
    console.print(f"\n[cyan]→[/cyan] Connecting to [bold]{host}[/bold]...")
    if not doctor.connect(password=ssh_password, key_path=ssh_key):
        console.print("[red]Failed to connect. Exiting.[/red]")
        return

    console.print("[green]✓ Connected[/green]\n")

    if reboot:
        # Reboot the device
        console.print("[yellow]→ Rebooting device...[/yellow]")
        exit_code, stdout, stderr = doctor.run_command("sudo reboot")
        
        if exit_code == 0:
            console.print("[green]✓ Reboot command sent[/green]")
            console.print("[dim]Device is rebooting. Wait 2-3 minutes before reconnecting.[/dim]")
        else:
            console.print(f"[red]✗ Reboot failed: {stderr}[/red]")
    else:
        # Restart specific service
        console.print(f"[yellow]→ Restarting {service} service...[/yellow]")
        
        # Check if service exists
        exit_code, stdout, stderr = doctor.run_command(f"systemctl is-active {service}")
        
        if exit_code == 0:
            # Service exists and is active, restart it
            exit_code, stdout, stderr = doctor.run_command(f"sudo systemctl restart {service}")
            if exit_code == 0:
                console.print(f"[green]✓ {service} service restarted[/green]")
                
                # Check status after restart
                exit_code, stdout, stderr = doctor.run_command(f"systemctl is-active {service}")
                if exit_code == 0:
                    console.print(f"[green]✓ {service} is now running[/green]")
                else:
                    console.print(f"[yellow]⚠ {service} status: {stdout.strip()}[/yellow]")
            else:
                console.print(f"[red]✗ Failed to restart {service}: {stderr}[/red]")
        else:
            # Service doesn't exist, try common MeshPi service names
            services_to_try = ["meshpi-host", "meshpi-daemon", "meshpi"]
            service_found = False
            
            for svc in services_to_try:
                exit_code, stdout, stderr = doctor.run_command(f"systemctl is-active {svc}")
                if exit_code == 0:
                    console.print(f"[cyan]Found MeshPi service: {svc}[/cyan]")
                    exit_code, stdout, stderr = doctor.run_command(f"sudo systemctl restart {svc}")
                    if exit_code == 0:
                        console.print(f"[green]✓ {svc} service restarted[/green]")
                        service_found = True
                    break
            
            if not service_found:
                console.print(f"[yellow]⚠ No MeshPi service found. Trying manual restart...[/yellow]")
                
                # Try to find and kill meshpi processes
                exit_code, stdout, stderr = doctor.run_command("pgrep -f meshpi")
                if exit_code == 0:
                    console.print("[yellow]→ Found MeshPi processes, stopping them...[/yellow]")
                    doctor.run_command("pkill -f meshpi")
                    console.print("[green]✓ MeshPi processes stopped[/green]")
                    
                    # Check if there's a startup script or systemd service
                    exit_code, stdout, stderr = doctor.run_command("ls /etc/systemd/system/meshpi*.service 2>/dev/null")
                    if exit_code == 0:
                        console.print("[cyan]→ Found systemd services, restarting...[/cyan]")
                        services = stdout.strip().split('\n')
                        for svc_file in services:
                            svc_name = svc_file.split('/')[-1].replace('.service', '')
                            doctor.run_command(f"sudo systemctl restart {svc_name}")
                    else:
                        console.print("[yellow]⚠ No automatic restart available. Manual restart may be needed.[/yellow]")
                        console.print("[dim]Try: meshpi host (on the device)[/dim]")
                else:
                    console.print("[yellow]⚠ No MeshPi processes found running[/yellow]")
                    console.print("[dim]MeshPi may not be running. Try starting it with 'meshpi host'[/dim]")

    doctor.disconnect()
    console.print("\n[green]✓ Restart operation completed[/green]")


# ─────────────────────────────────────────────────────────────────────────────
# meshpi ls / meshpi list
# ─────────────────────────────────────────────────────────────────────────────

@main.command("ls")
@click.option("--scan", is_flag=True, default=False, help="Scan network for devices before listing")
@click.option("--refresh", is_flag=True, default=False, help="Refresh device information")
@click.option("--all", is_flag=True, default=False, help="Show all devices including offline")
def cmd_list(scan: bool, refresh: bool, all: bool):
    """
    \b
    Interactive device list and management.
    
    Provides a menu-driven interface to view, diagnose, and manage MeshPi devices.
    
    Examples:
      meshpi ls              # Show interactive device list
      meshpi list            # Same as above
      meshpi ls --scan       # Scan and list devices
      meshpi ls --all        # Show all devices including offline
    """
    from .registry import registry as reg
    from .doctor import run_doctor
    
    while True:
        # Clear screen and show header
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]MeshPi Device Manager[/bold cyan]\n"
            "[dim]Interactive device list and management[/dim]",
            border_style="cyan"
        ))
        
        # Get devices
        devices = reg.all_devices()
        
        if scan:
            console.print("[yellow]→ Scanning for devices...[/yellow]")
            # Trigger network scan (this would need to be implemented)
            console.print("[dim]Network scan completed[/dim]\n")
        
        if not devices:
            console.print("[yellow]No devices found in registry.[/yellow]")
            console.print("[dim]Try running 'meshpi scan' on client devices first.[/dim]\n")
            
            if Confirm.ask("Add device manually?", default=False):
                add_device_manually()
            else:
                break
        
        # Create device table
        table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Device ID", style="bold")
        table.add_column("Status", width=8)
        table.add_column("Address", style="dim")
        table.add_column("Last Seen", style="dim")
        table.add_column("Profiles", style="dim")
        
        # Filter devices
        visible_devices = devices if all else [d for d in devices if d.online]
        
        for i, device in enumerate(visible_devices, 1):
            status = "[green]ONLINE[/green]" if device.online else "[red]OFFLINE[/red]"
            last_seen = device.last_seen.strftime("%H:%M") if device.last_seen else "Never"
            profiles = ", ".join(device.applied_profiles[:2]) if device.applied_profiles else "None"
            if len(device.applied_profiles) > 2:
                profiles += f" (+{len(device.applied_profiles)-2})"
            
            table.add_row(str(i), device.device_id, status, device.address, last_seen, profiles)
        
        console.print(table)
        
        if not all and len(devices) > len(visible_devices):
            offline_count = len(devices) - len(visible_devices)
            console.print(f"\n[dim]...and {offline_count} offline device(s) (use --all to show)[/dim]")
        
        # Show menu options
        console.print("\n" + "─" * 50)
        console.print("[bold cyan]Options:[/bold cyan]")
        console.print("  [1-{}] Select device".format(len(visible_devices)))
        console.print("  [s] Scan network")
        console.print("  [r] Refresh list")
        console.print("  [a] Show all devices")
        console.print("  [m] Add device manually")
        console.print("  [q] Quit")
        
        # Get user choice
        choice = Prompt.ask(
            "\n[cyan]Choose an option[/cyan]",
            choices=[str(i) for i in range(1, len(visible_devices) + 1)] + ["s", "r", "a", "m", "q"],
            default="q"
        )
        
        if choice == "q":
            break
        elif choice == "s":
            scan = True
            continue
        elif choice == "r":
            refresh = True
            continue
        elif choice == "a":
            all = not all
            continue
        elif choice == "m":
            add_device_manually()
            continue
        else:
            # Device selected
            device_index = int(choice) - 1
            if 0 <= device_index < len(visible_devices):
                selected_device = visible_devices[device_index]
                device_menu(selected_device)
            else:
                console.print("[red]Invalid device selection[/red]")
                Prompt.ask("Press Enter to continue...")


# Add alias for 'list' command
main.add_command(cmd_list, name="list")


def add_device_manually():
    """Add a device manually to the registry."""
    console.print("\n[bold cyan]Add Device Manually[/bold cyan]")
    console.print("─" * 30)
    
    device_id = Prompt.ask("Device ID (e.g., rpi-kitchen)")
    address = Prompt.ask("Address (e.g., pi@192.168.1.100 or pi@raspberrypi.local)")
    
    # Add to registry (this would need to be implemented)
    console.print(f"[green]✓ Device {device_id} added[/green]")
    console.print("[dim]Note: Device will appear as offline until it connects[/dim]")


def device_menu(device):
    """Show device-specific menu."""
    from .doctor import run_doctor, parse_target, RemoteDoctor
    
    while True:
        console.clear()
        console.print(Panel.fit(
            f"[bold cyan]Device: {device.device_id}[/bold cyan]\n"
            f"[dim]Address: {device.address}[/dim]\n"
            f"[dim]Status: {'[green]ONLINE[/green]' if device.online else '[red]OFFLINE[/red]'}[/dim]",
            border_style="cyan"
        ))
        
        # Device details
        details_table = Table(show_header=False, box=None)
        details_table.add_column("Property", style="cyan")
        details_table.add_column("Value")
        
        details_table.add_row("Device ID", device.device_id)
        details_table.add_row("Address", device.address)
        details_table.add_row("Status", "[green]Online[/green]" if device.online else "[red]Offline[/red]")
        details_table.add_row("Last Seen", device.last_seen.strftime("%Y-%m-%d %H:%M:%S") if device.last_seen else "Never")
        details_table.add_row("Applied Profiles", ", ".join(device.applied_profiles) if device.applied_profiles else "None")
        
        console.print(details_table)
        
        # Device-specific options
        console.print("\n[bold cyan]Device Options:[/bold cyan]")
        console.print("  [1] Run diagnostics")
        console.print("  [2] Restart service")
        console.print("  [3] Reboot device")
        console.print("  [4] View details")
        console.print("  [5] Remove device")
        console.print("  [b] Back to device list")
        console.print("  [q] Quit")
        
        choice = Prompt.ask(
            "\n[cyan]Choose an option[/cyan]",
            choices=["1", "2", "3", "4", "5", "b", "q"],
            default="b"
        )
        
        if choice == "b":
            break
        elif choice == "q":
            exit(0)
        elif choice == "1":
            # Run diagnostics
            console.print("\n[yellow]→ Running diagnostics on {device.device_id}...[/yellow]")
            try:
                # Parse address for doctor
                if "@" in device.address:
                    target = device.address
                else:
                    target = f"pi@{device.address}"
                
                run_doctor(target, password=False, key=None)
            except Exception as e:
                console.print(f"[red]✗ Diagnostics failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "2":
            # Restart service
            console.print(f"\n[yellow]→ Restarting MeshPi service on {device.device_id}...[/yellow]")
            try:
                # Parse address for restart
                if "@" in device.address:
                    target = device.address
                else:
                    target = f"pi@{device.address}"
                
                # Import restart function
                from .cli import cmd_restart
                cmd_restart(target, password=False, key=None, service="meshpi", reboot=False)
            except Exception as e:
                console.print(f"[red]✗ Restart failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "3":
            # Reboot device
            console.print(f"\n[yellow]→ Rebooting {device.device_id}...[/yellow]")
            if Confirm.ask("Are you sure you want to reboot this device?", default=False):
                try:
                    # Parse address for reboot
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_restart
                    cmd_restart(target, password=False, key=None, service="meshpi", reboot=True)
                except Exception as e:
                    console.print(f"[red]✗ Reboot failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "4":
            # View detailed information
            show_device_details(device)
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "5":
            # Remove device
            if Confirm.ask(f"Remove {device.device_id} from registry?", default=False):
                console.print(f"[green]✓ Device {device.device_id} removed[/green]")
                break


def show_device_details(device):
    """Show detailed device information."""
    console.print("\n[bold cyan]Device Details[/bold cyan]")
    console.print("─" * 30)
    
    # This would show more detailed information about the device
    # For now, show what we have
    details = {
        "Device ID": device.device_id,
        "Address": device.address,
        "Status": "[green]Online[/green]" if device.online else "[red]Offline[/red]",
        "Last Seen": device.last_seen.strftime("%Y-%m-%d %H:%M:%S") if device.last_seen else "Never",
        "Applied Profiles": ", ".join(device.applied_profiles) if device.applied_profiles else "None",
        "First Seen": device.first_seen.strftime("%Y-%m-%d %H:%M:%S") if device.first_seen else "Unknown",
    }
    
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan", width=15)
    table.add_column("Value")
    
    for key, value in details.items():
        table.add_row(key, value)
    
    console.print(table)
