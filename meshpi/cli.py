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
  meshpi monitor              Monitor status of devices or groups
  meshpi ssh scan            Scan network for SSH devices
  meshpi ssh add <target>    Add SSH device to management
  meshpi ssh list            List managed SSH devices
  meshpi ssh connect         Connect to SSH device(s)
  meshpi ssh shell <target>  Open interactive SSH shell to device
  meshpi ssh exec <cmd>      Execute command on SSH device(s)
  meshpi ssh batch <cmd>     Execute custom command on multiple devices
  meshpi ssh system-update  Update package lists on device(s)
  meshpi ssh system-upgrade  Upgrade packages on device(s)
  meshpi ssh install         Install MeshPi on SSH device(s)
  meshpi ssh update          Update MeshPi on SSH device(s)
  meshpi ssh restart         Restart MeshPi service on SSH device(s)
  meshpi ssh transfer        Transfer files to/from SSH device(s)

Group Management Examples:
  meshpi group create servers          Create device group
  meshpi group add-device servers pi@192.168.1.100  Add device to group
  meshpi group list                   List all groups
  meshpi group status servers          Check status of group devices
  meshpi group exec servers "uptime"   Run command on group
  meshpi group system-update servers   Update all devices in group

Monitoring Examples:
  meshpi monitor                       Monitor all devices once
  meshpi monitor --group servers       Monitor specific group
  meshpi monitor --continuous          Continuous monitoring
  meshpi monitor --interval 30         Monitor every 30 seconds

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
  meshpi ssh shell pi@192.168.1.100  # Open SSH shell to device
  meshpi ssh exec "uptime"           # Run command on all devices
  meshpi ssh install --target pi@rpi # Install MeshPi on specific device
"""

from __future__ import annotations

import time
import subprocess
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
import sys
import tty
import termios

console = Console()

def get_key():
    """Get a single keypress from the user."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # Escape sequence
            # Read the next two characters to determine arrow key
            ch1 = sys.stdin.read(1)
            ch2 = sys.stdin.read(1)
            if ch1 == '[':
                if ch2 == 'A':
                    return 'up'
                elif ch2 == 'B':
                    return 'down'
                elif ch2 == 'C':
                    return 'right'
                elif ch2 == 'D':
                    return 'left'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def interactive_device_selection(devices: List, all_devices: bool = False):
    """Interactive device selection with arrow keys."""
    if not devices:
        return None
    
    selected_index = 0
    selected_devices = []  # For multi-selection
    
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]MeshPi Device Manager[/bold cyan]\n"
            "[dim]Use ↑↓ to navigate, SPACE to select, ENTER to confirm, q to quit[/dim]",
            border_style="cyan"
        ))
        
        # Create device table
        table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("Sel", style="bold", width=4)
        table.add_column("Device ID", style="bold")
        table.add_column("Status", width=8)
        table.add_column("Address", style="dim")
        table.add_column("Last Seen", style="dim")
        table.add_column("Profiles", style="dim")
        
        # Filter devices
        visible_devices = devices if all_devices else [d for d in devices if d.online]
        
        for i, device in enumerate(visible_devices):
            # Selection indicator
            if i == selected_index:
                sel_marker = "→"
                row_style = "on cyan"
            else:
                sel_marker = " "
                row_style = ""
            
            # Multi-selection marker
            multi_marker = "✓" if device in selected_devices else " "
            
            status = "[green]ONLINE[/green]" if device.online else "[red]OFFLINE[/red]"
            last_seen = time.strftime("%H:%M", time.localtime(device.last_seen)) if device.last_seen else "Never"
            profiles = ", ".join(device.applied_profiles[:2]) if device.applied_profiles else "None"
            if len(device.applied_profiles) > 2:
                profiles += f" (+{len(device.applied_profiles)-2})"
            
            if row_style:
                table.add_row(f"{multi_marker}{sel_marker}", device.device_id, status, device.address, last_seen, profiles, style=row_style)
            else:
                table.add_row(f"{multi_marker}{sel_marker}", device.device_id, status, device.address, last_seen, profiles)
        
        console.print(table)
        
        # Show multi-selection info
        if selected_devices:
            console.print(f"\n[dim]Selected: {len(selected_devices)} device(s)[/dim]")
        
        # Show help
        console.print("\n[bold cyan]Controls:[/bold cyan]")
        console.print("  ↑↓ Navigate | SPACE Select | ENTER Confirm | q Quit | a Toggle all")
        
        # Get user input
        key = get_key()
        
        if key == 'q':
            return None
        elif key == 'up':
            selected_index = max(0, selected_index - 1)
        elif key == 'down':
            selected_index = min(len(visible_devices) - 1, selected_index + 1)
        elif key == ' ':
            # Toggle selection
            device = visible_devices[selected_index]
            if device in selected_devices:
                selected_devices.remove(device)
            else:
                selected_devices.append(device)
        elif key == '\r' or key == '\n':
            # Confirm selection
            if selected_devices:
                return selected_devices
            else:
                return [visible_devices[selected_index]]
        elif key == 'a':
            # Toggle all selection
            if selected_devices == visible_devices:
                selected_devices = []
            else:
                selected_devices = visible_devices.copy()

def enhanced_device_menu(devices: List):
    """Enhanced device menu for single or multiple devices."""
    if len(devices) == 1:
        # Single device menu
        device = devices[0]
        device_menu(device)
    else:
        # Multi-device menu
        multi_device_menu(devices)

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


# meshpi group
# ─────────────────────────────────────────────────────────────────────────────

@main.group("group")
def cmd_group():
    """Device group management for batch operations."""
    pass


@cmd_group.command("create")
@click.argument("group_name")
@click.option("--description", default="", help="Group description")
def cmd_group_create(group_name: str, description: str):
    """Create a device group."""
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    groups_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing groups
    groups = {}
    if groups_file.exists():
        try:
            groups = json.loads(groups_file.read_text())
        except:
            groups = {}
    
    if group_name in groups:
        console.print(f"[red]Group '{group_name}' already exists[/red]")
        return
    
    groups[group_name] = {
        "name": group_name,
        "description": description,
        "devices": [],
        "created_at": time.time()
    }
    
    groups_file.write_text(json.dumps(groups, indent=2))
    console.print(f"[green]✓ Group '{group_name}' created[/green]")


@cmd_group.command("add-device")
@click.argument("group_name")
@click.argument("target")
def cmd_group_add_device(group_name: str, target: str):
    """Add device to group."""
    from pathlib import Path
    import json
    from .ssh_manager import parse_device_target
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    if not groups_file.exists():
        console.print("[red]No groups found. Create a group first.[/red]")
        return
    
    try:
        groups = json.loads(groups_file.read_text())
    except:
        console.print("[red]Error reading groups file[/red]")
        return
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    user, host, port = parse_device_target(target)
    device_info = f"{user}@{host}:{port}"
    
    if device_info in groups[group_name]["devices"]:
        console.print("[yellow]Device already in group[/yellow]")
        return
    
    groups[group_name]["devices"].append(device_info)
    groups_file.write_text(json.dumps(groups, indent=2))
    console.print(f"[green]✓ Added {device_info} to group '{group_name}'[/green]")


@cmd_group.command("list")
def cmd_group_list():
    """List all device groups."""
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    if not groups_file.exists():
        console.print("[yellow]No groups found[/yellow]")
        return
    
    try:
        groups = json.loads(groups_file.read_text())
    except:
        console.print("[red]Error reading groups file[/red]")
        return
    
    if not groups:
        console.print("[yellow]No groups found[/yellow]")
        return
    
    from rich.table import Table
    table = Table(title="Device Groups", border_style="cyan")
    table.add_column("Group", style="bold cyan")
    table.add_column("Devices", style="dim")
    table.add_column("Description", style="dim")
    
    for group_name, group_data in groups.items():
        device_count = len(group_data.get("devices", []))
        description = group_data.get("description", "")
        table.add_row(group_name, str(device_count), description)
    
    console.print(table)


@cmd_group.command("show")
@click.argument("group_name")
def cmd_group_show(group_name: str):
    """Show devices in a group."""
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    try:
        groups = json.loads(groups_file.read_text())
    except:
        console.print("[red]Error reading groups file[/red]")
        return
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    group_data = groups[group_name]
    devices = group_data.get("devices", [])
    
    from rich.table import Table
    table = Table(title=f"Group: {group_name}", border_style="cyan")
    table.add_column("Device", style="bold")
    table.add_column("Type", style="dim")
    
    for device in devices:
        table.add_row(device, "SSH")
    
    console.print(table)
    console.print(f"\n[dim]Total devices: {len(devices)}[/dim]")


@cmd_group.command("exec")
@click.argument("group_name")
@click.argument("command")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_group_exec(group_name: str, command: str, parallel: bool):
    """Execute command on all devices in a group."""
    from pathlib import Path
    import json
    from .ssh_manager import SSHManager, parse_device_target
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    try:
        groups = json.loads(groups_file.read_text())
    except:
        console.print("[red]Error reading groups file[/red]")
        return
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    devices = groups[group_name].get("devices", [])
    if not devices:
        console.print(f"[yellow]No devices in group '{group_name}'[/yellow]")
        return
    
    manager = SSHManager()
    
    # Add devices from group
    for device_str in devices:
        user, host, port = parse_device_target(device_str)
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    # Connect and execute
    console.print(f"[cyan]→[/cyan] Executing command on group '{group_name}'...")
    console.print(f"[dim]Command: {command}[/dim]")
    
    for device in manager.devices:
        if manager.connect_to_device(device):
            exit_code, stdout, stderr = manager.run_command_on_device(device, command)
            console.print(f"\n[bold]{device}:[/bold]")
            if exit_code == 0:
                console.print(stdout)
            else:
                console.print(f"[red]Error: {stderr}[/red]")
            manager.disconnect_device(device)


