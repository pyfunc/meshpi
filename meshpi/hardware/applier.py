"""
meshpi.hardware.applier
=======================
Applies hardware profiles to the RPi: installs packages,
loads kernel modules, patches /boot/config.txt, runs post-commands.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .profiles import HardwareProfile, get_profile

console = Console()
CONFIG_TXT = Path("/boot/firmware/config.txt")   # RPi OS Bookworm+
LEGACY_CONFIG_TXT = Path("/boot/config.txt")


def _config_txt_path() -> Path:
    return CONFIG_TXT if CONFIG_TXT.exists() else LEGACY_CONFIG_TXT


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _sudo(cmd: list[str], input_str: str = "") -> tuple[int, str]:
    r = subprocess.run(
        ["sudo"] + cmd,
        input=input_str,
        capture_output=True,
        text=True,
    )
    return r.returncode, (r.stdout + r.stderr).strip()


def _patch_config_txt(lines_to_add: list[str]) -> None:
    """Append lines to /boot/config.txt if not already present."""
    cfg = _config_txt_path()
    try:
        existing = cfg.read_text()
    except PermissionError:
        # Need sudo
        rc, out = _sudo(["cat", str(cfg)])
        existing = out if rc == 0 else ""

    additions = []
    for line in lines_to_add:
        if line.strip() and line not in existing:
            additions.append(line)

    if additions:
        patch = "\n# meshpi hardware profile\n" + "\n".join(additions) + "\n"
        proc = subprocess.Popen(
            ["sudo", "tee", "-a", str(cfg)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        proc.communicate(patch.encode())


def apply_hardware_profile(profile_id: str, config: dict | None = None) -> list[str]:
    """
    Apply a hardware profile to the running system.
    Returns list of warning/error messages.
    """
    profile = get_profile(profile_id)
    errors: list[str] = []
    config = config or {}

    console.print(f"\n[bold cyan]Hardware profile:[/bold cyan] {profile.name}")
    console.print(f"[dim]{profile.description}[/dim]\n")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:

        # 1. apt packages
        if profile.packages:
            task = progress.add_task(f"Installing packages: {', '.join(profile.packages)}", total=None)
            rc, out = _sudo(["apt-get", "install", "-y", "--no-install-recommends"] + profile.packages)
            progress.remove_task(task)
            if rc == 0:
                console.print(f"  [green]✓[/green] Packages installed")
            else:
                errors.append(f"apt: {out[:200]}")
                console.print(f"  [red]✗[/red] Package install failed: {out[:100]}")

        # 2. kernel modules
        if profile.kernel_modules:
            task = progress.add_task("Loading kernel modules", total=None)
            for mod in profile.kernel_modules:
                rc, out = _sudo(["modprobe", mod])
                if rc != 0:
                    errors.append(f"modprobe {mod}: {out}")
            # Persist across reboots
            modules_conf = "\n".join(profile.kernel_modules) + "\n"
            proc = subprocess.Popen(
                ["sudo", "tee", "-a", "/etc/modules"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
            )
            proc.communicate(modules_conf.encode())
            progress.remove_task(task)
            console.print(f"  [green]✓[/green] Kernel modules: {', '.join(profile.kernel_modules)}")

        # 3. dtoverlays → config.txt
        all_config_lines = profile.config_txt_lines[:]
        for overlay in profile.overlays:
            all_config_lines.append(f"dtoverlay={overlay}" if not overlay.startswith("dtoverlay") else overlay)

        if all_config_lines:
            task = progress.add_task("Patching /boot/config.txt", total=None)
            _patch_config_txt(all_config_lines)
            progress.remove_task(task)
            console.print(f"  [green]✓[/green] /boot/config.txt updated ({len(all_config_lines)} lines)")

        # 4. post commands
        if profile.post_commands:
            task = progress.add_task("Running post-install commands", total=None)
            for cmd_str in profile.post_commands:
                rc = subprocess.run(
                    cmd_str, shell=True, capture_output=True, text=True
                ).returncode
                if rc != 0:
                    errors.append(f"post_cmd '{cmd_str}': exit {rc}")
            progress.remove_task(task)
            console.print(f"  [green]✓[/green] Post-install commands done")

    return errors


def apply_multiple_profiles(profile_ids: list[str], config: dict | None = None) -> None:
    """Apply multiple hardware profiles sequentially."""
    all_errors: dict[str, list[str]] = {}
    for pid in profile_ids:
        try:
            errs = apply_hardware_profile(pid, config)
            if errs:
                all_errors[pid] = errs
        except KeyError as exc:
            console.print(f"[red]✗[/red] {exc}")

    if all_errors:
        console.print("\n[bold red]Hardware profile errors:[/bold red]")
        for pid, errs in all_errors.items():
            for e in errs:
                console.print(f"  [red]{pid}:[/red] {e}")
    else:
        console.print("\n[bold green]✓ All hardware profiles applied.[/bold green]")
        console.print("[dim]A reboot is recommended to activate kernel modules and overlays.[/dim]")
