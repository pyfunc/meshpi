"""
meshpi.hardware.custom
=======================
Custom hardware profile management for user-defined profiles.
"""

from __future__ import annotations

import json
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from .profiles import HardwareProfile, PROFILES

console = Console()

# User profiles directory
USER_PROFILES_DIR = Path.home() / ".meshpi" / "profiles"
USER_PROFILES_FILE = USER_PROFILES_DIR / "custom_profiles.json"


def ensure_profiles_dir() -> Path:
    """Ensure the user profiles directory exists."""
    USER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return USER_PROFILES_DIR


def load_custom_profiles() -> Dict[str, HardwareProfile]:
    """Load custom profiles from user directory."""
    custom_profiles = {}
    
    if not USER_PROFILES_FILE.exists():
        return custom_profiles
    
    try:
        with open(USER_PROFILES_FILE, 'r') as f:
            data = json.load(f)
        
        for profile_id, profile_data in data.items():
            # Convert dict back to HardwareProfile
            profile = HardwareProfile(**profile_data)
            custom_profiles[profile_id] = profile
            
    except Exception as e:
        console.print(f"[red]Error loading custom profiles: {e}[/red]")
    
    return custom_profiles


def save_custom_profiles(custom_profiles: Dict[str, HardwareProfile]) -> bool:
    """Save custom profiles to user directory."""
    try:
        ensure_profiles_dir()
        
        # Convert profiles to dicts for JSON serialization
        data = {}
        for profile_id, profile in custom_profiles.items():
            data[profile_id] = asdict(profile)
        
        with open(USER_PROFILES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        console.print(f"[red]Error saving custom profiles: {e}[/red]")
        return False


def get_all_profiles() -> Dict[str, HardwareProfile]:
    """Get all profiles (built-in + custom)."""
    all_profiles = PROFILES.copy()
    custom_profiles = load_custom_profiles()
    all_profiles.update(custom_profiles)
    return all_profiles


def create_custom_profile_interactive() -> Optional[HardwareProfile]:
    """Interactive custom profile creation wizard."""
    console.print(Panel.fit(
        "[bold cyan]Create Custom Hardware Profile[/bold cyan]\n"
        "[dim]Follow the wizard to define your custom hardware profile[/dim]",
        border_style="cyan"
    ))
    
    try:
        # Basic info
        profile_id = Prompt.ask("[bold]Profile ID[/bold]", help="Unique identifier (e.g., my_custom_sensor)")
        if not profile_id or not profile_id.replace('_', '').replace('-', '').isalnum():
            console.print("[red]Invalid profile ID. Use alphanumeric characters, underscores, and hyphens only.[/red]")
            return None
        
        name = Prompt.ask("[bold]Profile Name[/bold]", help="Human-readable name")
        description = Prompt.ask("[bold]Description[/bold]", help="Detailed description of the hardware")
        
        # Category selection
        categories = ["display", "gpio", "sensor", "camera", "audio", "networking", "hat", "storage", "custom"]
        category = Prompt.ask(
            "[bold]Category[/bold]", 
            choices=categories,
            default="custom",
            help="Hardware category"
        )
        
        # Packages
        console.print("\n[bold cyan]System Packages (apt)[/bold cyan]")
        console.print("[dim]Enter system packages to install via apt, one per line. Empty line to finish.[/dim]")
        packages = []
        while True:
            pkg = Prompt.ask(f"Package {len(packages) + 1}", default="", show_default=False)
            if not pkg:
                break
            packages.append(pkg)
        
        # Python packages
        console.print("\n[bold cyan]Python Packages (pip)[/bold cyan]")
        console.print("[dim]Enter Python packages to install via pip, one per line. Empty line to finish.[/dim]")
        python_packages = []
        while True:
            pkg = Prompt.ask(f"Python package {len(python_packages) + 1}", default="", show_default=False)
            if not pkg:
                break
            python_packages.append(pkg)
        
        # Kernel modules
        console.print("\n[bold cyan]Kernel Modules[/bold cyan]")
        console.print("[dim]Enter kernel modules to load, one per line. Empty line to finish.[/dim]")
        kernel_modules = []
        while True:
            module = Prompt.ask(f"Module {len(kernel_modules) + 1}", default="", show_default=False)
            if not module:
                break
            kernel_modules.append(module)
        
        # Device tree overlays
        console.print("\n[bold cyan]Device Tree Overlays[/bold cyan]")
        console.print("[dim]Enter dtoverlay lines, one per line. Empty line to finish.[/dim]")
        overlays = []
        while True:
            overlay = Prompt.ask(f"Overlay {len(overlays) + 1}", default="", show_default=False)
            if not overlay:
                break
            overlays.append(overlay)
        
        # config.txt lines
        console.print("\n[bold cyan]config.txt Lines[/bold cyan]")
        console.print("[dim]Enter custom config.txt lines, one per line. Empty line to finish.[/dim]")
        config_txt_lines = []
        while True:
            line = Prompt.ask(f"Config line {len(config_txt_lines) + 1}", default="", show_default=False)
            if not line:
                break
            config_txt_lines.append(line)
        
        # Post-install commands
        console.print("\n[bold cyan]Post-install Commands[/bold cyan]")
        console.print("[dim]Enter shell commands to run after installation, one per line. Empty line to finish.[/dim]")
        post_commands = []
        while True:
            cmd = Prompt.ask(f"Command {len(post_commands) + 1}", default="", show_default=False)
            if not cmd:
                break
            post_commands.append(cmd)
        
        # Tags
        tags_input = Prompt.ask("[bold]Tags[/bold]", help="Comma-separated tags (e.g., i2c, sensor, custom)")
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
        
        # Create profile
        profile = HardwareProfile(
            id=profile_id,
            name=name,
            category=category,
            description=description,
            packages=packages,
            kernel_modules=kernel_modules,
            overlays=overlays,
            config_txt_lines=config_txt_lines,
            post_commands=post_commands,
            tags=tags
        )
        
        # Show summary
        console.print("\n[bold cyan]Profile Summary:[/bold cyan]")
        console.print(f"  ID: {profile.id}")
        console.print(f"  Name: {profile.name}")
        console.print(f"  Category: {profile.category}")
        console.print(f"  Description: {profile.description}")
        console.print(f"  Packages: {len(profile.packages)} apt, {len(python_packages)} pip")
        console.print(f"  Kernel modules: {len(profile.kernel_modules)}")
        console.print(f"  Overlays: {len(profile.overlays)}")
        console.print(f"  Config lines: {len(profile.config_txt_lines)}")
        console.print(f"  Post commands: {len(profile.post_commands)}")
        console.print(f"  Tags: {', '.join(profile.tags)}")
        
        # Add pip packages to post_commands
        if python_packages:
            pip_cmd = f"pip3 install {' '.join(python_packages)}"
            profile.post_commands.insert(0, pip_cmd)
        
        if Confirm.ask("\n[bold]Save this profile?[/bold]", default=True):
            return profile
        else:
            return None
            
    except Exception as e:
        console.print(f"[red]Error creating profile: {e}[/red]")
        return None


def import_profile_from_file(file_path: str) -> Optional[HardwareProfile]:
    """Import profile from YAML or JSON file."""
    path = Path(file_path)
    
    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return None
    
    try:
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        # Validate required fields
        required_fields = ['id', 'name', 'category', 'description']
        for field in required_fields:
            if field not in data:
                console.print(f"[red]Missing required field: {field}[/red]")
                return None
        
        # Create profile
        profile = HardwareProfile(
            id=data['id'],
            name=data['name'],
            category=data['category'],
            description=data['description'],
            packages=data.get('packages', []),
            kernel_modules=data.get('kernel_modules', []),
            overlays=data.get('overlays', []),
            config_txt_lines=data.get('config_txt_lines', []),
            post_commands=data.get('post_commands', []),
            tags=data.get('tags', [])
        )
        
        return profile
        
    except Exception as e:
        console.print(f"[red]Error importing profile: {e}[/red]")
        return None


def export_profile_to_file(profile: HardwareProfile, file_path: str) -> bool:
    """Export profile to YAML or JSON file."""
    path = Path(file_path)
    
    try:
        data = asdict(profile)
        
        with open(path, 'w') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            else:
                json.dump(data, f, indent=2)
        
        console.print(f"[green]Profile exported to: {file_path}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]Error exporting profile: {e}[/red]")
        return False


def list_custom_profiles() -> None:
    """List all custom profiles."""
    custom_profiles = load_custom_profiles()
    
    if not custom_profiles:
        console.print("[yellow]No custom profiles found.[/yellow]")
        console.print(f"[dim]Custom profiles are stored in: {USER_PROFILES_FILE}[/dim]")
        return
    
    table = Table(title="Custom Hardware Profiles", border_style="cyan")
    table.add_column("ID", style="bold cyan", no_wrap=True)
    table.add_column("Category", style="dim")
    table.add_column("Name")
    table.add_column("Description", style="dim")
    table.add_column("Packages", style="dim")
    
    for profile in custom_profiles.values():
        table.add_row(
            profile.id,
            profile.category,
            profile.name,
            profile.description[:50] + "..." if len(profile.description) > 50 else profile.description,
            f"{len(profile.packages)} apt"
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(custom_profiles)} custom profiles[/dim]")


def delete_custom_profile(profile_id: str) -> bool:
    """Delete a custom profile."""
    custom_profiles = load_custom_profiles()
    
    if profile_id not in custom_profiles:
        console.print(f"[red]Custom profile '{profile_id}' not found.[/red]")
        return False
    
    if Confirm.ask(f"[bold]Delete custom profile '{profile_id}'?[/bold]", default=False):
        del custom_profiles[profile_id]
        return save_custom_profiles(custom_profiles)
    
    return False
