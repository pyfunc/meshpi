"""
fake_applier.py
===============
Monkey-patches meshpi.applier when MESHPI_SIMULATE=1.
All system calls are replaced with log-only stubs.
Enables full protocol testing in Docker without root / real RPi.
"""

import os
import sys

if os.environ.get("MESHPI_SIMULATE") == "1":
    import meshpi.applier as _applier
    from rich.console import Console

    _console = Console()

    def _simulated_apply(config: dict) -> None:
        _console.print("\n[bold yellow]⚠  SIMULATE MODE — no system changes applied[/bold yellow]")
        _console.print(f"[dim]Would configure {len(config)} fields:[/dim]")
        for k, v in config.items():
            is_secret = any(x in k.lower() for x in ["password", "key", "secret"])
            _console.print(f"  [cyan]{k}[/cyan] = {'***' if is_secret else v}")
        _console.print("\n[green]✓[/green] Simulation complete — would reboot here\n")

    _applier.apply_config = _simulated_apply
    _console.print("[dim]meshpi applier: SIMULATE mode active[/dim]")
