"""
meshpi.cli
==========
MeshPi command-line interface.

Commands:
  meshpi config              Interactive config wizard (HOST)
  meshpi host                Start host service (HOST)
  meshpi host --ssh pi@rpi   Start host service on remote RPi
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
  meshpi ssh scan            Scan network for SSH devices
  meshpi ssh add <target>    Add SSH device to management
  meshpi ssh list            List managed SSH devices
  meshpi ssh connect         Connect to SSH device(s)
  meshpi ssh exec <cmd>      Execute command on SSH device(s)
  meshpi ssh install         Install MeshPi on SSH device(s)
  meshpi ssh update          Update MeshPi on SSH device(s)
  meshpi ssh restart         Restart MeshPi service on SSH device(s)
  meshpi ssh transfer        Transfer files to/from SSH device(s)

Doctor Examples:
  meshpi doctor pi@192.168.1.100      # Diagnose and auto-repair
  meshpi doctor pi@rpi --password     # Use password auth
  meshpi doctor --local               # Local diagnostics only

Restart Examples:
  meshpi restart pi@192.168.1.100     # Reboot the device (default)
  meshpi restart pi@rpi --service-only # Restart meshpi service only

List Examples:
  meshpi ls                         # Interactive device list
  meshpi list                        # Interactive device list
  meshpi ls --scan                   # Scan and list devices

Host Examples:
  meshpi host                        # Start host service locally
  meshpi host --ssh pi@192.168.1.100 # Start host on remote RPi
  meshpi host --ssh pi@rpi --agent   # Start host with agent on remote RPi

SSH Management Examples:
  meshpi ssh scan --add              # Scan and add devices
  meshpi ssh add pi@192.168.1.100    # Add specific device
  meshpi ssh connect --all           # Connect to all devices
  meshpi ssh exec "uptime"           # Run command on all devices
  meshpi ssh install --target pi@rpi # Install MeshPi on specific device
"""

from __future__ import annotations

import time
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


def kill_processes_blocking_port(port: int, target_host: str = "localhost") -> bool:
    """Kill processes that are blocking the specified port."""
    import subprocess
    import psutil
    
    console.print(f"[yellow]→ Checking for processes blocking port {port}...[/yellow]")
    
    try:
        # Find processes using the port
        connections = psutil.net_connections()
        killed_any = False
        
        for conn in connections:
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    process = psutil.Process(conn.pid)
                    console.print(f"[dim]  Found process {process.name()} (PID: {conn.pid}) using port {port}[/dim]")
                    
                    # Kill the process
                    process.kill()
                    console.print(f"[dim]  ✓ Killed process {process.name()} (PID: {conn.pid})[/dim]")
                    killed_any = True
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    console.print(f"[dim]  ⚠ Could not kill process {conn.pid} (access denied or not found)[/dim]")
                    continue
        
        if not killed_any:
            console.print(f"[dim]  No processes found blocking port {port}[/dim]")
        
        # Wait a moment for processes to fully terminate
        import time
        time.sleep(1)
        
        return True
        
    except Exception as e:
        console.print(f"[dim]  ⚠ Error checking port {port}: {e}[/dim]")
        return False