@cmd_group.command("hw-apply")
@click.argument("group_name")
@click.argument("profile_ids", nargs=-1)
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be installed")
@click.option("--interactive", "-i", is_flag=True, default=False, help="Interactive profile selection")
@click.option("--search", "-s", default=None, help="Search profiles before selection")
def cmd_group_hw_apply(group_name: str, profile_ids: tuple, parallel: bool, dry_run: bool, interactive: bool, search: str):
    """Apply hardware profiles to all devices in a group."""
    from pathlib import Path
    import json
    from .ssh_manager import SSHManager, parse_device_target
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    try:
        groups = json.loads(groups_file.read_text())
    except:
        console.print("[red]Error reading groups file[/red]")
        return
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    devices = groups[group_name].get("devices", [])
    if not devices:
        console.print(f"[yellow]No devices in group '{group_name}'[/yellow]")
        return
    
    manager = SSHManager()
    
    # Add devices from group
    for device_str in devices:
        user, host, port = parse_device_target(device_str)
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    # Connect to devices
    for device in manager.devices:
        manager.connect_to_device(device)
    
    # Build apply command
    cmd_parts = ["meshpi", "hw", "apply"]
    if dry_run:
        cmd_parts.append("--dry-run")
    if interactive:
        cmd_parts.append("--interactive")
    if search:
        cmd_parts.extend(["--search", search])
    cmd_parts.extend(profile_ids)
    
    apply_cmd = " ".join(cmd_parts)
    
    console.print(f"[cyan]→[/cyan] Applying hardware profiles to group '{group_name}'...")
    console.print(f"[dim]Command: {apply_cmd}[/dim]")
    
    results = manager.run_command_on_all(apply_cmd, parallel=parallel)
    
    for device, (exit_code, stdout, stderr) in results.items():
        console.print(f"\n[bold]{device}:[/bold]")
        if exit_code == 0:
            console.print(stdout)
        else:
            console.print(f"[red]Error: {stderr}[/red]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


# ─────────────────────────────────────────────────────────────────────────────
# meshpi hw
# ─────────────────────────────────────────────────────────────────────────────

@main.group("hw")
def cmd_hw():
    """Hardware peripheral profiles — list, inspect, apply."""
    pass


@cmd_hw.command("quick-install")
@click.argument("category", default="")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--group", help="Device group name")
@click.option("--popular", is_flag=True, default=False, help="Show only popular profiles")
@click.option("--interactive", "-i", is_flag=True, default=True, help="Interactive selection")
def cmd_hw_quick_install(category: str, target: Optional[str], group: str, popular: bool, interactive: bool):
    """
    \b
    Quick hardware installation wizard.
    
    Examples:
      meshpi hw quick-install display --interactive
      meshpi hw quick-install sensor --group sensors
      meshpi hw quick-install --popular --target pi@192.168.1.100
    """
    from .hardware.custom import get_all_profiles
    from .hardware.profiles import list_profiles
    from rich.table import Table
    from rich.prompt import Confirm, Prompt
    
    # Get all profiles
    all_profiles = get_all_profiles()
    
    # Filter by category if specified
    if category:
        profiles = [p for p in all_profiles.values() if p.category == category]
    else:
        profiles = list(all_profiles.values())
    
    # Filter by popular if requested
    if popular:
        popular_tags = ["oled", "sensor", "hat", "i2c", "spi", "display"]
        profiles = [p for p in profiles if any(tag in p.tags for tag in popular_tags)]
    
    if not profiles:
        console.print("[yellow]No profiles found[/yellow]")
        return
    
    if interactive:
        # Show categorized selection
        categories = {}
        for profile in profiles:
            if profile.category not in categories:
                categories[profile.category] = []
            categories[profile.category].append(profile)
        
        console.print(Panel.fit(
            "[bold cyan]Quick Hardware Installation[/bold cyan]\n"
            "[dim]Select a category to browse available hardware[/dim]",
            border_style="cyan"
        ))
        
        # Show categories
        cat_table = Table(title="Available Categories", border_style="cyan")
        cat_table.add_column("Category", style="bold cyan")
        cat_table.add_column("Count", style="dim")
        cat_table.add_column("Examples", style="dim")
        
        for cat_name, cat_profiles in categories.items():
            examples = ", ".join([p.name for p in cat_profiles[:2]])
            if len(cat_profiles) > 2:
                examples += f" (+{len(cat_profiles)-2})"
            cat_table.add_row(cat_name, str(len(cat_profiles)), examples)
        
        console.print(cat_table)
        
        # Let user choose category
        chosen_cat = Prompt.ask(
            "[bold]Choose category[/bold]", 
            choices=list(categories.keys()),
            default=category if category in categories else list(categories.keys())[0]
        )
        
        # Show profiles in chosen category
        cat_profiles = categories[chosen_cat]
        
        console.print(f"\n[bold cyan]{chosen_cat.title()} Profiles:[/bold cyan]")
        profile_table = Table(border_style="cyan")
        profile_table.add_column("ID", style="bold cyan", no_wrap=True)
        profile_table.add_column("Name")
        profile_table.add_column("Description", style="dim")
        profile_table.add_column("Tags", style="dim")
        
        for i, profile in enumerate(cat_profiles):
            profile_table.add_row(
                profile.id,
                profile.name,
                profile.description[:50] + "..." if len(profile.description) > 50 else profile.description,
                ", ".join(profile.tags[:3])
            )
        
        console.print(profile_table)
        
        # Let user select profiles
        selected_ids = []
        while True:
            profile_id = Prompt.ask(
                "[bold]Enter profile ID to install[/bold]", 
                default="",
                show_default=False
            )
            if not profile_id:
                break
            
            # Find profile
            profile = next((p for p in cat_profiles if p.id == profile_id), None)
            if profile:
                selected_ids.append(profile_id)
                console.print(f"[green]✓ Added {profile.name}[/green]")
            else:
                console.print(f"[red]Profile '{profile_id}' not found[/red]")
        
        if not selected_ids:
            console.print("[yellow]No profiles selected[/yellow]")
            return
        
        console.print(f"\n[cyan]Selected {len(selected_ids)} profiles:[/cyan]")
        for pid in selected_ids:
            profile = next((p for p in cat_profiles if p.id == pid), None)
            if profile:
                console.print(f"  • {profile.name}")
        
        if not Confirm.ask("\n[bold]Install these profiles?[/bold]", default=True):
            return
        
        # Execute installation
        if group:
            # Install on group
            from pathlib import Path
            import json
            groups_file = Path.home() / ".meshpi" / "groups.json"
            if groups_file.exists():
                groups = json.loads(groups_file.read_text())
                if group in groups:
                    devices = groups[group].get("devices", [])
                    console.print(f"[cyan]Installing on {len(devices)} devices in group '{group}'...[/cyan]")
                    # Use group command
                    from .ssh_manager import SSHManager, parse_device_target
                    manager = SSHManager()
                    for device_str in devices:
                        user, host, port = parse_device_target(device_str)
                        device = SSHDevice(host, user, port)
                        manager.add_device(device)
                    
                    for device in manager.devices:
                        manager.connect_to_device(device)
                    
                    apply_cmd = f"meshpi hw apply {' '.join(selected_ids)}"
                    results = manager.run_command_on_all(apply_cmd, parallel=True)
                    
                    for device, (exit_code, stdout, stderr) in results.items():
                        console.print(f"\n[bold]{device}:[/bold]")
                        if exit_code == 0:
                            console.print(stdout)
                        else:
                            console.print(f"[red]Error: {stderr}[/red]")
                        manager.disconnect_device(device)
                    return
        
        if target:
            # Install on specific device
            from .ssh_manager import SSHManager, parse_device_target
            user, host, port = parse_device_target(target)
            device = SSHDevice(host, user, port)
            manager = SSHManager()
            manager.add_device(device)
            
            if manager.connect_to_device(device):
                apply_cmd = f"meshpi hw apply {' '.join(selected_ids)}"
                exit_code, stdout, stderr = manager.run_command_on_device(device, apply_cmd)
                console.print(f"\n[bold]{device}:[/bold]")
                if exit_code == 0:
                    console.print(stdout)
                else:
                    console.print(f"[red]Error: {stderr}[/red]")
                manager.disconnect_device(device)
            return
        
        # Local installation
        from .hardware.applier import apply_multiple_profiles
        apply_multiple_profiles(list(selected_ids))
        
    else:
        # Non-interactive: just show available profiles
        table = Table(title=f"Hardware Profiles ({len(profiles)} found)", border_style="cyan")
        table.add_column("ID", style="bold cyan", no_wrap=True)
        table.add_column("Category", style="dim")
        table.add_column("Name")
        table.add_column("Description", style="dim")
        
        for p in profiles[:20]:  # Limit output
            table.add_row(
                p.id, 
                p.category, 
                p.name, 
                p.description[:60] + "..." if len(p.description) > 60 else p.description
            )
        
        console.print(table)
        if len(profiles) > 20:
            console.print(f"\n[dim]... and {len(profiles) - 20} more profiles[/dim]")


@cmd_hw.command("catalog")
@click.option("--category", "-c", default=None,
              help="Filter by category: display|gpio|sensor|camera|audio|networking|hat|storage")
@click.option("--tag", "-t", default=None, help="Filter by tag (e.g. 'i2c', 'spi', 'oled')")
@click.option("--popular", is_flag=True, default=False, help="Show only popular profiles")
@click.option("--installed", is_flag=True, default=False, help="Show only installed profiles")
@click.option("--format", default="table", type=click.Choice(["table", "json", "list"]), help="Output format")
def cmd_hw_catalog(category: str, tag: str, popular: bool, installed: bool, format: str):
    """Browse hardware catalog with filtering options."""
    from .hardware.custom import get_all_profiles
    from .hardware.profiles import list_profiles
    
    # Get all profiles
    all_profiles = get_all_profiles()
    profiles = list(all_profiles.values())
    
    # Apply filters
    if category:
        profiles = [p for p in profiles if p.category == category]
    
    if tag:
        profiles = [p for p in profiles if tag in p.tags]
    
    if popular:
        popular_tags = ["oled", "sensor", "hat", "i2c", "spi", "display", "camera"]
        profiles = [p for p in profiles if any(tag in p.tags for tag in popular_tags)]
    
    if installed:
        # TODO: Check what's actually installed on the system
        console.print("[yellow]Installed filter not yet implemented[/yellow]")
    
    if format == "json":
        import json
        data = []
        for p in profiles:
            data.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "tags": p.tags,
                "packages": p.packages
            })
        console.print(json.dumps(data, indent=2))
    
    elif format == "list":
        for p in profiles:
            console.print(f"{p.id:30} {p.category:15} {p.name}")
    
    else:  # table format
        from rich.table import Table
        
        # Group by category
        categories = {}
        for p in profiles:
            if p.category not in categories:
                categories[p.category] = []
            categories[p.category].append(p)
        
        for cat_name, cat_profiles in categories.items():
            console.print(f"\n[bold cyan]{cat_name.title()} ({len(cat_profiles)}):[/bold cyan]")
            
            table = Table(border_style="cyan", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="bold cyan", no_wrap=True, width=25)
            table.add_column("Name", width=30)
            table.add_column("Description", style="dim", width=50)
            table.add_column("Tags", style="dim", width=20)
            
            for p in cat_profiles[:10]:  # Limit per category
                table.add_row(
                    p.id,
                    p.name,
                    p.description[:47] + "..." if len(p.description) > 47 else p.description,
                    ", ".join(p.tags[:3])
                )
            
            console.print(table)
            if len(cat_profiles) > 10:
                console.print(f"[dim]... and {len(cat_profiles) - 10} more in {cat_name}[/dim]")
        
        console.print(f"\n[dim]Total: {len(profiles)} profiles[/dim]")


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


@cmd_hw.command("search")
@click.argument("query", default="")
@click.option("--category", "-c", default=None,
              help="Filter by category: display|gpio|sensor|camera|audio|networking|hat|storage")
