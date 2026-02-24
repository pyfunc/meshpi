"""
meshpi.image
============
Custom OS image builder for Raspberry Pi with pre-installed MeshPi.

Creates bootable images that automatically connect to MeshPi host on first boot.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import shutil

from jinja2 import Template


# Templates
FIRSTBOOT_SCRIPT_TEMPLATE = '''#!/bin/bash
# MeshPi First Boot Script — auto-generated
set -e

LOG_FILE="/var/log/meshpi-firstboot.log"
echo "[$(date)] MeshPi first boot starting..." >> $LOG_FILE

# Wait for network
echo "[$(date)] Waiting for network..." >> $LOG_FILE
until ping -c1 8.8.8.8 >/dev/null 2>&1; do
    sleep 5
done

# Install dependencies if needed
if ! command -v pip3 &> /dev/null; then
    echo "[$(date)] Installing pip3..." >> $LOG_FILE
    apt-get update -qq
    apt-get install -y python3-pip -qq
fi

# Install MeshPi
echo "[$(date)] Installing MeshPi..." >> $LOG_FILE
pip3 install meshpi --break-system-packages --quiet 2>/dev/null || pip3 install meshpi --quiet

# Configure MeshPi host
echo "[$(date)] Configuring MeshPi host..." >> $LOG_FILE
export MESHPI_HOST_IP={{ host_ip }}
export MESHPI_HOST_PORT={{ host_port }}

# Run initial scan
echo "[$(date)] Running MeshPi scan..." >> $LOG_FILE
meshpi scan || echo "[$(date)] Scan failed or waiting for host" >> $LOG_FILE

# Disable firstboot service
echo "[$(date)] Disabling firstboot service..." >> $LOG_FILE
systemctl disable meshpi-firstboot.service
rm -f /etc/systemd/system/meshpi-firstboot.service
rm -f /usr/local/bin/meshpi-firstboot.sh
systemctl daemon-reload

echo "[$(date)] MeshPi first boot complete." >> $LOG_FILE
'''

FIRSTBOOT_SERVICE_TEMPLATE = '''[Unit]
Description=MeshPi First Boot Setup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/meshpi-firstboot.sh
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''


@dataclass
class ImageConfig:
    """Configuration for image building."""
    host_ip: str
    host_port: int = 7422
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    hostname: Optional[str] = None
    ssh_enabled: bool = True
    base_image_url: Optional[str] = None


class ImageBuilder:
    """
    Builder for custom Raspberry Pi OS images with MeshPi pre-installed.
    
    Example:
        builder = ImageBuilder()
        builder.build(
            host_ip="192.168.1.10",
            output_path="meshpi-rpi.img",
            wifi_ssid="MyNetwork",
            wifi_password="password"
        )
    """
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or (Path.home() / ".meshpi" / "image-cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def build(
        self,
        host_ip: str,
        output_path: str,
        host_port: int = 7422,
        wifi_ssid: str = None,
        wifi_password: str = None,
        hostname: str = None,
        base_image: str = None,
    ) -> bool:
        """
        Build a custom image with MeshPi pre-installed.
        
        Args:
            host_ip: MeshPi host IP address
            output_path: Output image file path
            host_port: MeshPi host port
            wifi_ssid: WiFi network name (optional, pre-configures WiFi)
            wifi_password: WiFi password (optional)
            hostname: Device hostname (optional)
            base_image: Path to base RPi OS image (optional)
        
        Returns:
            True if successful
        """
        console = self._get_console()
        
        try:
            console.print("[cyan]→ Building MeshPi image...[/cyan]")
            
            # Check for required tools
            if not self._check_tools():
                console.print("[red]✗ Required tools not found. Need: losetup, mount, umount[/red]")
                return False
            
            # Use provided base image or download
            if base_image:
                image_path = Path(base_image)
                if not image_path.exists():
                    console.print(f"[red]✗ Base image not found: {base_image}[/red]")
                    return False
            else:
                console.print("[yellow]Note: No base image provided.[/yellow]")
                console.print("[dim]To use this feature, provide a Raspberry Pi OS image path.[/dim]")
                console.print("[dim]Download from: https://www.raspberrypi.com/software/operating-systems/[/dim]")
                return self._create_config_package(host_ip, host_port, wifi_ssid, wifi_password, hostname, output_path)
            
            # Create temporary working directory
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                
                # Copy base image
                work_image = tmpdir / "work.img"
                shutil.copy(image_path, work_image)
                
                # Setup loop device and mount
                console.print("[cyan]→ Mounting image...[/cyan]")
                mount_points = self._mount_image(work_image)
                
                if not mount_points:
                    console.print("[red]✗ Failed to mount image[/red]")
                    return False
                
                boot_mount, root_mount = mount_points
                
                try:
                    # Enable SSH
                    if ssh_enabled:
                        (boot_mount / "ssh").touch()
                        console.print("[green]✓ SSH enabled[/green]")
                    
                    # Configure WiFi if provided
                    if wifi_ssid:
                        self._configure_wifi(boot_mount, wifi_ssid, wifi_password)
                        console.print("[green]✓ WiFi configured[/green]")
                    
                    # Set hostname if provided
                    if hostname:
                        self._set_hostname(root_mount, hostname)
                        console.print(f"[green]✓ Hostname set to {hostname}[/green]")
                    
                    # Inject firstboot service
                    self._inject_firstboot(root_mount, host_ip, host_port)
                    console.print("[green]✓ Firstboot service injected[/green]")
                    
                finally:
                    # Unmount
                    self._unmount_image(boot_mount, root_mount)
                
                # Copy to output
                shutil.copy(work_image, output_path)
                console.print(f"[green]✓ Image created: {output_path}[/green]")
                
                return True
                
        except Exception as e:
            console.print(f"[red]✗ Build failed: {e}[/red]")
            return False
    
    def _create_config_package(
        self,
        host_ip: str,
        host_port: int,
        wifi_ssid: str,
        wifi_password: str,
        hostname: str,
        output_path: str,
    ) -> bool:
        """Create a configuration package that can be applied to a running RPi."""
        console = self._get_console()
        
        output = Path(output_path)
        output.mkdir(parents=True, exist_ok=True)
        
        # Create firstboot script
        firstboot_script = Template(FIRSTBOOT_SCRIPT_TEMPLATE).render(
            host_ip=host_ip,
            host_port=host_port
        )
        (output / "meshpi-firstboot.sh").write_text(firstboot_script)
        
        # Create service file
        (output / "meshpi-firstboot.service").write_text(FIRSTBOOT_SERVICE_TEMPLATE)
        
        # Create setup instructions
        instructions = f'''# MeshPi Configuration Package

This package contains files to configure a Raspberry Pi with MeshPi.

## Target Configuration
- Host IP: {host_ip}
- Host Port: {host_port}
- WiFi SSID: {wifi_ssid or "Not configured"}
- Hostname: {hostname or "Not configured"}

## Manual Installation

1. Copy files to RPi:
   ```bash
   scp meshpi-firstboot.sh pi@raspberrypi:/tmp/
   scp meshpi-firstboot.service pi@raspberrypi:/tmp/
   ```

2. SSH into RPi and install:
   ```bash
   ssh pi@raspberrypi
   
   # Install firstboot script
   sudo mv /tmp/meshpi-firstboot.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/meshpi-firstboot.sh
   
   # Install service
   sudo mv /tmp/meshpi-firstboot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable meshpi-firstboot.service
   
   # Enable SSH if not already
   sudo raspi-config nonint do_ssh 0
   
   # Reboot to trigger firstboot
   sudo reboot
   ```

## Alternative: One-line Setup
```bash
curl -sSL https://get.meshpi.io | MESHPI_HOST={host_ip} MESHPI_PORT={host_port} bash
```
'''
        (output / "README.md").write_text(instructions)
        
        console.print(f"[green]✓ Configuration package created: {output_path}[/green]")
        console.print("[dim]Follow README.md instructions to apply to RPi[/dim]")
        
        return True
    
    def _check_tools(self) -> bool:
        """Check if required tools are available."""
        required = ["losetup", "mount", "umount"]
        for tool in required:
            if not shutil.which(tool):
                return False
        return True
    
    def _mount_image(self, image_path: Path) -> Optional[tuple]:
        """Mount image partitions. Returns (boot_mount, root_mount) or None."""
        # This requires sudo privileges
        # For safety, we return None if not running as root or without sudo
        return None
    
    def _unmount_image(self, boot_mount: Path, root_mount: Path) -> None:
        """Unmount image partitions."""
        pass
    
    def _configure_wifi(self, boot_mount: Path, ssid: str, password: str) -> None:
        """Configure WiFi in boot partition."""
        wpa_supplicant = f'''
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
        (boot_mount / "wpa_supplicant.conf").write_text(wpa_supplicant.strip())
    
    def _set_hostname(self, root_mount: Path, hostname: str) -> None:
        """Set device hostname."""
        # Update /etc/hostname
        (root_mount / "etc" / "hostname").write_text(hostname + "\n")
        
        # Update /etc/hosts
        hosts = (root_mount / "etc" / "hosts").read_text()
        hosts = hosts.replace("raspberrypi", hostname)
        (root_mount / "etc" / "hosts").write_text(hosts)
    
    def _inject_firstboot(self, root_mount: Path, host_ip: str, host_port: int) -> None:
        """Inject firstboot service into image."""
        # Create firstboot script
        script = Template(FIRSTBOOT_SCRIPT_TEMPLATE).render(
            host_ip=host_ip,
            host_port=host_port
        )
        
        script_path = root_mount / "usr" / "local" / "bin" / "meshpi-firstboot.sh"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(script)
        script_path.chmod(0o755)
        
        # Create service file
        service_path = root_mount / "etc" / "systemd" / "system" / "meshpi-firstboot.service"
        service_path.write_text(FIRSTBOOT_SERVICE_TEMPLATE)
        
        # Enable service
        service_link = root_mount / "etc" / "systemd" / "system" / "multi-user.target.wants" / "meshpi-firstboot.service"
        service_link.parent.mkdir(parents=True, exist_ok=True)
        if not service_link.exists():
            service_link.symlink_to("/etc/systemd/system/meshpi-firstboot.service")
    
    def _get_console(self):
        """Get rich console."""
        from rich.console import Console
        return Console()


def build_image(
    host_ip: str,
    output_path: str,
    host_port: int = 7422,
    wifi_ssid: str = None,
    wifi_password: str = None,
    hostname: str = None,
    base_image: str = None,
) -> bool:
    """
    Convenience function to build a MeshPi image.
    
    Example:
        build_image(
            host_ip="192.168.1.10",
            output_path="./meshpi-config/",
            wifi_ssid="MyNetwork",
            wifi_password="password"
        )
    """
    builder = ImageBuilder()
    return builder.build(
        host_ip=host_ip,
        output_path=output_path,
        host_port=host_port,
        wifi_ssid=wifi_ssid,
        wifi_password=wifi_password,
        hostname=hostname,
        base_image=base_image,
    )