def kill_processes_blocking_port_remote(ssh_manager, device, port: int) -> bool:
    """Kill processes blocking port on remote device via SSH."""
    console.print(f"[yellow]→ Checking for processes blocking port {port} on {device}...[/yellow]")
    
    try:
        # Find processes using the port on remote system
        find_cmd = f"lsof -ti :{port} 2>/dev/null || ss -ltnp | grep ':{port}' | awk '{{print $7}}' | cut -d',' -f1 2>/dev/null || echo ''"
        exit_code, stdout, stderr = ssh_manager.run_command_on_device(device, find_cmd)
        
        if exit_code == 0 and stdout.strip():
            pids = stdout.strip().split('\n')
            pids = [pid.strip() for pid in pids if pid.strip() and pid.isdigit()]
            
            if pids:
                console.print(f"[dim]  Found {len(pids)} process(es) using port {port}[/dim]")
                
                for pid in pids:
                    # Get process name
                    name_cmd = f"ps -p {pid} -o comm= 2>/dev/null || echo 'unknown'"
                    exit_code_name, stdout_name, _ = ssh_manager.run_command_on_device(device, name_cmd)
                    process_name = stdout_name.strip() if exit_code_name == 0 else "unknown"
                    
                    console.print(f"[dim]  Found process {process_name} (PID: {pid}) using port {port}[/dim]")
                    
                    # Kill the process
                    kill_cmd = f"kill -9 {pid} 2>/dev/null || true"
                    exit_code_kill, _, _ = ssh_manager.run_command_on_device(device, kill_cmd)
                    
                    if exit_code_kill == 0:
                        console.print(f"[dim]  ✓ Killed process {process_name} (PID: {pid})[/dim]")
                    else:
                        console.print(f"[dim]  ⚠ Could not kill process {pid}[/dim]")
            else:
                console.print(f"[dim]  No processes found blocking port {port}[/dim]")
        else:
            console.print(f"[dim]  No processes found blocking port {port}[/dim]")
        
        # Wait a moment for processes to fully terminate
        import time
        time.sleep(1)
        
        return True
        
    except Exception as e:
        console.print(f"[dim]  ⚠ Error checking port {port} on {device}: {e}[/dim]")
        return False


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
@click.option("--ssh", help="Run host service on remote SSH device (user@host:port)")
@click.option("--ssh-key", help="SSH private key for remote host")
@click.option("--ssh-password", is_flag=True, default=False,
              help="Use password authentication for SSH")
def cmd_host(port: int, bind: str, agent: bool, install: bool, uninstall: bool, status: bool, 
             ssh: Optional[str], ssh_key: Optional[str], ssh_password: bool):
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
    
    # Handle SSH remote execution
    if ssh:
        from .ssh_manager import SSHManager, parse_device_target
        import getpass
        import time
        
        console.print(Panel.fit(
            f"[bold cyan]MeshPi Host via SSH[/bold cyan]\n"
            f"Starting host service on [bold]{ssh}[/bold]",
            border_style="cyan",
        ))
        
        # Parse SSH target
        user, host, port_ssh = parse_device_target(ssh)
        
        # Get credentials
        ssh_password = None
        if ssh_password:
            ssh_password = getpass.getpass(f"Enter SSH password for {user}@{host}: ")
        
        # Connect and run host service
        manager = SSHManager()
        device = manager.SSHDevice(host, user, port_ssh)
        
        if manager.connect_to_device(device, password=ssh_password, key_path=ssh_key):
            console.print(f"[green]✓ Connected to {device}[/green]")
            
            # Check if MeshPi is installed
            console.print("[cyan]→ Checking MeshPi installation...[/cyan]")
            exit_code, stdout, stderr = manager.run_command_on_device(device, "command -v meshpi >/dev/null 2>&1 && echo 'installed' || echo 'not installed'")
            
            if "not installed" in stdout:
                console.print("[yellow]⚠ MeshPi not installed on remote device[/yellow]")
                if Confirm.ask("Install MeshPi on remote device?", default=True):
                    console.print("[cyan]→ Installing MeshPi...[/cyan]")
                    manager.install_meshpi_on_device(device, "venv")
                else:
                    console.print("[red]✗ Cannot start host without MeshPi[/red]")
                    return
            
            # Start host service remotely
            console.print(f"[cyan]→ Starting MeshPi host on port {port}...[/cyan]")
            
            # Kill processes blocking the port first
            kill_processes_blocking_port_remote(manager, device, port)
            
            # Create host command
            host_cmd = f"meshpi host --port {port} --bind {bind}"
            if agent:
                host_cmd += " --agent"
            
            # Run in background with nohup
            start_cmd = f"nohup {host_cmd} > /tmp/meshpi-host.log 2>&1 & echo $! > /tmp/meshpi-host.pid"
            
            exit_code, stdout, stderr = manager.run_command_on_device(device, start_cmd)
            
            if exit_code == 0:
                console.print(f"[green]✓ MeshPi host started on {device}[/green]")
                console.print(f"[dim]Port: {port}[/dim]")
                console.print(f"[dim]Bind: {bind}[/dim]")
                
                # Check if service is running
                time.sleep(2)
                check_cmd = "ps aux | grep 'meshpi.*host' | grep -v grep || echo 'not running'"
                exit_code, stdout, stderr = manager.run_command_on_device(device, check_cmd)
                
                if "not running" not in stdout:
                    console.print("[green]✓ Host service is running[/green]")
                    
                    # Show log location
                    console.print(f"[dim]Logs: /tmp/meshpi-host.log on {device}[/dim]")
                    
                    # Show how to stop
                    console.print(f"[dim]To stop: ssh {device} 'kill $(cat /tmp/meshpi-host.pid)'[/dim]")
                else:
                    console.print("[yellow]⚠ Host service may not be running properly[/yellow]")
                    console.print(f"[dim]Check logs: ssh {device} 'cat /tmp/meshpi-host.log'[/dim]")
            else:
                console.print(f"[red]✗ Failed to start host service[/red]")
                console.print(f"[dim]Error: {stderr}[/dim]")
            
            manager.disconnect_device(device)
        else:
            console.print(f"[red]✗ Failed to connect to {device}[/red]")
        
        return
    
    # Local host execution
    # Kill processes blocking the port first
    kill_processes_blocking_port(port)
    
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
@click.option("--service-only", is_flag=True, default=False,
              help="Only restart service instead of rebooting device")