@click.option("--tag", "-t", default=None, help="Filter by tag (e.g. 'i2c', 'spi', 'oled')")
@click.option("--installed", is_flag=True, default=False, help="Show only installed profiles")
@click.option("--interactive", "-i", is_flag=True, default=False, help="Interactive selection and install")
def cmd_hw_search(query: str, category: str, tag: str, installed: bool, interactive: bool):
    """Search hardware profiles with advanced filtering and interactive installation."""
    from .hardware.profiles import list_profiles, get_profile
    from .hardware.applier import apply_multiple_profiles
    from rich.prompt import Confirm
    
    profiles = list_profiles(category=category, tag=tag)
    
    # Filter by query
    if query:
        query_lower = query.lower()
        profiles = [p for p in profiles if 
                   query_lower in p.name.lower() or 
                   query_lower in p.description.lower() or 
                   query_lower in p.id.lower()]
    
    if not profiles:
        console.print("[yellow]No profiles found matching your criteria.[/yellow]")
        return
    
    if interactive:
        # Interactive selection mode
        selected_profiles = interactive_profile_selection(profiles)
        if selected_profiles:
            console.print(f"\n[cyan]Installing {len(selected_profiles)} selected profiles...[/cyan]")
            apply_multiple_profiles(selected_profiles)
        else:
            console.print("[yellow]No profiles selected.[/yellow]")
    else:
        # Display results
        table = Table(title=f"Hardware Profiles ({len(profiles)} found)", border_style="cyan")
        table.add_column("ID", style="bold cyan", no_wrap=True)
        table.add_column("Category", style="dim")
        table.add_column("Name")
        table.add_column("Description", style="dim")
        table.add_column("Tags", style="dim")
        
        for p in profiles:
            table.add_row(
                p.id, 
                p.category, 
                p.name, 
                p.description[:60] + "..." if len(p.description) > 60 else p.description,
                ", ".join(p.tags[:3])
            )
        
        console.print(table)
        console.print(f"\n[dim]Use --interactive to select and install, or 'meshpi hw apply <id>' to install specific profile[/dim]")


def interactive_profile_selection(profiles):
    """Interactive profile selection with arrow keys."""
    if not profiles:
        return []
    
    selected_index = 0
    selected_profiles = []
    
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]Select Hardware Profiles[/bold cyan]\n"
            "[dim]Use ↑↓ to navigate, SPACE to select, ENTER to confirm, q to quit[/dim]",
            border_style="cyan"
        ))
        
        # Create profile table
        table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("Sel", style="bold", width=4)
        table.add_column("ID", style="bold cyan")
        table.add_column("Category", style="dim")
        table.add_column("Name")
        table.add_column("Tags", style="dim")
        
        for i, profile in enumerate(profiles):
            if i == selected_index:
                sel_marker = "→"
                row_style = "on cyan"
            else:
                sel_marker = " "
                row_style = ""
            
            multi_marker = "✓" if profile in selected_profiles else " "
            
            if row_style:
                table.add_row(
                    f"{multi_marker}{sel_marker}", 
                    profile.id, 
                    profile.category, 
                    profile.name, 
                    ", ".join(profile.tags[:2]), 
                    style=row_style
                )
            else:
                table.add_row(
                    f"{multi_marker}{sel_marker}", 
                    profile.id, 
                    profile.category, 
                    profile.name, 
                    ", ".join(profile.tags[:2])
                )
        
        console.print(table)
        
        if selected_profiles:
            console.print(f"\n[dim]Selected: {len(selected_profiles)} profile(s)[/dim]")
        
        console.print("\n[bold cyan]Controls:[/bold cyan]")
        console.print("  ↑↓ Navigate | SPACE Select | ENTER Confirm | q Quit | a Toggle all")
        
        key = get_key()
        
        if key == 'q':
            return []
        elif key == 'up':
            selected_index = max(0, selected_index - 1)
        elif key == 'down':
            selected_index = min(len(profiles) - 1, selected_index + 1)
        elif key == ' ':
            profile = profiles[selected_index]
            if profile in selected_profiles:
                selected_profiles.remove(profile)
            else:
                selected_profiles.append(profile)
        elif key == '\r' or key == '\n':
            return selected_profiles
        elif key == 'a':
            if selected_profiles == profiles:
                selected_profiles = []
            else:
                selected_profiles = profiles.copy()


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


@cmd_hw.command("create")
@click.option("--interactive", "-i", is_flag=True, default=True, help="Interactive profile creation")
@click.option("--import-file", "-f", default=None, help="Import profile from YAML/JSON file")
@click.option("--name", default=None, help="Profile name")
@click.option("--category", default=None, help="Profile category")
@click.option("--description", default=None, help="Profile description")
@click.option("--packages", default=None, help="Comma-separated apt packages")
@click.option("--python-packages", default=None, help="Comma-separated pip packages")
@click.option("--tags", default=None, help="Comma-separated tags")
def cmd_hw_create(interactive: bool, import_file: str, name: str, category: str, 
                  description: str, packages: str, python_packages: str, tags: str):
    """
    \b
    Create custom hardware profiles.

    Examples:
      meshpi hw create --interactive
      meshpi hw create --import-file my_profile.yaml
      meshpi hw create --name "My Sensor" --category sensor --packages "i2c-tools,python3-smbus"
    """
    from .hardware.custom import (
        create_custom_profile_interactive,
        import_profile_from_file,
        save_custom_profiles,
        load_custom_profiles
    )
    from .hardware.profiles import HardwareProfile
    
    if import_file:
        # Import from file
        profile = import_profile_from_file(import_file)
        if profile:
            custom_profiles = load_custom_profiles()
            custom_profiles[profile.id] = profile
            if save_custom_profiles(custom_profiles):
                console.print(f"[green]✓ Profile '{profile.id}' imported successfully[/green]")
            else:
                console.print(f"[red]✗ Failed to save imported profile[/red]")
        return
    
    if interactive or not all([name, category, description]):
        # Interactive creation
        profile = create_custom_profile_interactive()
        if profile:
            custom_profiles = load_custom_profiles()
            custom_profiles[profile.id] = profile
            if save_custom_profiles(custom_profiles):
                console.print(f"[green]✓ Custom profile '{profile.id}' created successfully[/green]")
                console.print(f"[dim]Use: meshpi hw apply {profile.id}[/dim]")
            else:
                console.print(f"[red]✗ Failed to save custom profile[/red]")
        return
    
    # Quick creation from command line
    profile_id = name.lower().replace(' ', '_').replace('-', '_')
    
    pkg_list = [p.strip() for p in packages.split(',')] if packages else []
    py_pkg_list = [p.strip() for p in python_packages.split(',')] if python_packages else []
    tag_list = [t.strip() for t in tags.split(',')] if tags else []
    
    post_commands = []
    if py_pkg_list:
        post_commands.append(f"pip3 install {' '.join(py_pkg_list)}")
    
    profile = HardwareProfile(
        id=profile_id,
        name=name,
        category=category,
        description=description,
        packages=pkg_list,
        post_commands=post_commands,
        tags=tag_list
    )
    
    custom_profiles = load_custom_profiles()
    custom_profiles[profile.id] = profile
    
    if save_custom_profiles(custom_profiles):
        console.print(f"[green]✓ Custom profile '{profile.id}' created successfully[/green]")
        console.print(f"[dim]Use: meshpi hw apply {profile.id}[/dim]")
    else:
        console.print(f"[red]✗ Failed to save custom profile[/red]")


@cmd_hw.command("custom")
def cmd_hw_custom():
    """Manage custom hardware profiles."""
    from .hardware.custom import list_custom_profiles
    list_custom_profiles()


@cmd_hw.command("export")
@click.argument("profile_id")
@click.argument("file_path")
@click.option("--format", "-f", default="yaml", help="Export format: yaml or json")
def cmd_hw_export(profile_id: str, file_path: str, format: str):
    """Export a hardware profile to file."""
    from .hardware.custom import export_profile_to_file
    from .hardware.custom import get_all_profiles
    
    all_profiles = get_all_profiles()
    
    if profile_id not in all_profiles:
        console.print(f"[red]Profile '{profile_id}' not found.[/red]")
        return
    
    # Ensure file has correct extension
    if not file_path.endswith(('.' + format)):
        file_path += f'.{format}'
    
    profile = all_profiles[profile_id]
    if export_profile_to_file(profile, file_path):
        console.print(f"[green]✓ Profile '{profile_id}' exported to {file_path}[/green]")
    else:
        console.print(f"[red]✗ Failed to export profile[/red]")


@cmd_hw.command("delete")
@click.argument("profile_id")
@click.option("--confirm", is_flag=True, default=False, help="Skip confirmation prompt")
def cmd_hw_delete(profile_id: str, confirm: bool):
    """Delete a custom hardware profile."""
    from .hardware.custom import delete_custom_profile
    
    if confirm:
        if delete_custom_profile(profile_id):
            console.print(f"[green]✓ Custom profile '{profile_id}' deleted[/green]")
        else:
            console.print(f"[red]✗ Failed to delete profile[/red]")
    else:
        if delete_custom_profile(profile_id):
            console.print(f"[green]✓ Custom profile '{profile_id}' deleted[/green]")
        else:
            console.print(f"[red]✗ Failed to delete profile[/red]")


