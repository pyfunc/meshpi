"""
meshpi.ota
==========
Over-the-Air update management for Raspberry Pi fleet.

Provides A/B partition updates with rollback capability.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import json

import httpx


class OtaStatus(Enum):
    """OTA update status."""
    IDLE = "idle"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    STAGING = "staging"
    APPLYING = "applying"
    REBOOTING = "rebooting"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class OtaError(Exception):
    """OTA update error."""
    pass


@dataclass
class OtaJob:
    """OTA update job definition."""
    job_id: str
    image_url: str
    target_version: str
    target_devices: list[str]
    checksum: Optional[str] = None
    rollout_percent: int = 100
    rollback_on_fail: bool = True
    status: OtaStatus = OtaStatus.IDLE
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: dict[str, float] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


@dataclass
class OtaDeviceStatus:
    """OTA status for a single device."""
    device_id: str
    job_id: str
    status: OtaStatus
    progress: float = 0.0
    current_partition: str = "A"
    target_partition: str = "B"
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class OtaManager:
    """
    OTA update manager for fleet-wide updates.
    
    Features:
    - Staged rollout (percentage-based)
    - A/B partition support
    - Automatic rollback on failure
    - Progress tracking
    
    Example:
        manager = OtaManager(ws_manager, audit_log)
        job = OtaJob(
            job_id="update-001",
            image_url="https://example.com/rpi-os.img",
            target_version="2025.01",
            target_devices=["rpi-kitchen", "rpi-bedroom"]
        )
        await manager.push_update(job)
    """
    
    def __init__(self, ws_manager=None, audit_log=None, storage_path: Path = None):
        self.ws_manager = ws_manager
        self.audit_log = audit_log
        self.storage_path = storage_path or (Path.home() / ".meshpi" / "ota")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.active_jobs: dict[str, OtaJob] = {}
        self.device_status: dict[str, OtaDeviceStatus] = {}
    
    async def push_update(self, job: OtaJob) -> None:
        """
        Push OTA update to devices with staged rollout.
        
        Args:
            job: OTA job configuration
        """
        job.status = OtaStatus.DOWNLOADING
        job.started_at = time.time()
        self.active_jobs[job.job_id] = job
        
        # Get checksum if not provided
        if not job.checksum:
            job.checksum = await self._get_checksum(job.image_url)
        
        # Calculate rollout batch
        devices = job.target_devices
        batch_size = max(1, int(len(devices) * job.rollout_percent / 100))
        batch = devices[:batch_size]
        
        job.status = OtaStatus.APPLYING
        
        for device_id in batch:
            # Initialize device status
            self.device_status[device_id] = OtaDeviceStatus(
                device_id=device_id,
                job_id=job.job_id,
                status=OtaStatus.DOWNLOADING,
            )
            
            try:
                await self._push_to_device(device_id, job)
                job.progress[device_id] = 100.0
                
                if self.audit_log:
                    self.audit_log.write(
                        device_id, 
                        "ota_push", 
                        detail={"version": job.target_version, "job_id": job.job_id}
                    )
                    
            except Exception as e:
                job.errors[device_id] = str(e)
                self.device_status[device_id].status = OtaStatus.FAILED
                self.device_status[device_id].error = str(e)
                
                if self.audit_log:
                    self.audit_log.write(
                        device_id,
                        "ota_push",
                        success=False,
                        detail={"error": str(e), "job_id": job.job_id}
                    )
    
    async def _push_to_device(self, device_id: str, job: OtaJob) -> None:
        """Push update to a single device."""
        if not self.ws_manager:
            raise OtaError("WebSocket manager not configured")
        
        self.device_status[device_id].status = OtaStatus.APPLYING
        
        await self.ws_manager.send_command(device_id, {
            "cmd": "ota_apply",
            "job_id": job.job_id,
            "image_url": job.image_url,
            "version": job.target_version,
            "checksum": job.checksum,
            "rollback_on_fail": job.rollback_on_fail,
        })
    
    async def rollback(self, device_id: str) -> None:
        """
        Rollback device to previous partition.
        
        Args:
            device_id: Device to rollback
        """
        if not self.ws_manager:
            raise OtaError("WebSocket manager not configured")
        
        await self.ws_manager.send_command(device_id, {
            "cmd": "ota_rollback",
        })
        
        if device_id in self.device_status:
            self.device_status[device_id].status = OtaStatus.ROLLED_BACK
        
        if self.audit_log:
            self.audit_log.write(device_id, "ota_rollback")
    
    async def rollback_all(self, job_id: str) -> None:
        """Rollback all devices in a job."""
        job = self.active_jobs.get(job_id)
        if not job:
            return
        
        for device_id in job.target_devices:
            try:
                await self.rollback(device_id)
            except Exception:
                pass
    
    def get_job_status(self, job_id: str) -> Optional[OtaJob]:
        """Get status of an OTA job."""
        return self.active_jobs.get(job_id)
    
    def get_device_status(self, device_id: str) -> Optional[OtaDeviceStatus]:
        """Get OTA status for a device."""
        return self.device_status.get(device_id)
    
    def update_device_status(self, device_id: str, status: OtaStatus, 
                             progress: float = None, error: str = None) -> None:
        """Update device OTA status (called from WebSocket handler)."""
        if device_id not in self.device_status:
            return
        
        device_status = self.device_status[device_id]
        device_status.status = status
        
        if progress is not None:
            device_status.progress = progress
        
        if error:
            device_status.error = error
        
        # Update job progress
        job_id = device_status.job_id
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.progress[device_id] = progress or 0
            
            # Check if all devices completed
            all_done = all(
                job.progress.get(d, 0) >= 100 or d in job.errors
                for d in job.target_devices
            )
            
            if all_done:
                job.status = OtaStatus.COMPLETED
                job.completed_at = time.time()
    
    async def _get_checksum(self, url: str) -> str:
        """Get SHA256 checksum for image URL."""
        # Try .sha256 file first
        checksum_url = url + ".sha256"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(checksum_url)
                if resp.status_code == 200:
                    return resp.text.strip().split()[0]
        except Exception:
            pass
        
        # Calculate from download (for small files or local)
        return ""
    
    def save_state(self) -> None:
        """Save OTA state to disk."""
        state_file = self.storage_path / "ota_state.json"
        
        data = {
            "active_jobs": {
                job_id: {
                    "job_id": job.job_id,
                    "image_url": job.image_url,
                    "target_version": job.target_version,
                    "target_devices": job.target_devices,
                    "checksum": job.checksum,
                    "rollout_percent": job.rollout_percent,
                    "rollback_on_fail": job.rollback_on_fail,
                    "status": job.status.value,
                    "created_at": job.created_at,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "progress": job.progress,
                    "errors": job.errors,
                }
                for job_id, job in self.active_jobs.items()
            },
            "device_status": {
                device_id: {
                    "device_id": status.device_id,
                    "job_id": status.job_id,
                    "status": status.status.value,
                    "progress": status.progress,
                    "current_partition": status.current_partition,
                    "target_partition": status.target_partition,
                    "error": status.error,
                    "started_at": status.started_at,
                    "completed_at": status.completed_at,
                }
                for device_id, status in self.device_status.items()
            }
        }
        
        state_file.write_text(json.dumps(data, indent=2))
    
    def load_state(self) -> None:
        """Load OTA state from disk."""
        state_file = self.storage_path / "ota_state.json"
        
        if not state_file.exists():
            return
        
        try:
            data = json.loads(state_file.read_text())
            
            for job_id, job_data in data.get("active_jobs", {}).items():
                job = OtaJob(
                    job_id=job_data["job_id"],
                    image_url=job_data["image_url"],
                    target_version=job_data["target_version"],
                    target_devices=job_data["target_devices"],
                    checksum=job_data.get("checksum"),
                    rollout_percent=job_data.get("rollout_percent", 100),
                    rollback_on_fail=job_data.get("rollback_on_fail", True),
                    status=OtaStatus(job_data.get("status", "idle")),
                    created_at=job_data.get("created_at", time.time()),
                    started_at=job_data.get("started_at"),
                    completed_at=job_data.get("completed_at"),
                    progress=job_data.get("progress", {}),
                    errors=job_data.get("errors", {}),
                )
                self.active_jobs[job_id] = job
            
            for device_id, status_data in data.get("device_status", {}).items():
                status = OtaDeviceStatus(
                    device_id=status_data["device_id"],
                    job_id=status_data["job_id"],
                    status=OtaStatus(status_data.get("status", "idle")),
                    progress=status_data.get("progress", 0.0),
                    current_partition=status_data.get("current_partition", "A"),
                    target_partition=status_data.get("target_partition", "B"),
                    error=status_data.get("error"),
                    started_at=status_data.get("started_at"),
                    completed_at=status_data.get("completed_at"),
                )
                self.device_status[device_id] = status
                
        except Exception:
            pass


def get_inactive_partition() -> str:
    """
    Get the inactive partition for OTA updates.
    
    Returns:
        Path to inactive partition (e.g., /dev/mmcblk0p3)
    """
    import subprocess
    
    try:
        # Get current root partition
        result = subprocess.run(
            ["findmnt", "-n", "-o", "SOURCE", "/"],
            capture_output=True,
            text=True
        )
        current = result.stdout.strip()
        
        # A/B partition scheme
        if "mmcblk0p2" in current:
            return "/dev/mmcblk0p3"
        elif "mmcblk0p3" in current:
            return "/dev/mmcblk0p2"
        else:
            # Fallback
            return "/dev/mmcblk0p3"
    except Exception:
        return "/dev/mmcblk0p3"


def apply_ota_update(image_path: str, target_partition: str) -> bool:
    """
    Apply OTA update to target partition.
    
    Args:
        image_path: Path to OS image file
        target_partition: Target partition device
    
    Returns:
        True if successful
    """
    import subprocess
    
    try:
        # Write image to partition
        subprocess.run(
            ["dd", f"if={image_path}", f"of={target_partition}", "bs=4M", "status=progress"],
            check=True
        )
        
        # Sync to ensure all data is written
        subprocess.run(["sync"], check=True)
        
        return True
    except subprocess.CalledProcessError:
        return False


def set_boot_partition(partition: str) -> bool:
    """
    Set boot partition for next reboot.
    
    Args:
        partition: Partition to boot from
    
    Returns:
        True if successful
    """
    import subprocess
    
    try:
        # Use raspi-config to set boot partition
        subprocess.run(
            ["raspi-config", "nonint", "do_boot_partition", partition],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


# Global OTA manager instance
_ota_manager: OtaManager | None = None


def get_ota_manager() -> OtaManager:
    """Get or create global OTA manager instance."""
    global _ota_manager
    if _ota_manager is None:
        _ota_manager = OtaManager()
    return _ota_manager