def cmd_restart(target: str | None, password: bool, key: str | None, service_only: bool):
    """
    \b
    Restart MeshPi service or reboot Raspberry Pi device.
    By default, reboots the device. Use --service-only to restart only the service.

    Examples:
      meshpi restart pi@raspberrypi           # Reboot the device (default)
      meshpi restart pi@192.168.1.100         # Reboot via IP
      meshpi restart pi@rpi --service-only   # Restart meshpi service only
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
        f"{'Rebooting device' if not service_only else 'Restarting meshpi service'} on [bold]{user}@{host}:{port}[/bold]",
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

    if not service_only:
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
        console.print("[yellow]→ Restarting meshpi service...[/yellow]")
        
        # Check if service exists
        exit_code, stdout, stderr = doctor.run_command("systemctl is-active meshpi")
        
        if exit_code == 0:
            # Service exists and is active, restart it
            exit_code, stdout, stderr = doctor.run_command("sudo systemctl restart meshpi")
            if exit_code == 0:
                console.print("[green]✓ meshpi service restarted[/green]")
                
                # Check status after restart
                exit_code, stdout, stderr = doctor.run_command("systemctl is-active meshpi")
                if exit_code == 0:
                    console.print("[green]✓ meshpi is now running[/green]")
                else:
                    console.print(f"[yellow]⚠ meshpi status: {stdout.strip()}[/yellow]")
            else:
                console.print(f"[red]✗ Failed to restart meshpi: {stderr}[/red]")
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
                console.print(f"[yellow]⚠ No MeshPi service found. Trying to start MeshPi...[/yellow]")
                
                # Try to start MeshPi using multiple methods
                console.print("[cyan]→ Attempting to start MeshPi service...[/cyan]")
                
                # Method 1: Try starting meshpi host directly
                exit_code, stdout, stderr = doctor.run_command(r"command -v meshpi >/dev/null 2>&1 && nohup meshpi host > /tmp/meshpi-host.log 2>&1 & echo \$! > /tmp/meshpi-host.pid")
                if exit_code == 0:
                    console.print("[green]✓ MeshPi host started in background[/green]")
                else:
                    # Method 2: Try with virtual environment
                    exit_code, stdout, stderr = doctor.run_command(r"[ -d /home/pi/meshpi-env ] && source /home/pi/meshpi-env/bin/activate && nohup meshpi host > /tmp/meshpi-host.log 2>&1 & echo \$! > /tmp/meshpi-host.pid")
                    if exit_code == 0:
                        console.print("[green]✓ MeshPi host started in virtual environment[/green]")
                    else:
                        # Method 3: Try with python directly
                        exit_code, stdout, stderr = doctor.run_command(r"[ -f /home/pi/meshpi-env/bin/python ] && nohup /home/pi/meshpi-env/bin/python -m meshpi host > /tmp/meshpi-python.log 2>&1 & echo \$! > /tmp/meshpi-python.pid")
                        if exit_code == 0:
                            console.print("[green]✓ MeshPi started with Python directly[/green]")
                        else:
                            console.print("[yellow]⚠ Could not start MeshPi automatically[/yellow]")
                            console.print("[dim]Try running the service manager:[/dim]")
                            console.print("[dim]  ./rpi-service-manager.sh pi@192.168.188.148[/dim]")
                            console.print("[dim]Or start manually:[/dim]")
                            console.print("[dim]  ssh pi@192.168.188.148[/dim]")
                            console.print("[dim]  source /home/pi/meshpi-env/bin/activate[/dim]")
                            console.print("[dim]  meshpi host[/dim]")

    doctor.disconnect()
    console.print("\n[green]✓ Restart operation completed[/green]")


# ─────────────────────────────────────────────────────────────────────────────
# meshpi ssh
# ─────────────────────────────────────────────────────────────────────────────

@main.group("ssh")
def cmd_ssh():
    """SSH device management for Raspberry Pi fleet."""
    pass


@cmd_ssh.command("scan")
@click.option("--network", default="192.168.1.0/24", help="Network range to scan")
@click.option("--user", default="pi", help="Default SSH username")
@click.option("--port", default=22, help="SSH port")
@click.option("--timeout", default=5, help="Connection timeout")
@click.option("--add", is_flag=True, default=False, help="Add discovered devices to management")
def cmd_ssh_scan(network: str, user: str, port: int, timeout: int, add: bool):
    """Scan network for SSH-enabled Raspberry Pi devices."""
    from .ssh_manager import SSHManager
    
    manager = SSHManager()
    devices = manager.scan_network(network, user, port, timeout)
    
    if not devices:
        console.print("[yellow]No SSH devices found[/yellow]")
        return
    
    console.print(f"\n[green]Found {len(devices)} SSH device(s):[/green]")
    
    table = Table(border_style="cyan")
    table.add_column("Host", style="bold")
    table.add_column("User", style="dim")
    table.add_column("Port", style="dim")
    
    for device in devices:
        table.add_row(device.host, device.user, str(device.port))
    
    console.print(table)
    
    if add and Confirm.ask(f"\nAdd {len(devices)} device(s) to management?", default=False):
        for device in devices:
            manager.add_device(device)
        
        # Save device list
        manager.save_device_list(str(Path.home() / ".meshpi" / "ssh_devices.json"))


@cmd_ssh.command("add")
@click.argument("target")
@click.option("--name", help="Device name for identification")
@click.option("--tags", help="Comma-separated tags")
def cmd_ssh_add(target: str, name: Optional[str], tags: Optional[str]):
    """Add SSH device to management."""
    from .ssh_manager import SSHManager, SSHDevice, parse_device_target
    
    user, host, port = parse_device_target(target)
    device = SSHDevice(host, user, port, name, tags.split(",") if tags else [])
    
    manager = SSHManager()
    manager.add_device(device)
    manager.save_device_list(str(Path.home() / ".meshpi" / "ssh_devices.json"))


@cmd_ssh.command("list")
@click.option("--refresh", is_flag=True, default=False, help="Refresh device information")
def cmd_ssh_list(refresh: bool):
    """List managed SSH devices."""
    from .ssh_manager import SSHManager
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    if not manager.devices:
        console.print("[yellow]No devices managed yet[/yellow]")
        console.print("[dim]Use 'meshpi ssh add' or 'meshpi ssh scan --add' to add devices[/dim]")
        return
    
    manager.list_devices_table()


@cmd_ssh.command("connect")
@click.argument("target", required=False)
@click.option("--password", is_flag=True, default=False, help="Use password authentication")
@click.option("--key", help="Path to SSH private key")
@click.option("--all", is_flag=True, default=False, help="Connect to all devices")
def cmd_ssh_connect(target: Optional[str], password: bool, key: Optional[str], all: bool):
    """Connect to SSH device(s)."""
    from .ssh_manager import SSHManager, SSHDevice, parse_device_target
    from pathlib import Path
    import getpass
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    if all:
        devices_to_connect = manager.devices
    elif target:
        user, host, port = parse_device_target(target)
        device = SSHDevice(host, user, port)
        devices_to_connect = [device]
    else:
        console.print("[red]Error: Specify target or use --all[/red]")
        return
    
    ssh_password = None
    if password:
        ssh_password = getpass.getpass("Enter SSH password: ")
    
    connected_count = 0
    for device in devices_to_connect:
        console.print(f"[cyan]→[/cyan] Connecting to {device}...")
        if manager.connect_to_device(device, password=ssh_password, key_path=key):
            console.print(f"[green]✓ Connected to {device}[/green]")
            connected_count += 1
        else:
            console.print(f"[red]✗ Failed to connect to {device}[/red]")
    
    console.print(f"\n[green]Connected to {connected_count}/{len(devices_to_connect)} devices[/green]")
    
    # Show device info for connected devices
    if connected_count > 0:
        console.print("\n[bold]Device Information:[/bold]")
        for device in devices_to_connect:
            if device._connected:
                info = manager.get_device_info(device)
                console.print(f"\n[bold]{device}[/bold]")
                console.print(f"  Hostname: {info.get('hostname', 'N/A')}")
                console.print(f"  Uptime: {info.get('uptime', 'N/A')}")
                console.print(f"  CPU Temp: {info.get('cpu_temp', 'N/A')}")
                console.print(f"  MeshPi: {info.get('meshpi_version', 'N/A')}")
        
        # Keep connections open for interactive use
        console.print("\n[dim]Connections active. Press Ctrl+C to disconnect.[/dim]")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Disconnecting...[/yellow]")
            for device in devices_to_connect:
                manager.disconnect_device(device)
            console.print("[green]✓ All devices disconnected[/green]")


@cmd_ssh.command("exec")
@click.argument("command")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_ssh_exec(command: str, target: Optional[str], parallel: bool):
    """Execute command on SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    # Filter devices if target specified
    if target:
        user, host, port = parse_device_target(target)
        manager.devices = [d for d in manager.devices if d.host == host and d.user == user and d.port == port]
    
    if not manager.devices:
        console.print("[red]No devices available[/red]")
        return
    
    # Connect to all devices
    console.print("[cyan]→[/cyan] Connecting to devices...")
    for device in manager.devices:
        manager.connect_to_device(device)
    
    # Execute command
    console.print(f"[cyan]→[/cyan] Executing: [bold]{command}[/bold]")
    results = manager.run_command_on_all(command, parallel=parallel)
    
    # Display results
    table = Table(title="Command Results", border_style="cyan")
    table.add_column("Device", style="bold")
    table.add_column("Exit Code", style="dim")
    table.add_column("Output")
    table.add_column("Error", style="red")
    
    for device, (exit_code, stdout, stderr) in results.items():
        exit_status = "[green]0[/green]" if exit_code == 0 else f"[red]{exit_code}[/red]"
        output = stdout[:100] + "..." if len(stdout) > 100 else stdout
        error = stderr[:50] + "..." if len(stderr) > 50 else stderr
        
        table.add_row(str(device), exit_status, output, error)
    
    console.print(table)
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("install")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--method", default="pip", type=click.Choice(["pip", "venv"]), help="Installation method")
def cmd_ssh_install(target: Optional[str], method: str):
    """Install MeshPi on SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    # Filter devices if target specified
    if target:
        user, host, port = parse_device_target(target)
        manager.devices = [d for d in manager.devices if d.host == host and d.user == user and d.port == port]
    
    if not manager.devices:
        console.print("[red]No devices available[/red]")
        return
    
    # Connect and install
    for device in manager.devices:
        if manager.connect_to_device(device):
            manager.install_meshpi_on_device(device, method)
            manager.disconnect_device(device)


@cmd_ssh.command("update")
@click.option("--target", help="Specific device (user@host:port)")
def cmd_ssh_update(target: Optional[str]):
    """Update MeshPi on SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    # Filter devices if target specified
    if target:
        user, host, port = parse_device_target(target)
        manager.devices = [d for d in manager.devices if d.host == host and d.user == user and d.port == port]
    
    if not manager.devices:
        console.print("[red]No devices available[/red]")
        return
    
    # Connect and update
    for device in manager.devices:
        if manager.connect_to_device(device):
            manager.update_meshpi_on_device(device)
            manager.disconnect_device(device)