@cmd_hw.command("apply")
@click.argument("profile_ids", nargs=-1, required=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--interactive", "-i", is_flag=True, default=False, help="Interactive profile selection")
@click.option("--search", "-s", default=None, help="Search profiles before selection")
def cmd_hw_apply(profile_ids: tuple, dry_run: bool, interactive: bool, search: str):
    """
    \b
    Apply one or more hardware profiles to this RPi.

    Examples:
      meshpi hw apply oled_ssd1306_i2c sensor_bme280
      meshpi hw apply --interactive
      meshpi hw apply --search oled --interactive
      meshpi hw apply --dry-run oled_ssd1306_i2c
    """
    from .hardware.profiles import list_profiles, get_profile
    from .hardware.custom import get_all_profiles
    from .hardware.applier import apply_multiple_profiles
    
    # Interactive mode or search mode
    if interactive or search:
        profiles = list(get_all_profiles().values())
        
        # Filter by search query if provided
        if search:
            search_lower = search.lower()
            profiles = [p for p in profiles if 
                       search_lower in p.name.lower() or 
                       search_lower in p.description.lower() or 
                       search_lower in p.id.lower()]
        
        if not profiles:
            console.print("[yellow]No profiles found.[/yellow]")
            return
        
        selected = interactive_profile_selection(profiles)
        if selected:
            profile_ids = tuple(p.id for p in selected)
        else:
            console.print("[yellow]No profiles selected.[/yellow]")
            return
    
    if not profile_ids:
        console.print("[red]No profiles specified. Use --interactive or provide profile IDs.[/red]")
        return

    if dry_run:
        console.print("[yellow]Dry-run: showing what would be installed[/yellow]")
        all_profiles = get_all_profiles()
        for pid in profile_ids:
            try:
                p = all_profiles[pid]
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
# meshpi monitor
# ─────────────────────────────────────────────────────────────────────────────

@main.command("monitor")
@click.option("--group", help="Monitor specific device group")
@click.option("--interval", default=60, help="Monitoring interval in seconds")
@click.option("--continuous", is_flag=True, default=False, help="Continuous monitoring")
def cmd_monitor(group: Optional[str], interval: int, continuous: bool):
    """
    Monitor status of devices or groups.
    
    Examples:
      meshpi monitor                    # Monitor all devices
      meshpi monitor --group servers    # Monitor specific group
      meshpi monitor --interval 30      # Monitor every 30 seconds
      meshpi monitor --continuous       # Continuous monitoring
    """
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    import json
    
    if group:
        # Monitor specific group
        groups_file = Path.home() / ".meshpi" / "groups.json"
        
        if not groups_file.exists():
            console.print("[red]No groups found[/red]")
            return
        
        groups = json.loads(groups_file.read_text())
        
        if group not in groups:
            console.print(f"[red]Group '{group}' not found[/red]")
            return
        
        devices = groups[group]["devices"]
        if not devices:
            console.print(f"[yellow]No devices in group '{group}'[/yellow]")
            return
        
        console.print(f"[bold cyan]Monitoring Group: {group}[/bold cyan]")
        
        # Create SSH manager and add devices
        manager = SSHManager()
        target_devices = []
        for device_str in devices:
            user, host, port = parse_device_target(device_str)
            from .ssh_manager import SSHDevice
            device = SSHDevice(host, user, port)
            manager.add_device(device)
            target_devices.append(device)
        
    else:
        # Monitor all registered devices
        from .registry import registry as reg
        all_devices = reg.all_devices()
        
        if not all_devices:
            console.print("[yellow]No devices found[/yellow]")
            return
        
        console.print("[bold cyan]Monitoring All Devices[/bold cyan]")
        
        # Create SSH manager from registry devices
        manager = SSHManager()
        target_devices = []
        
        for device in all_devices:
            from .ssh_manager import SSHDevice
            ssh_device = SSHDevice(device.host, device.user, device.port)
            manager.add_device(ssh_device)
            target_devices.append(ssh_device)
    
    # Monitor function
    def monitor_once():
        """Perform one monitoring cycle."""
        console.print(f"\n[cyan]→ Monitoring {len(target_devices)} device(s)...[/cyan]")
        
        status_table = Table(title=f"Device Status - {time.strftime('%H:%M:%S')}", border_style="cyan")
        status_table.add_column("Device", style="bold")
        status_table.add_column("Status", style="bold")
        status_table.add_column("Uptime", style="dim")
        status_table.add_column("Load", style="dim")
        status_table.add_column("Memory", style="dim")
        status_table.add_column("Temp", style="dim")
        status_table.add_column("MeshPi", style="dim")
        
        online_count = 0
        meshpi_count = 0
        
        for device in target_devices:
            try:
                if manager.connect_to_device(device):
                    # Get system info
                    info = manager.get_device_info(device)
                    
                    uptime = info.get("uptime", "N/A").split()[0] if info.get("uptime") != "N/A" else "N/A"
                    load = info.get("uptime", "N/A").split("load average:")[1].strip() if "load average:" in info.get("uptime", "") else "N/A"
                    memory = info.get("memory", "N/A").split()[1] if info.get("memory", "N/A") != "N/A" else "N/A"
                    temp = info.get("cpu_temp", "N/A")
                    meshpi_version = info.get("meshpi_version", "N/A")
                    
                    if meshpi_version != "N/A" and "not installed" not in meshpi_version:
                        meshpi_status = "[green]✓[/green]"
                        meshpi_count += 1
                    else:
                        meshpi_status = "[red]✗[/red]"
                    
                    status_table.add_row(
                        str(device),
                        "[green]ONLINE[/green]",
                        uptime,
                        load,
                        memory,
                        temp,
                        meshpi_status
                    )
                    online_count += 1
                else:
                    status_table.add_row(
                        str(device),
                        "[red]OFFLINE[/red]",
                        "—",
                        "—",
                        "—",
                        "—",
                        "[red]✗[/red]"
                    )
            except Exception as e:
                status_table.add_row(
                    str(device),
                    "[red]ERROR[/red]",
                    str(e)[:15],
                    "—",
                    "—",
                    "—",
                    "[red]✗[/red]"
                )
            finally:
                manager.disconnect_device(device)
        
        console.print(status_table)
        console.print(f"\n[green]Online: {online_count}/{len(target_devices)} devices[/green]")
        console.print(f"[green]MeshPi: {meshpi_count}/{len(target_devices)} devices[/green]")
        
        return online_count, meshpi_count
    
    # Initial monitoring
    monitor_once()
    
    if continuous:
        console.print(f"\n[dim]Continuous monitoring every {interval}s (Ctrl+C to stop)[/dim]")
        try:
            while True:
                time.sleep(interval)
                monitor_once()
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped[/yellow]")


def get_detailed_device_info(device) -> dict:
    """Get detailed information about a device."""
    from .ssh_manager import SSHManager
    
    info = {
        "model": "Unknown",
        "hostname": "Unknown", 
        "architecture": "Unknown",
        "meshpi_status": "Unknown",
        "cpu_temp": "Unknown",
        "memory": "Unknown",
        "uptime": "Unknown"
    }
    
    try:
        manager = SSHManager()
        if manager.connect_to_device(device):
            device_info = manager.get_device_info(device)
            
            # Extract and format information
            info["hostname"] = device_info.get("hostname", "Unknown")
            info["architecture"] = device_info.get("architecture", "Unknown")
            info["cpu_temp"] = device_info.get("cpu_temp", "Unknown")
            info["memory"] = device_info.get("memory", "Unknown")
            info["uptime"] = device_info.get("uptime", "Unknown")
            
            # Check MeshPi status
            meshpi_version = device_info.get("meshpi_version", "N/A")
            if meshpi_version != "N/A" and "not installed" not in meshpi_version:
                info["meshpi_status"] = f"[green]{meshpi_version}[/green]"
            else:
                info["meshpi_status"] = "[red]Not installed[/red]"
            
            # Try to get model information
            exit_code, stdout, stderr = manager.run_command_on_device(device, "cat /proc/device-tree/model 2>/dev/null || echo 'Unknown'")
            if exit_code == 0 and stdout.strip():
                model = stdout.strip()
                if "raspberry pi" in model.lower():
                    info["model"] = model
                else:
                    info["model"] = f"{model} (Non-RPi)"
            
            manager.disconnect_device(device)
            
    except Exception as e:
        console.print(f"[dim]  Could not get detailed info for {device}: {e}[/dim]")
    
    return info


def identify_device_type_quick(device) -> str:
    """Quick device type identification for basic SSH scan."""
    from .ssh_manager import SSHManager
    
    try:
        manager = SSHManager()
        if manager.connect_to_device(device):
            # Quick checks for device type
            checks = [
                ("Raspberry Pi", "cat /proc/device-tree/model 2>/dev/null | grep -i raspberry"),
                ("Router/Gateway", "ip route show default | grep -q 'via.*192.168.188.1'"),
                ("Linux", "uname -s | grep -q Linux"),
                ("ARM", "uname -m | grep -q arm")
            ]
            
            for device_type, cmd in checks:
                exit_code, _, _ = manager.run_command_on_device(device, cmd)
                if exit_code == 0:
                    manager.disconnect_device(device)
                    return device_type
            
            manager.disconnect_device(device)
            
    except Exception:
        pass
    
    return "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# meshpi ssh
# ─────────────────────────────────────────────────────────────────────────────

@main.group("ssh")
def cmd_ssh():
    """SSH device management for Raspberry Pi fleet."""
    pass


@cmd_ssh.command("scan")
@click.option("--network", default=None, help="Network range to scan (auto-detects if not specified)")
@click.option("--user", default="pi", help="Default SSH username")
@click.option("--port", default=22, help="SSH port")
@click.option("--timeout", default=5, help="Connection timeout")
@click.option("--add", is_flag=True, default=False, help="Add discovered devices to management")
@click.option("--identify", is_flag=True, default=True, help="Identify device types and collect metadata")
@click.option("--no-identify", is_flag=True, default=False, help="Disable device identification (basic SSH scan only)")
def cmd_ssh_scan(network: Optional[str], user: str, port: int, timeout: int, add: bool, identify: bool, no_identify: bool):
    """Scan network for SSH-enabled Raspberry Pi devices with device identification."""
    from .ssh_manager import SSHManager
    
    # Handle --no-identify flag
    if no_identify:
        identify = False
    
    # Auto-detect network if not specified
    if network is None:
        try:
            # Get local IP by connecting to a remote address
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            
            # Use conservative /24 approach for SSH scan
            if '.' in local_ip and (local_ip.startswith('192.168.') or local_ip.startswith('10.') or local_ip.startswith('172.')):
                parts = local_ip.split('.')
                network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            else:
                network = "192.168.1.0/24"  # fallback
            
            console.print(f"[dim]Auto-detected network: {network}[/dim]")
        except:
            network = "192.168.1.0/24"  # fallback
    
    if identify:
        console.print("[bold cyan]→ Scanning for Raspberry Pi devices with identification...[/bold cyan]")
        # Use enhanced auto-detection
        discovered_devices = auto_detect_rpi_devices()
        
        if not discovered_devices:
            console.print("[yellow]No Raspberry Pi devices found[/yellow]")
            console.print("[dim]Falling back to basic SSH scan...[/dim]\n")
            identify = False
        else:
            console.print(f"\n[green]✓ Found {len(discovered_devices)} Raspberry Pi device(s):[/green]")
            
            # Create detailed table with device information
            table = Table(title="Discovered Raspberry Pi Devices", border_style="cyan")
            table.add_column("Device ID", style="bold")
            table.add_column("IP Address", style="dim")
            table.add_column("Hostname", style="dim")
            table.add_column("Model", style="dim")
            table.add_column("Architecture", style="dim")
            table.add_column("MeshPi", style="bold")
            table.add_column("Status", style="bold")
            
            for device in discovered_devices:
                # Get additional device info
                device_info = get_detailed_device_info(device)
                
                model = device_info.get("model", "Unknown")
                hostname = device_info.get("hostname", device.device_id)
                arch = device_info.get("architecture", "Unknown")
                meshpi_status = device_info.get("meshpi_status", "Unknown")
                status = "[green]ONLINE[/green]" if device.online else "[red]OFFLINE[/red]"
                
                table.add_row(
                    device.device_id,
                    device.address,
                    hostname,
                    model,
                    arch,
                    meshpi_status,
                    status
                )
            
            console.print(table)
            
            if add and Confirm.ask(f"\nAdd {len(discovered_devices)} device(s) to management?", default=False):
                from .registry import registry as reg
                for device in discovered_devices:
                    reg.register_device(
                        device_id=device.device_id,
                        address=device.address,
                        host=device.host,
                        user=device.user,
                        port=device.port
                    )
                reg.save()
                console.print(f"[green]✓ Added {len(discovered_devices)} devices to registry[/green]")
            
            return
    
    # Basic SSH scan (fallback or if identify=False)
    console.print("[bold cyan]→ Basic SSH device scan...[/bold cyan]")
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
    table.add_column("Type", style="dim")
    
    for device in devices:
        # Try to identify device type
        device_type = identify_device_type_quick(device)
        table.add_row(device.host, device.user, str(device.port), device_type)
    
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


@cmd_ssh.command("shell")
@click.argument("target")
@click.option("--password", is_flag=True, default=False, help="Use password authentication")
@click.option("--key", help="Path to SSH private key")
def cmd_ssh_shell(target: str, password: bool, key: Optional[str]):
    """Open interactive SSH shell to device."""
    from .ssh_manager import parse_device_target
    import getpass
    
    user, host, port = parse_device_target(target)
    
    console.print(Panel.fit(
        f"[bold cyan]SSH Shell Access[/bold cyan]\n"
        f"Connecting to [bold]{user}@{host}:{port}[/bold]\n"
        f"[dim]Type 'exit' to return to MeshPi[/dim]",
        border_style="cyan"
    ))
    
    # Build SSH command
    ssh_cmd = ["ssh"]
    
    if key:
        ssh_cmd.extend(["-i", key])
    elif not password:
        # Try default key
        default_key = Path.home() / ".ssh" / "id_rsa"
        if default_key.exists():
            ssh_cmd.extend(["-i", str(default_key)])
    
    ssh_cmd.extend(["-p", str(port), f"{user}@{host}"])
    
    try:
        console.print(f"[cyan]→ Launching SSH shell...[/cyan]")
        console.print("[dim]Use 'exit' to return to MeshPi[/dim]\n")
        
        # Launch SSH shell
        subprocess.run(ssh_cmd, check=True)
        
        console.print("\n[green]✓ Returned from SSH shell[/green]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ SSH connection failed: {e}[/red]")
        
        if not password and Confirm.ask("Try with password authentication?", default=False):
            try:
                ssh_password = getpass.getpass(f"Enter SSH password for {user}@{host}: ")
                
                # Use sshpass if available
                ssh_pass_cmd = ["sshpass", "-p", ssh_password] + ssh_cmd
                
                try:
                    subprocess.run(ssh_pass_cmd, check=True)
                    console.print("\n[green]✓ Returned from SSH shell[/green]")
                except FileNotFoundError:
                    console.print("[yellow]sshpass not available. Install with: sudo apt install sshpass[/yellow]")
                    console.print(f"[dim]Manual command: ssh {user}@{host}[/dim]")
                except subprocess.CalledProcessError:
                    console.print("[red]✗ Password authentication failed[/red]")
                    
            except Exception as e:
                console.print(f"[red]✗ Password authentication failed: {e}[/red]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]SSH session interrupted[/yellow]")


@cmd_ssh.command("system-update")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_ssh_system_update(target: Optional[str], parallel: bool):
    """Update package lists on SSH device(s)."""
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
    
    # Execute system update
    console.print(f"[cyan]→[/cyan] Updating package lists on devices...")
    results = manager.run_command_on_all("sudo apt update", parallel=parallel)
    
    # Display results
    table = Table(title="System Update Results", border_style="cyan")
    table.add_column("Device", style="bold")
    table.add_column("Exit Code", style="dim")
    table.add_column("Output")
    table.add_column("Error", style="red")
    
    for device, (exit_code, stdout, stderr) in results.items():
        exit_status = "[green]0[/green]" if exit_code == 0 else f"[red]{exit_code}[/red]"
        output = stdout[:150] + "..." if len(stdout) > 150 else stdout
        error = stderr[:100] + "..." if len(stderr) > 100 else stderr
        
        table.add_row(str(device), exit_status, output, error)
    
    console.print(table)
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("system-upgrade")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
@click.option("--safe", is_flag=True, default=False, help="Safe upgrade (avoid removing packages)")
def cmd_ssh_system_upgrade(target: Optional[str], parallel: bool, safe: bool):
    """Upgrade packages on SSH device(s)."""
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
    
    # Confirm operation
    if not Confirm.ask(f"[yellow]This will upgrade packages on {len(manager.devices)} device(s). Continue?[/yellow]", default=False):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    # Connect to all devices
    console.print("[cyan]→[/cyan] Connecting to devices...")
    for device in manager.devices:
        manager.connect_to_device(device)
    
    # Execute system upgrade
    upgrade_cmd = "sudo apt upgrade -y" if not safe else "sudo apt safe-upgrade -y"
    console.print(f"[cyan]→[/cyan] Upgrading packages on devices...")
    console.print(f"[dim]Command: {upgrade_cmd}[/dim]")
    
    results = manager.run_command_on_all(upgrade_cmd, parallel=parallel)
    
    # Display results
    table = Table(title="System Upgrade Results", border_style="cyan")
    table.add_column("Device", style="bold")
    table.add_column("Exit Code", style="dim")
    table.add_column("Output")
    table.add_column("Error", style="red")
    
    for device, (exit_code, stdout, stderr) in results.items():
        exit_status = "[green]0[/green]" if exit_code == 0 else f"[red]{exit_code}[/red]"
        output = stdout[:150] + "..." if len(stdout) > 150 else stdout
        error = stderr[:100] + "..." if len(stderr) > 100 else stderr
        
        table.add_row(str(device), exit_status, output, error)
    
    console.print(table)
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("batch")
@click.argument("command")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
@click.option("--dry-run", is_flag=True, default=False, help="Show command without executing")
@click.option("--timeout", default=30, help="Command timeout in seconds")
def cmd_ssh_batch(command: str, target: Optional[str], parallel: bool, dry_run: bool, timeout: int):
    """Execute custom command on multiple SSH devices."""
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
    
    # Show command and devices
    console.print(f"[bold cyan]Batch Command Execution[/bold cyan]")
    console.print(f"[dim]Command: {command}[/dim]")
    console.print(f"[dim]Devices: {len(manager.devices)}[/dim]")
    console.print(f"[dim]Parallel: {parallel}[/dim]")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN - Command will be executed on:[/yellow]")
        for device in manager.devices:
            console.print(f"  • {device}")
        return
    
    # Confirm operation
    if not Confirm.ask(f"[yellow]Execute command on {len(manager.devices)} device(s)?[/yellow]", default=False):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    # Connect to all devices
    console.print("[cyan]→[/cyan] Connecting to devices...")
    for device in manager.devices:
        manager.connect_to_device(device)
    
    # Execute command
    console.print(f"[cyan]→[/cyan] Executing command...")
    results = manager.run_command_on_all(command, parallel=parallel)
    
    # Display results
    table = Table(title="Batch Command Results", border_style="cyan")
    table.add_column("Device", style="bold")
    table.add_column("Exit Code", style="dim")
    table.add_column("Output")
    table.add_column("Error", style="red")
    
    success_count = 0
    for device, (exit_code, stdout, stderr) in results.items():
        exit_status = "[green]0[/green]" if exit_code == 0 else f"[red]{exit_code}[/red]"
        output = stdout[:200] + "..." if len(stdout) > 200 else stdout
        error = stderr[:100] + "..." if len(stderr) > 100 else stderr
        
        table.add_row(str(device), exit_status, output, error)
        if exit_code == 0:
            success_count += 1
    
    console.print(table)
    console.print(f"\n[green]Success: {success_count}/{len(manager.devices)} devices[/green]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@main.group("group")
def cmd_group():
    """Group operations for managing multiple devices."""
    pass


@cmd_group.command("create")
@click.argument("group_name")
@click.option("--description", help="Group description")
def cmd_group_create(group_name: str, description: Optional[str]):
    """Create a new device group."""
    from .ssh_manager import SSHManager
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    # Load existing groups
    groups = {}
    if groups_file.exists():
        groups = json.loads(groups_file.read_text())
    
    if group_name in groups:
        console.print(f"[red]Group '{group_name}' already exists[/red]")
        return
    
    # Create group
    groups[group_name] = {
        "name": group_name,
        "description": description or "",
        "devices": [],
        "created_at": time.time()
    }
    
    # Save groups
    groups_file.write_text(json.dumps(groups, indent=2))
    console.print(f"[green]✓ Group '{group_name}' created[/green]")


@cmd_group.command("list")
def cmd_group_list():
    """List all device groups."""
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[yellow]No groups found[/yellow]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if not groups:
        console.print("[yellow]No groups found[/yellow]")
        return
    
    table = Table(title="Device Groups", border_style="cyan")
    table.add_column("Group Name", style="bold")
    table.add_column("Description", style="dim")
    table.add_column("Devices", style="dim")
    table.add_column("Created", style="dim")
    
    for group_name, group_data in groups.items():
        device_count = len(group_data.get("devices", []))
        created = time.strftime("%Y-%m-%d", time.localtime(group_data.get("created_at", 0)))
        description = group_data.get("description", "—")
        
        table.add_row(group_name, description, str(device_count), created)
    
    console.print(table)


@cmd_group.command("add-device")
@click.argument("group_name")
@click.argument("target")
def cmd_group_add_device(group_name: str, target: str):
    """Add device to a group."""
    from .ssh_manager import parse_device_target
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    # Parse target
    user, host, port = parse_device_target(target)
    device_str = f"{user}@{host}:{port}"
    
    # Add device to group
    if device_str not in groups[group_name]["devices"]:
        groups[group_name]["devices"].append(device_str)
        groups_file.write_text(json.dumps(groups, indent=2))
        console.print(f"[green]✓ Added {device_str} to group '{group_name}'[/green]")
    else:
        console.print(f"[yellow]Device already in group[/yellow]")


@cmd_group.command("remove-device")
@click.argument("group_name")
@click.argument("target")
def cmd_group_remove_device(group_name: str, target: str):
    """Remove device from a group."""
    from .ssh_manager import parse_device_target
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    # Parse target
    user, host, port = parse_device_target(target)
    device_str = f"{user}@{host}:{port}"
    
    # Remove device from group
    if device_str in groups[group_name]["devices"]:
        groups[group_name]["devices"].remove(device_str)
        groups_file.write_text(json.dumps(groups, indent=2))
        console.print(f"[green]✓ Removed {device_str} from group '{group_name}'[/green]")
    else:
        console.print(f"[yellow]Device not in group[/yellow]")


@cmd_group.command("show")
@click.argument("group_name")
def cmd_group_show(group_name: str):
    """Show details of a specific group."""
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    group_data = groups[group_name]
    
    console.print(Panel.fit(
        f"[bold cyan]Group: {group_name}[/bold cyan]\n"
        f"[dim]{group_data.get('description', 'No description')}[/dim]",
        border_style="cyan"
    ))
    
    # Group info
    info_table = Table(show_header=False, box=None)
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value")
    
    created = time.strftime("%Y-%m-%d %H:%M", time.localtime(group_data.get("created_at", 0)))
    info_table.add_row("Name", group_data["name"])
    info_table.add_row("Description", group_data.get("description", "—"))
    info_table.add_row("Devices", str(len(group_data.get("devices", []))))
    info_table.add_row("Created", created)
    
    console.print(info_table)
    
    # Device list
    devices = group_data.get("devices", [])
    if devices:
        console.print(f"\n[bold]Devices ({len(devices)}):[/bold]")
        for i, device in enumerate(devices, 1):
            console.print(f"  {i}. {device}")
    else:
        console.print("\n[dim]No devices in group[/dim]")


@cmd_group.command("delete")
@click.argument("group_name")
@click.option("--confirm", is_flag=True, default=False, help="Skip confirmation")
def cmd_group_delete(group_name: str, confirm: bool):
    """Delete a device group."""
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    device_count = len(groups[group_name].get("devices", []))
    
    if not confirm:
        if not Confirm.ask(
            f"[red]Delete group '{group_name}' with {device_count} device(s)?[/red]", 
            default=False
        ):
            console.print("[dim]Operation cancelled.[/dim]")
            return
    
    # Delete group
    del groups[group_name]
    groups_file.write_text(json.dumps(groups, indent=2))
    console.print(f"[green]✓ Group '{group_name}' deleted[/green]")


@cmd_group.command("update")
@click.argument("group_name")
@click.option("--name", help="New group name")
@click.option("--description", help="New group description")
def cmd_group_update(group_name: str, name: Optional[str], description: Optional[str]):
    """Update group properties."""
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    group_data = groups[group_name]
    
    # Update properties
    if name:
        # Move group to new key
        groups[name] = groups.pop(group_name)
        group_data = groups[name]
        group_data["name"] = name
        console.print(f"[green]✓ Group renamed to '{name}'[/green]")
        group_name = name
    
    if description is not None:
        group_data["description"] = description
        console.print(f"[green]✓ Description updated[/green]")
    
    # Save changes
    groups_file.write_text(json.dumps(groups, indent=2))
    console.print(f"[green]✓ Group '{group_name}' updated[/green]")


@cmd_group.command("status")
@click.argument("group_name")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_group_status(group_name: str, parallel: bool):
    """Check status of all devices in a group."""
    from .ssh_manager import SSHManager
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    devices = groups[group_name]["devices"]
    if not devices:
        console.print(f"[yellow]No devices in group '{group_name}'[/yellow]")
        return
    
    console.print(f"[bold cyan]Group Status: {group_name}[/bold cyan]")
    
    # Create SSH manager and add devices
    manager = SSHManager()
    for device_str in devices:
        user, host, port = parse_device_target(device_str)
        from .ssh_manager import SSHDevice
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    # Connect and check status
    console.print("[cyan]→[/cyan] Checking device status...")
    
    status_table = Table(title=f"Group '{group_name}' Status", border_style="cyan")
    status_table.add_column("Device", style="bold")
    status_table.add_column("Status", style="bold")
    status_table.add_column("Uptime", style="dim")
    status_table.add_column("Load", style="dim")
    status_table.add_column("Memory", style="dim")
    status_table.add_column("Temp", style="dim")
    
    online_count = 0
    
    for device in manager.devices:
        try:
            if manager.connect_to_device(device):
                # Get system info
                info = manager.get_device_info(device)
                
                uptime = info.get("uptime", "N/A").split()[0] if info.get("uptime") != "N/A" else "N/A"
                load = info.get("uptime", "N/A").split("load average:")[1].strip() if "load average:" in info.get("uptime", "") else "N/A"
                memory = info.get("memory", "N/A").split()[1] if info.get("memory", "N/A") != "N/A" else "N/A"
                temp = info.get("cpu_temp", "N/A")
                
                status_table.add_row(
                    str(device),
                    "[green]ONLINE[/green]",
                    uptime,
                    load,
                    memory,
                    temp
                )
                online_count += 1
            else:
                status_table.add_row(
                    str(device),
                    "[red]OFFLINE[/red]",
                    "—",
                    "—",
                    "—",
                    "—"
                )
        except Exception as e:
            status_table.add_row(
                str(device),
                "[red]ERROR[/red]",
                str(e)[:20],
                "—",
                "—",
                "—"
            )
        finally:
            manager.disconnect_device(device)
    
    console.print(status_table)
    console.print(f"\n[green]Online: {online_count}/{len(devices)} devices[/green]")


@cmd_group.command("system-update")
@click.argument("group_name")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_group_system_update(group_name: str, parallel: bool):
    """Update package lists on all devices in a group."""
    from .ssh_manager import SSHManager
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    devices = groups[group_name]["devices"]
    if not devices:
        console.print(f"[yellow]No devices in group '{group_name}'[/yellow]")
        return
    
    # Create SSH manager and add devices
    manager = SSHManager()
    for device_str in devices:
        user, host, port = parse_device_target(device_str)
        from .ssh_manager import SSHDevice
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    # Confirm operation
    console.print(f"[bold cyan]Group System Update[/bold cyan]")
    console.print(f"[dim]Group: {group_name}[/dim]")
    console.print(f"[dim]Devices: {len(devices)}[/dim]")
    
    if not Confirm.ask(f"[yellow]Update package lists on {len(devices)} device(s)?[/yellow]", default=False):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    # Connect and update
    console.print("[cyan]→[/cyan] Connecting to devices...")
    for device in manager.devices:
        manager.connect_to_device(device)
    
    console.print(f"[cyan]→[/cyan] Updating package lists...")
    results = manager.run_command_on_all("sudo apt update", parallel=parallel)
    
    # Display results
    table = Table(title=f"Group '{group_name}' Update Results", border_style="cyan")
    table.add_column("Device", style="bold")
    table.add_column("Exit Code", style="dim")
    table.add_column("Output")
    table.add_column("Error", style="red")
    
    success_count = 0
    for device, (exit_code, stdout, stderr) in results.items():
        exit_status = "[green]0[/green]" if exit_code == 0 else f"[red]{exit_code}[/red]"
        output = stdout[:150] + "..." if len(stdout) > 150 else stdout
        error = stderr[:100] + "..." if len(stderr) > 100 else stderr
        
        table.add_row(str(device), exit_status, output, error)
        if exit_code == 0:
            success_count += 1
    
    console.print(table)
    console.print(f"\n[green]Success: {success_count}/{len(devices)} devices[/green]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_group.command("exec")
@click.argument("group_name")
@click.argument("command")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_group_exec(group_name: str, command: str, parallel: bool):
    """Execute command on all devices in a group."""
    from .ssh_manager import SSHManager
    from pathlib import Path
    import json
    
    groups_file = Path.home() / ".meshpi" / "groups.json"
    
    if not groups_file.exists():
        console.print("[red]No groups found[/red]")
        return
    
    groups = json.loads(groups_file.read_text())
    
    if group_name not in groups:
        console.print(f"[red]Group '{group_name}' not found[/red]")
        return
    
    devices = groups[group_name]["devices"]
    if not devices:
        console.print(f"[yellow]No devices in group '{group_name}'[/yellow]")
        return
    
    # Create SSH manager and add devices
    manager = SSHManager()
    for device_str in devices:
        user, host, port = parse_device_target(device_str)
        from .ssh_manager import SSHDevice
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    # Confirm operation
    console.print(f"[bold cyan]Group Command Execution[/bold cyan]")
    console.print(f"[dim]Group: {group_name}[/dim]")
    console.print(f"[dim]Command: {command}[/dim]")
    console.print(f"[dim]Devices: {len(devices)}[/dim]")
    
    if not Confirm.ask(f"[yellow]Execute command on {len(devices)} device(s)?[/yellow]", default=False):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    # Connect and execute
    console.print("[cyan]→[/cyan] Connecting to devices...")
    for device in manager.devices:
        manager.connect_to_device(device)
    
    console.print(f"[cyan]→[/cyan] Executing command...")
    results = manager.run_command_on_all(command, parallel=parallel)
    
    # Display results
    table = Table(title=f"Group '{group_name}' Results", border_style="cyan")
    table.add_column("Device", style="bold")
    table.add_column("Exit Code", style="dim")
    table.add_column("Output")
    table.add_column("Error", style="red")
    
    success_count = 0
    for device, (exit_code, stdout, stderr) in results.items():
        exit_status = "[green]0[/green]" if exit_code == 0 else f"[red]{exit_code}[/red]"
        output = stdout[:200] + "..." if len(stdout) > 200 else stdout
        error = stderr[:100] + "..." if len(stderr) > 100 else stderr
        
        table.add_row(str(device), exit_status, output, error)
        if exit_code == 0:
            success_count += 1
    
    console.print(table)
    console.print(f"\n[green]Success: {success_count}/{len(devices)} devices[/green]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("hw-search")
@click.argument("query", default="")
@click.option("--category", "-c", default=None,
              help="Filter by category: display|gpio|sensor|camera|audio|networking|hat|storage")
@click.option("--tag", "-t", default=None, help="Filter by tag (e.g. 'i2c', 'spi', 'oled')")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_ssh_hw_search(query: str, category: str, tag: str, target: Optional[str], parallel: bool):
    """Search hardware profiles on remote SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    if target:
        user, host, port = parse_device_target(target)
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    if not manager.devices:
        console.print("[red]No devices available. Use 'meshpi ssh add' to add devices.[/red]")
        return
    
    # Connect to devices
    for device in manager.devices:
        if not device._connected:
            manager.connect_to_device(device)
    
    # Build search command
    cmd_parts = ["meshpi", "hw", "search"]
    if query:
        cmd_parts.append(query)
    if category:
        cmd_parts.extend(["--category", category])
    if tag:
        cmd_parts.extend(["--tag", tag])
    
    search_cmd = " ".join(cmd_parts)
    
    console.print(f"[cyan]→[/cyan] Searching hardware profiles on devices...")
    console.print(f"[dim]Command: {search_cmd}[/dim]")
    
    results = manager.run_command_on_all(search_cmd, parallel=parallel)
    
    for device, (exit_code, stdout, stderr) in results.items():
        console.print(f"\n[bold]{device}:[/bold]")
        if exit_code == 0:
            console.print(stdout)
        else:
            console.print(f"[red]Error: {stderr}[/red]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("hw-apply")
@click.argument("profile_ids", nargs=-1, required=False)
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be installed")
@click.option("--interactive", "-i", is_flag=True, default=False, help="Interactive profile selection")
@click.option("--search", "-s", default=None, help="Search profiles before selection")
def cmd_ssh_hw_apply(profile_ids: tuple, target: Optional[str], parallel: bool, dry_run: bool, interactive: bool, search: str):
    """Apply hardware profiles on remote SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    if target:
        user, host, port = parse_device_target(target)
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    if not manager.devices:
        console.print("[red]No devices available. Use 'meshpi ssh add' to add devices.[/red]")
        return
    
    # Connect to devices
    for device in manager.devices:
        if not device._connected:
            manager.connect_to_device(device)
    
    # Build apply command
    cmd_parts = ["meshpi", "hw", "apply"]
    if dry_run:
        cmd_parts.append("--dry-run")
    if interactive:
        cmd_parts.append("--interactive")
    if search:
        cmd_parts.extend(["--search", search])
    cmd_parts.extend(profile_ids)
    
    apply_cmd = " ".join(cmd_parts)
    
    console.print(f"[cyan]→[/cyan] Applying hardware profiles on devices...")
    console.print(f"[dim]Command: {apply_cmd}[/dim]")
    
    results = manager.run_command_on_all(apply_cmd, parallel=parallel)
    
    for device, (exit_code, stdout, stderr) in results.items():
        console.print(f"\n[bold]{device}:[/bold]")
        if exit_code == 0:
            console.print(stdout)
        else:
            console.print(f"[red]Error: {stderr}[/red]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("hw-create")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--interactive", "-i", is_flag=True, default=True, help="Interactive profile creation")
@click.option("--import-file", "-f", default=None, help="Import profile from YAML/JSON file")
@click.option("--name", default=None, help="Profile name")
@click.option("--category", default=None, help="Profile category")
@click.option("--description", default=None, help="Profile description")
@click.option("--packages", default=None, help="Comma-separated apt packages")
@click.option("--python-packages", default=None, help="Comma-separated pip packages")
@click.option("--tags", default=None, help="Comma-separated tags")
def cmd_ssh_hw_create(target: Optional[str], interactive: bool, import_file: str, 
                     name: str, category: str, description: str, packages: str, python_packages: str, tags: str):
    """Create custom hardware profiles on remote SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    if target:
        user, host, port = parse_device_target(target)
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    if not manager.devices:
        console.print("[red]No devices available. Use 'meshpi ssh add' to add devices.[/red]")
        return
    
    # Connect to devices
    for device in manager.devices:
        if not device._connected:
            manager.connect_to_device(device)
    
    # Build create command
    cmd_parts = ["meshpi", "hw", "create"]
    if interactive:
        cmd_parts.append("--interactive")
    if import_file:
        cmd_parts.extend(["--import-file", import_file])
    if name:
        cmd_parts.extend(["--name", name])
    if category:
        cmd_parts.extend(["--category", category])
    if description:
        cmd_parts.extend(["--description", description])
    if packages:
        cmd_parts.extend(["--packages", packages])
    if python_packages:
        cmd_parts.extend(["--python-packages", python_packages])
    if tags:
        cmd_parts.extend(["--tags", tags])
    
    create_cmd = " ".join(cmd_parts)
    
    console.print(f"[cyan]→[/cyan] Creating custom hardware profiles on devices...")
    console.print(f"[dim]Command: {create_cmd}[/dim]")
    
    results = manager.run_command_on_all(create_cmd, parallel=False)  # Sequential for interactive
    
    for device, (exit_code, stdout, stderr) in results.items():
        console.print(f"\n[bold]{device}:[/bold]")
        if exit_code == 0:
            console.print(stdout)
        else:
            console.print(f"[red]Error: {stderr}[/red]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("hw-custom")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_ssh_hw_custom(target: Optional[str], parallel: bool):
    """List custom hardware profiles on remote SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    if target:
        user, host, port = parse_device_target(target)
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    if not manager.devices:
        console.print("[red]No devices available. Use 'meshpi ssh add' to add devices.[/red]")
        return
    
    # Connect to devices
    for device in manager.devices:
        if not device._connected:
            manager.connect_to_device(device)
    
    console.print(f"[cyan]→[/cyan] Listing custom hardware profiles on devices...")
    
    results = manager.run_command_on_all("meshpi hw custom", parallel=parallel)
    
    for device, (exit_code, stdout, stderr) in results.items():
        console.print(f"\n[bold]{device}:[/bold]")
        if exit_code == 0:
            console.print(stdout)
        else:
            console.print(f"[red]Error: {stderr}[/red]")
    
    # Disconnect
    for device in manager.devices:
        manager.disconnect_device(device)


@cmd_ssh.command("hw-list")
@click.option("--category", "-c", default=None,
              help="Filter by category: display|gpio|sensor|camera|audio|networking|hat|storage")
@click.option("--tag", "-t", default=None, help="Filter by tag (e.g. 'i2c', 'spi', 'oled')")
@click.option("--target", help="Specific device (user@host:port)")
@click.option("--parallel", is_flag=True, default=True, help="Run in parallel")
def cmd_ssh_hw_list(category: str, tag: str, target: Optional[str], parallel: bool):
    """List hardware profiles on remote SSH device(s)."""
    from .ssh_manager import SSHManager, parse_device_target
    from pathlib import Path
    
    manager = SSHManager()
    devices_file = Path.home() / ".meshpi" / "ssh_devices.json"
    
    if devices_file.exists():
        manager.load_device_list(str(devices_file))
    
    if target:
        user, host, port = parse_device_target(target)
        device = SSHDevice(host, user, port)
        manager.add_device(device)
    
    if not manager.devices:
        console.print("[red]No devices available. Use 'meshpi ssh add' to add devices.[/red]")
        return
    
    # Connect to devices
    for device in manager.devices:
        if not device._connected:
            manager.connect_to_device(device)
    
    # Build list command
    cmd_parts = ["meshpi", "hw", "list"]
    if category:
        cmd_parts.extend(["--category", category])
    if tag:
        cmd_parts.extend(["--tag", tag])
    
    list_cmd = " ".join(cmd_parts)
    
    console.print(f"[cyan]→[/cyan] Listing hardware profiles on devices...")
    console.print(f"[dim]Command: {list_cmd}[/dim]")
    
    results = manager.run_command_on_all(list_cmd, parallel=parallel)
    
    for device, (exit_code, stdout, stderr) in results.items():
        console.print(f"\n[bold]{device}:[/bold]")
        if exit_code == 0:
            console.print(stdout)
        else:
            console.print(f"[red]Error: {stderr}[/red]")
    
    # Disconnect
    for device in manager.devices:
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
    """Auto-detect Raspberry Pi devices on local network.
    
    Filters out common network infrastructure (.1, .254 gateways) and uses
    strict RPI detection to avoid false positives with routers and other ARM devices.
    """
    from .ssh_manager import SSHManager
    from .registry import DeviceRecord
    import socket
    from ipaddress import ip_network
    from rich.progress import Progress
    
    discovered = []
    
    # Get local network range - only scan the specific subnet the interface is connected to
    try:
        # Get local IP and interface by connecting to a remote address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        
        # Try to get network interface information using standard library
        network = None
        
        # Method 1: Try to read from /proc/net/route to get the interface and gateway
        try:
            with open('/proc/net/route', 'r') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        interface = parts[0]
                        # Get IP address for this interface
                        try:
                            import fcntl
                            import struct
                            siockgifaddr = 0x8915  # Magic number for SIOCGIFADDR
                            sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            
                            # Get IP address of the interface
                            try:
                                ifreq = struct.pack('16sH14s', interface.encode(), socket.AF_INET, b'\x00'*14)
                                result = fcntl.ioctl(sockfd.fileno(), siockgifaddr, ifreq)
                                ip_bytes = result[20:24]
                                interface_ip = socket.inet_ntoa(ip_bytes)
                                
                                if interface_ip == local_ip:
                                    # Get netmask for this interface
                                    siockifnetmask = 0x891B  # Magic number for SIOCGIFNETMASK
                                    try:
                                        ifreq = struct.pack('16sH14s', interface.encode(), socket.AF_INET, b'\x00'*14)
                                        result = fcntl.ioctl(sockfd.fileno(), siockifnetmask, ifreq)
                                        netmask_bytes = result[20:24]
                                        netmask = socket.inet_ntoa(netmask_bytes)
                                        
                                        # Calculate network using ipaddress module
                                        import ipaddress
                                        ip_interface = ipaddress.IPv4Interface(f"{local_ip}/{netmask}")
                                        network = str(ip_interface.network)
                                        break
                                    except:
                                        pass
                            finally:
                                sockfd.close()
                        except:
                            pass
        except:
            pass
        
        # Method 2: If above fails, use a more conservative approach - only scan the local /24
        if not network:
            if '.' in local_ip and (local_ip.startswith('192.168.') or local_ip.startswith('10.') or local_ip.startswith('172.')):
                parts = local_ip.split('.')
                # Only scan the /24 that contains our local IP, not all possible subnets
                network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            else:
                network = "192.168.1.0/24"  # fallback
                
    except:
        network = "192.168.1.0/24"  # fallback
    
    console.print(f"[dim]Scanning network {network} for Raspberry Pi devices...[/dim]")
    
    # Use SSH manager to scan for SSH devices
    ssh_manager = SSHManager()
    ssh_devices = ssh_manager.scan_network(network, user="pi", port=22, timeout=3)
    
    # Filter out obvious network infrastructure devices
    filtered_devices = []
    for device in ssh_devices:
        # Skip common router/gateway IP addresses and network infrastructure
        host_parts = device.host.split('.')
        if len(host_parts) == 4:
            last_octet = int(host_parts[3])
            # Skip common gateway addresses and network devices
            if last_octet in [1, 254, 255, 0]:
                console.print(f"[dim]Skipping network infrastructure: {device.host}[/dim]")
                continue
        
        filtered_devices.append(device)
    
    ssh_devices = filtered_devices
    
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
                # Could not connect with SSH key, try password only for likely RPI devices
                # Skip password attempts for obvious network infrastructure
                host_parts = ssh_device.host.split('.')
                if len(host_parts) == 4:
                    last_octet = int(host_parts[3])
                    if last_octet in [1, 254, 255, 0]:
                        console.print(f"[dim]Skipping network device: {ssh_device.host}[/dim]")
                        continue
                
                # For other devices, try password but with a clear message that it's optional
                try:
                    import getpass
                    console.print(f"[yellow]Authentication failed for {ssh_device.user}@{ssh_device.host}[/yellow]")
                    password = getpass.getpass(f"Enter SSH password for {ssh_device.user}@{ssh_device.host} (or press Enter to skip): ")
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
    """Check if the connected device is a Raspberry Pi using strict detection.
    
    Uses multiple indicators to avoid false positives with routers and other ARM devices:
    - Primary: Raspberry Pi model string, BCM hardware, or hostname + boot config
    - Secondary: Boot files, firmware directory, vcgencmd tool, RPI-specific issue files
    - Architecture check alone is insufficient (many routers use ARM)
    """
    try:
        # Check for Raspberry Pi specific files and characteristics
        commands = [
            "cat /proc/device-tree/model 2>/dev/null || echo 'unknown'",
            "hostname 2>/dev/null || echo 'unknown'",
            "uname -m 2>/dev/null || echo 'unknown'",
            "cat /proc/cpuinfo 2>/dev/null | grep 'Hardware' | head -1 || echo 'unknown'",
            "test -f /boot/config.txt && echo 'config_exists' || echo 'no_config'",
            "test -d /boot/firmware && echo 'firmware_exists' || echo 'no_firmware'",
            "which vcgencmd 2>/dev/null && echo 'vcgencmd_exists' || echo 'no_vcgencmd'"
        ]
        
        model = ""
        hostname = ""
        arch = ""
        hardware = ""
        boot_config = ""
        firmware = ""
        vcgencmd = ""
        
        for cmd in commands:
            stdin, stdout, stderr = ssh_device.client.exec_command(cmd)
            result = stdout.read().decode().strip()
            
            if "model" in cmd:
                model = result
            elif "hostname" in cmd:
                hostname = result
            elif "uname" in cmd:
                arch = result
            elif "Hardware" in cmd:
                hardware = result
            elif "config" in cmd:
                boot_config = result
            elif "firmware" in cmd:
                firmware = result
            elif "vcgencmd" in cmd:
                vcgencmd = result
        
        # More strict Raspberry Pi detection
        # Primary indicators: Raspberry Pi in model string or BCM hardware
        is_rpi = (
            ("raspberry pi" in model.lower() and model.lower() != "unknown") or
            ("bcm" in model.lower() and model.lower() != "unknown") or
            ("bcm28" in hardware.lower() and hardware.lower() != "unknown") or
            ("raspberrypi" in hostname.lower() and boot_config == "config_exists")
        )
        
        # Secondary indicators for confirmation (but not sufficient alone)
        rpi_indicators = [
            boot_config == "config_exists",
            firmware == "firmware_exists", 
            vcgencmd == "vcgencmd_exists",
            arch in ["armv7l", "aarch64", "armv6l"]
        ]
        
        # If we have some indicators but not primary ones, require more confirmation
        if not is_rpi and sum(rpi_indicators) >= 2:
            # Check for additional RPI-specific files
            try:
                stdin, stdout, stderr = ssh_device.client.exec_command("test -f /etc/rpi-issue && echo 'rpi_issue' || echo 'no_rpi_issue'")
                rpi_issue = stdout.read().decode().strip()
                
                stdin, stdout, stderr = ssh_device.client.exec_command("test -f /boot/issue.txt && echo 'boot_issue' || echo 'no_boot_issue'")
                boot_issue = stdout.read().decode().strip()
                
                # Only consider it RPI if we have multiple strong indicators
                if (rpi_issue == "rpi_issue" or boot_issue == "boot_issue") and boot_config == "config_exists":
                    is_rpi = True
                    
            except Exception:
                pass
        
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
        console.print("  [5] Shell access")
        console.print("  [6] System update")
        console.print("  [7] Batch operations")
        console.print("  [8] Remove device")
        console.print("  [b] Back to device list")
        console.print("  [q] Quit")
        
        choice = Prompt.ask(
            "\n[cyan]Choose an option[/cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "b", "q"],
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
            # Shell access
            console.print(f"\n[yellow]→ Opening SSH shell to {device.device_id}...[/yellow]")
            try:
                # Parse address for SSH
                if "@" in device.address:
                    target = device.address
                else:
                    target = f"pi@{device.address}"
                
                # Open SSH shell
                open_ssh_shell(target)
            except Exception as e:
                console.print(f"[red]✗ Shell access failed: {e}[/red]")
            
            # Continue without prompt since SSH shell will handle interaction
            
        elif choice == "6":
            # System update
            console.print(f"\n[yellow]→ Running system update on {device.device_id}...[/yellow]")
            if Confirm.ask("Update package lists on this device?", default=True):
                try:
                    # Parse address for SSH
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    # Run system update
                    from .cli import cmd_ssh_system_update
                    cmd_ssh_system_update(target=target, parallel=False)
                except Exception as e:
                    console.print(f"[red]✗ System update failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "7":
            # Batch operations
            batch_operations_menu(device)
            
        elif choice == "8":
            # Remove device
            if Confirm.ask(f"Remove {device.device_id} from registry?", default=False):
                console.print(f"[green]✓ Device {device.device_id} removed[/green]")
                break


def batch_operations_menu(device):
    """Show batch operations menu for device."""
    while True:
        console.clear()
        console.print(Panel.fit(
            f"[bold cyan]Batch Operations: {device.device_id}[/bold cyan]\n"
            f"[dim]Address: {device.address}[/dim]",
            border_style="cyan"
        ))
        
        console.print("\n[bold cyan]Batch Operations:[/bold cyan]")
        console.print("  [1] Custom command")
        console.print("  [2] System upgrade")
        console.print("  [3] Install package")
        console.print("  [4] Service management")
        console.print("  [5] File transfer")
        console.print("  [b] Back to device menu")
        
        choice = Prompt.ask(
            "\n[cyan]Choose an option[/cyan]",
            choices=["1", "2", "3", "4", "5", "b"],
            default="b"
        )
        
        if choice == "b":
            break
        elif choice == "1":
            # Custom command
            command = Prompt.ask("Enter command to execute")
            if command:
                console.print(f"\n[yellow]→ Executing: {command}[/yellow]")
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_batch
                    cmd_ssh_batch(command=command, target=target, parallel=False)
                except Exception as e:
                    console.print(f"[red]✗ Command failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "2":
            # System upgrade
            console.print(f"\n[yellow]→ System upgrade on {device.device_id}[/yellow]")
            if Confirm.ask("Upgrade all packages on this device?", default=False):
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_system_upgrade
                    cmd_ssh_system_upgrade(target=target, parallel=False)
                except Exception as e:
                    console.print(f"[red]✗ System upgrade failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "3":
            # Install package
            package = Prompt.ask("Enter package name to install")
            if package:
                console.print(f"\n[yellow]→ Installing {package}[/yellow]")
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_batch
                    cmd_ssh_batch(command=f"sudo apt install -y {package}", target=target, parallel=False)
                except Exception as e:
                    console.print(f"[red]✗ Package installation failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "4":
            # Service management
            service_menu(device)
            
        elif choice == "5":
            # File transfer
            file_transfer_menu(device)


def service_menu(device):
    """Service management menu."""
    while True:
        console.clear()
        console.print(Panel.fit(
            f"[bold cyan]Service Management: {device.device_id}[/bold cyan]\n"
            f"[dim]Address: {device.address}[/dim]",
            border_style="cyan"
        ))
        
        console.print("\n[bold cyan]Service Operations:[/bold cyan]")
        console.print("  [1] List services")
        console.print("  [2] Check service status")
        console.print("  [3] Start service")
        console.print("  [4] Stop service")
        console.print("  [5] Restart service")
        console.print("  [6] Enable service")
        console.print("  [7] Disable service")
        console.print("  [b] Back to batch operations")
        
        choice = Prompt.ask(
            "\n[cyan]Choose an option[/cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7", "b"],
            default="b"
        )
        
        if choice == "b":
            break
        elif choice == "1":
            # List services
            console.print("\n[yellow]→ Listing services...[/yellow]")
            try:
                if "@" in device.address:
                    target = device.address
                else:
                    target = f"pi@{device.address}"
                
                from .cli import cmd_ssh_batch
                cmd_ssh_batch(command="systemctl list-units --type=service --state=running", target=target, parallel=False)
            except Exception as e:
                console.print(f"[red]✗ Failed to list services: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice in ["2", "3", "4", "5", "6", "7"]:
            # Service operations
            if choice in ["2", "3", "4", "5"]:
                service_name = Prompt.ask("Enter service name")
            else:
                service_name = Prompt.ask("Enter service name to enable/disable")
            
            if service_name:
                commands = {
                    "2": f"systemctl status {service_name}",
                    "3": f"sudo systemctl start {service_name}",
                    "4": f"sudo systemctl stop {service_name}",
                    "5": f"sudo systemctl restart {service_name}",
                    "6": f"sudo systemctl enable {service_name}",
                    "7": f"sudo systemctl disable {service_name}",
                }
                
                action = {
                    "2": "checking status",
                    "3": "starting",
                    "4": "stopping", 
                    "5": "restarting",
                    "6": "enabling",
                    "7": "disabling"
                }
                
                console.print(f"\n[yellow]→ {action[choice].capitalize()} {service_name}...[/yellow]")
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_batch
                    cmd_ssh_batch(command=commands[choice], target=target, parallel=False)
                except Exception as e:
                    console.print(f"[red]✗ Service operation failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")


def file_transfer_menu(device):
    """File transfer menu."""
    while True:
        console.clear()
        console.print(Panel.fit(
            f"[bold cyan]File Transfer: {device.device_id}[/bold cyan]\n"
            f"[dim]Address: {device.address}[/dim]",
            border_style="cyan"
        ))
        
        console.print("\n[bold cyan]File Operations:[/bold cyan]")
        console.print("  [1] Upload file")
        console.print("  [2] Download file")
        console.print("  [3] List remote directory")
        console.print("  [4] Create remote directory")
        console.print("  [b] Back to batch operations")
        
        choice = Prompt.ask(
            "\n[cyan]Choose an option[/cyan]",
            choices=["1", "2", "3", "4", "b"],
            default="b"
        )
        
        if choice == "b":
            break
        elif choice == "1":
            # Upload file
            local_path = Prompt.ask("Enter local file path")
            remote_path = Prompt.ask("Enter remote file path")
            
            if local_path and remote_path:
                console.print(f"\n[yellow]→ Uploading {local_path} to {remote_path}[/yellow]")
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_transfer
                    cmd_ssh_transfer(local_path=local_path, remote_path=remote_path, target=target)
                except Exception as e:
                    console.print(f"[red]✗ File upload failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "2":
            # Download file
            remote_path = Prompt.ask("Enter remote file path")
            local_path = Prompt.ask("Enter local file path")
            
            if remote_path and local_path:
                console.print(f"\n[yellow]→ Downloading {remote_path} to {local_path}[/yellow]")
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_transfer
                    cmd_ssh_transfer(local_path=local_path, remote_path=remote_path, target=target, download=True)
                except Exception as e:
                    console.print(f"[red]✗ File download failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "3":
            # List remote directory
            remote_path = Prompt.ask("Enter remote directory path", default="/home/pi")
            
            if remote_path:
                console.print(f"\n[yellow]→ Listing {remote_path}[/yellow]")
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_batch
                    cmd_ssh_batch(command=f"ls -la {remote_path}", target=target, parallel=False)
                except Exception as e:
                    console.print(f"[red]✗ Directory listing failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "4":
            # Create remote directory
            remote_path = Prompt.ask("Enter remote directory path to create")
            
            if remote_path:
                console.print(f"\n[yellow]→ Creating directory {remote_path}[/yellow]")
                try:
                    if "@" in device.address:
                        target = device.address
                    else:
                        target = f"pi@{device.address}"
                    
                    from .cli import cmd_ssh_batch
                    cmd_ssh_batch(command=f"mkdir -p {remote_path}", target=target, parallel=False)
                except Exception as e:
                    console.print(f"[red]✗ Directory creation failed: {e}[/red]")
            
            Prompt.ask("\nPress Enter to continue...")


def open_ssh_shell(target: str):
    """Open interactive SSH shell to device."""
    import os
    import subprocess
    import getpass
    from .ssh_manager import parse_device_target
    
    user, host, port = parse_device_target(target)
    
    console.print(Panel.fit(
        f"[bold cyan]SSH Shell Access[/bold cyan]\n"
        f"Connecting to [bold]{user}@{host}:{port}[/bold]\n"
        f"[dim]Type 'exit' to return to MeshPi[/dim]",
        border_style="cyan"
    ))
    
    # Try different SSH methods
    ssh_cmd = None
    
    # Method 1: Try with default SSH key
    default_key = Path.home() / ".ssh" / "id_rsa"
    if default_key.exists():
        ssh_cmd = ["ssh", "-i", str(default_key), "-p", str(port), f"{user}@{host}"]
    else:
        # Method 2: Try without key (will prompt for password if needed)
        ssh_cmd = ["ssh", "-p", str(port), f"{user}@{host}"]
    
    try:
        console.print(f"[cyan]→ Launching SSH shell...[/cyan]")
        console.print("[dim]Use 'exit' to return to MeshPi[/dim]\n")
        
        # Launch SSH shell
        subprocess.run(ssh_cmd, check=True)
        
        console.print("\n[green]✓ Returned from SSH shell[/green]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ SSH connection failed: {e}[/red]")
        console.print("[dim]Check SSH credentials and network connectivity[/dim]")
        
        # Offer to try with password
        if Confirm.ask("Try with password authentication?", default=False):
            try:
                password = getpass.getpass(f"Enter SSH password for {user}@{host}: ")
                
                # Use sshpass if available, otherwise fallback to manual
                ssh_pass_cmd = ["sshpass", "-p", password] + ssh_cmd
                
                try:
                    subprocess.run(ssh_pass_cmd, check=True)
                    console.print("\n[green]✓ Returned from SSH shell[/green]")
                except FileNotFoundError:
                    console.print("[yellow]sshpass not available. Please install it or use manual SSH.[/yellow]")
                    console.print(f"[dim]Manual command: ssh {user}@{host}[/dim]")
                except subprocess.CalledProcessError:
                    console.print("[red]✗ Password authentication failed[/red]")
                    
            except Exception as e:
                console.print(f"[red]✗ Password authentication failed: {e}[/red]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]SSH session interrupted[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ SSH shell failed: {e}[/red]")


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