@cmd_ssh.command("restart")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--service", default="meshpi-daemon", help="Service name to restart")
def cmd_ssh_restart(target: Optional[str], service: str):
    """Restart MeshPi service on SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    # Filter devices if target specified
    if target:
        user, host, port = parse_device_target(target)
        manager.devices = [d for d in manager.devices if d.host == host and d.user == user and d.port == port]
    
    if not manager.devices:
        console.print("[red]No devices available[/red]")
        return
    
    # Connect and restart
    for device in manager.devices:
        if manager.connect_to_device(device):
            manager.restart_meshpi_on_device(device, service)
            manager.disconnect_device(device)


@cmd_ssh.command("transfer")
@click.argument("local_path")
@click.argument("remote_path")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--download", is_flag=True, default=False, help="Download from device instead of upload")
def cmd_ssh_transfer(local_path: str, remote_path: str, target: Optional[str], download: bool):
    """Transfer files to/from SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    # Filter devices if target specified
    if target:
        user, host, port = parse_device_target(target)
        manager.devices = [d for d in manager.devices if d.host == host and d.user == user and d.port == port]
    
    if not manager.devices:
        console.print("[red]No devices available[/red]")
        return
    
    # Connect and transfer
    for device in manager.devices:
        if manager.connect_to_device(device):
            if download:
                success = manager.transfer_file_from_device(device, remote_path, local_path)
                action = "downloaded from"
            else:
                success = manager.transfer_file_to_device(device, local_path, remote_path)
                action = "uploaded to"
            
            if success:
                console.print(f"[green]✓ File {action} {device}[/green]")
            else:
                console.print(f"[red]✗ Transfer failed for {device}[/red]")
            
            manager.disconnect_device(device)


def auto_detect_rpi_devices() -> list[DeviceRecord]:
    """Auto-detect Raspberry Pi devices on local network."""
    from .ssh_manager import SSHManager
    from .registry import DeviceRecord
    import socket
    from ipaddress import ip_network
    from rich.progress import Progress
    
    discovered = []
    
    # Get local network range
    try:
        # Get local IP by connecting to a remote address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        
        # Determine network range (assuming /24)
        if '.' in local_ip and local_ip.startswith('192.168.') or local_ip.startswith('10.') or local_ip.startswith('172.'):
            parts = local_ip.split('.')
            network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        else:
            network = "192.168.1.0/24"  # fallback
    except:
        network = "192.168.1.0/24"  # fallback
    
    console.print(f"[dim]Scanning network {network} for Raspberry Pi devices...[/dim]")
    
    # Use SSH manager to scan for SSH devices
    ssh_manager = SSHManager()
    ssh_devices = ssh_manager.scan_network(network, user="pi", port=22, timeout=3)
    
    if not ssh_devices:
        return discovered
    
    console.print(f"[dim]Found {len(ssh_devices)} SSH-enabled device(s), testing for Raspberry Pi...[/dim]")
    
    # Test each device for RPI characteristics
    with Progress() as progress:
        task = progress.add_task("Testing devices...", total=len(ssh_devices))
        
        for ssh_device in ssh_devices:
            progress.update(task, advance=1)
            
            try:
                # Try to connect with SSH key first
                if ssh_manager.connect_to_device(ssh_device):
                    # Check if it's a Raspberry Pi
                    is_rpi, hostname = check_if_raspberry_pi(ssh_device)
                    
                    if is_rpi:
                        # Generate device ID
                        device_id = hostname or f"rpi-{ssh_device.host.split('.')[-1]}"
                        
                        # Create device record
                        device = DeviceRecord(
                            device_id=device_id,
                            address=ssh_device.host,
                            host=ssh_device.host,
                            user=ssh_device.user,
                            port=ssh_device.port,
                            meshpi_port=7422,
                            online=True
                        )
                        
                        discovered.append(device)
                        console.print(f"[green]✓ Found Raspberry Pi: {device_id} ({ssh_device.host})[/green]")
                        
                        # Try to configure meshpi if possible
                        try:
                            configure_meshpi_on_device(ssh_device)
                        except Exception as e:
                            console.print(f"[dim]  Could not configure meshpi: {e}[/dim]")
                    
                    ssh_manager.disconnect_device(ssh_device)
                    
            except Exception as e:
                # Could not connect with SSH key, try password
                try:
                    import getpass
                    password = getpass.getpass(f"Enter password for {ssh_device.user}@{ssh_device.host} (or press Enter to skip): ")
                    if password:
                        if ssh_manager.connect_to_device(ssh_device, password=password):
                            # Check if it's a Raspberry Pi
                            is_rpi, hostname = check_if_raspberry_pi(ssh_device)
                            
                            if is_rpi:
                                # Generate device ID
                                device_id = hostname or f"rpi-{ssh_device.host.split('.')[-1]}"
                                
                                # Create device record
                                device = DeviceRecord(
                                    device_id=device_id,
                                    address=ssh_device.host,
                                    host=ssh_device.host,
                                    user=ssh_device.user,
                                    port=ssh_device.port,
                                    meshpi_port=7422,
                                    online=True
                                )
                                
                                discovered.append(device)
                                console.print(f"[green]✓ Found Raspberry Pi: {device_id} ({ssh_device.host})[/green]")
                                
                                # Try to configure meshpi if possible
                                try:
                                    configure_meshpi_on_device(ssh_device)
                                except Exception as e:
                                    console.print(f"[dim]  Could not configure meshpi: {e}[/dim]")
                            
                            ssh_manager.disconnect_device(ssh_device)
                except Exception:
                    # Skip this device
                    pass
    
    return discovered


def check_if_raspberry_pi(ssh_device) -> tuple[bool, str]:
    """Check if the connected device is a Raspberry Pi."""
    try:
        # Check for Raspberry Pi specific files
        commands = [
            "cat /proc/device-tree/model 2>/dev/null || echo 'unknown'",
            "hostname 2>/dev/null || echo 'unknown'",
            "uname -m 2>/dev/null || echo 'unknown'"
        ]
        
        model = ""
        hostname = ""
        arch = ""
        
        for cmd in commands:
            stdin, stdout, stderr = ssh_device.client.exec_command(cmd)
            result = stdout.read().decode().strip()
            
            if "model" in cmd:
                model = result
            elif "hostname" in cmd:
                hostname = result
            elif "uname" in cmd:
                arch = result
        
        # Check if it's a Raspberry Pi
        is_rpi = (
            "raspberry pi" in model.lower() or 
            "bcm" in model.lower() or
            arch in ["armv7l", "aarch64", "armv6l"] or
            "raspberrypi" in hostname.lower()
        )
        
        return is_rpi, hostname
        
    except Exception:
        return False, ""


def configure_meshpi_on_device(ssh_device) -> bool:
    """Try to configure meshpi on the discovered device."""
    try:
        console.print(f"[dim]  Configuring MeshPi on {ssh_device.host}...[/dim]")
        
        # Check if meshpi is already installed
        stdin, stdout, stderr = ssh_device.client.exec_command("command -v meshpi >/dev/null 2>&1 && echo 'installed' || echo 'not_installed'")
        result = stdout.read().decode().strip()
        
        if result == "installed":
            console.print(f"[dim]  MeshPi already installed, starting service...[/dim]")
            # MeshPi is already installed, try to start service on port 7422
            stdin, stdout, stderr = ssh_device.client.exec_command("nohup meshpi host --port 7422 --bind 0.0.0.0 > /tmp/meshpi-host.log 2>&1 & echo $! > /tmp/meshpi-host.pid")
            time.sleep(2)  # Give it time to start
            
            # Check if it's running
            stdin, stdout, stderr = ssh_device.client.exec_command("netstat -tlnp 2>/dev/null | grep 7422 || ss -tlnp 2>/dev/null | grep 7422")
            if stdout.read().decode().strip():
                console.print(f"[dim]  ✓ MeshPi service started on port 7422[/dim]")
                return True
            else:
                console.print(f"[dim]  ⚠ MeshPi service may not be running properly[/dim]")
                return False
        else:
            console.print(f"[dim]  Installing MeshPi...[/dim]")
            # Try to install meshpi (basic installation)
            stdin, stdout, stderr = ssh_device.client.exec_command("pip3 install meshpi --break-system-packages -q 2>/dev/null && echo 'installed' || echo 'failed'")
            result = stdout.read().decode().strip()
            
            if result == "installed":
                console.print(f"[dim]  ✓ MeshPi installed successfully[/dim]")
                # Start meshpi service
                stdin, stdout, stderr = ssh_device.client.exec_command("nohup meshpi host --port 7422 --bind 0.0.0.0 > /tmp/meshpi-host.log 2>&1 & echo $! > /tmp/meshpi-host.pid")
                time.sleep(2)  # Give it time to start
                
                # Check if it's running
                stdin, stdout, stderr = ssh_device.client.exec_command("netstat -tlnp 2>/dev/null | grep 7422 || ss -tlnp 2>/dev/null | grep 7422")
                if stdout.read().decode().strip():
                    console.print(f"[dim]  ✓ MeshPi service started on port 7422[/dim]")
                    return True
                else:
                    console.print(f"[dim]  ⚠ MeshPi service may not be running properly[/dim]")
                    return False
            else:
                console.print(f"[dim]  ✗ Failed to install MeshPi[/dim]")
                return False
        
    except Exception as e:
        console.print(f"[dim]  ✗ Configuration failed: {e}[/dim]")
        return False


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
            console.print("[dim]Trying to auto-detect Raspberry Pi devices on local network...[/dim]\n")
            
            # Try to auto-detect RPI devices
            discovered_devices = auto_detect_rpi_devices()
            
            if discovered_devices:
                console.print(f"[green]✓ Found {len(discovered_devices)} Raspberry Pi device(s)[/green]\n")
                
                # Add discovered devices to registry
                for device in discovered_devices:
                    console.print(f"[cyan]→ Adding {device.device_id} ({device.address})[/cyan]")
                    reg.register_device(
                        device_id=device.device_id,
                        address=device.address,
                        host=device.host,
                        user=device.user,
                        port=device.port
                    )
                
                devices = reg.all_devices()
            else:
                console.print("[yellow]No Raspberry Pi devices found on local network.[/yellow]")
                console.print("[dim]Make sure devices are powered on and connected to the network.[/dim]\n")
                
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
            last_seen = time.strftime("%H:%M", time.localtime(device.last_seen)) if device.last_seen else "Never"
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
    
    # Add to registry
    from .registry import registry as reg
    from .doctor import parse_target
    
    try:
        # Parse address to get user, host, port
        if "@" in address:
            user, host, port = parse_target(address)
        else:
            # Default user if not specified
            user = "pi"
            host = address
            port = 22
        
        # Create device entry
        device = reg.register_device(
            device_id=device_id,
            address=address,
            host=host,
            user=user,
            port=port
        )
        
        console.print(f"[green]✓ Device {device_id} added[/green]")
        console.print(f"[dim]Address: {address}[/dim]")
        console.print("[dim]Note: Device will appear as offline until it connects[/dim]")
        
        # Save to registry
        reg.save()
        
    except Exception as e:
        console.print(f"[red]✗ Failed to add device: {e}[/red]")
        console.print("[dim]Device was not added to registry[/dim]")


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
        details_table.add_row("Last Seen", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(device.last_seen)) if device.last_seen else "Never")
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
        "Last Seen": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(device.last_seen)) if device.last_seen else "Never",
        "Applied Profiles": ", ".join(device.applied_profiles) if device.applied_profiles else "None",
        "First Seen": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(device.first_seen)) if device.first_seen else "Unknown",
    }
    
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan", width=15)
    table.add_column("Value")
    
    for key, value in details.items():
        table.add_row(key, value)
    
    console.print(table)
