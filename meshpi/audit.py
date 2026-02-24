"""
meshpi.audit
============
Audit logging for MeshPi fleet operations.

Records all operations performed on devices for compliance and debugging.

Usage:
    from meshpi.audit import audit_log
    
    audit_log.write("rpi-kitchen", "ota_push", detail={"version": "2025.01"})
    audit_log.write("rpi-bedroom", "config_apply", success=True)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any
from enum import Enum

# Default audit log path
AUDIT_LOG_PATH = Path.home() / ".meshpi" / "audit.jsonl"


class AuditAction(Enum):
    """Standard audit actions."""
    # Device operations
    DEVICE_ADD = "device_add"
    DEVICE_REMOVE = "device_remove"
    DEVICE_CONNECT = "device_connect"
    DEVICE_DISCONNECT = "device_disconnect"
    
    # Configuration
    CONFIG_APPLY = "config_apply"
    CONFIG_PUSH = "config_push"
    CONFIG_UPDATE = "config_update"
    
    # Hardware
    HW_PROFILE_APPLY = "hw_profile_apply"
    HW_PROFILE_REMOVE = "hw_profile_remove"
    
    # OTA Updates
    OTA_PUSH = "ota_push"
    OTA_APPLY = "ota_apply"
    OTA_ROLLBACK = "ota_rollback"
    OTA_STATUS = "ota_status"
    
    # Security
    KEY_ROTATE = "key_rotate"
    KEY_GENERATE = "key_generate"
    
    # Service
    SERVICE_RESTART = "service_restart"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    DEVICE_REBOOT = "device_reboot"
    
    # Commands
    COMMAND_EXEC = "command_exec"
    SHELL_OPEN = "shell_open"
    
    # Alerts
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    
    # Groups
    GROUP_CREATE = "group_create"
    GROUP_DELETE = "group_delete"
    GROUP_ADD_DEVICE = "group_add_device"
    GROUP_REMOVE_DEVICE = "group_remove_device"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: float
    iso_time: str
    device_id: str
    action: str
    user: str
    success: bool
    detail: dict[str, Any]
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert entry to JSON string."""
        return json.dumps(asdict(self))


class AuditLog:
    """
    Audit log manager for MeshPi.
    
    Writes entries to JSONL file (one JSON object per line) for easy
    parsing and analysis.
    
    Example:
        audit = AuditLog()
        audit.write("rpi-kitchen", "config_apply", success=True)
        entries = audit.read(device_id="rpi-kitchen", hours=24)
    """
    
    def __init__(self, log_path: Path = None):
        self.log_path = log_path or AUDIT_LOG_PATH
        self._ensure_log_file()
    
    def _ensure_log_file(self) -> None:
        """Ensure log file and directory exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()
    
    def write(
        self,
        device_id: str,
        action: str | AuditAction,
        user: str = "host",
        success: bool = True,
        detail: dict[str, Any] = None,
        ip_address: str = None,
        session_id: str = None,
    ) -> None:
        """
        Write an audit log entry.
        
        Args:
            device_id: Target device identifier
            action: Action being performed (string or AuditAction enum)
            user: User or system performing the action
            success: Whether the action succeeded
            detail: Additional details about the action
            ip_address: Source IP address if applicable
            session_id: Session identifier for grouping related actions
        """
        now = time.time()
        iso_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        
        action_str = action.value if isinstance(action, AuditAction) else action
        
        entry = AuditEntry(
            timestamp=now,
            iso_time=iso_time,
            device_id=device_id,
            action=action_str,
            user=user,
            success=success,
            detail=detail or {},
            ip_address=ip_address,
            session_id=session_id,
        )
        
        with open(self.log_path, "a") as f:
            f.write(entry.to_json() + "\n")
    
    def read(
        self,
        device_id: str = None,
        action: str = None,
        user: str = None,
        success: bool = None,
        hours: int = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """
        Read audit log entries with optional filtering.
        
        Args:
            device_id: Filter by device ID
            action: Filter by action type
            user: Filter by user
            success: Filter by success status
            hours: Only entries from last N hours
            limit: Maximum number of entries to return
        
        Returns:
            List of matching AuditEntry objects
        """
        entries = []
        cutoff = time.time() - (hours * 3600) if hours else 0
        
        if not self.log_path.exists():
            return entries
        
        with open(self.log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    entry = AuditEntry(**data)
                    
                    # Apply filters
                    if device_id and entry.device_id != device_id:
                        continue
                    if action and entry.action != action:
                        continue
                    if user and entry.user != user:
                        continue
                    if success is not None and entry.success != success:
                        continue
                    if hours and entry.timestamp < cutoff:
                        continue
                    
                    entries.append(entry)
                    
                    if len(entries) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
        
        # Return newest first
        entries.reverse()
        return entries[:limit]
    
    def get_recent(self, count: int = 50) -> list[AuditEntry]:
        """Get most recent audit entries."""
        return self.read(limit=count)
    
    def get_device_history(self, device_id: str, hours: int = 24) -> list[AuditEntry]:
        """Get audit history for a specific device."""
        return self.read(device_id=device_id, hours=hours, limit=500)
    
    def get_failures(self, hours: int = 24) -> list[AuditEntry]:
        """Get failed operations in the specified time period."""
        return self.read(success=False, hours=hours, limit=100)
    
    def export_csv(self, output_path: str, hours: int = None) -> int:
        """
        Export audit log to CSV file.
        
        Args:
            output_path: Path to output CSV file
            hours: Only export entries from last N hours (all if None)
        
        Returns:
            Number of entries exported
        """
        import csv
        
        entries = self.read(hours=hours, limit=10000)
        
        if not entries:
            return 0
        
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                "timestamp", "iso_time", "device_id", "action",
                "user", "success", "detail", "ip_address", "session_id"
            ])
            
            for entry in entries:
                writer.writerow([
                    entry.timestamp,
                    entry.iso_time,
                    entry.device_id,
                    entry.action,
                    entry.user,
                    entry.success,
                    json.dumps(entry.detail),
                    entry.ip_address or "",
                    entry.session_id or "",
                ])
        
        return len(entries)
    
    def get_stats(self, hours: int = 24) -> dict:
        """
        Get audit statistics for the specified time period.
        
        Returns:
            Dictionary with counts by action, success rate, etc.
        """
        entries = self.read(hours=hours, limit=10000)
        
        if not entries:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "by_action": {},
                "by_device": {},
            }
        
        stats = {
            "total": len(entries),
            "success": sum(1 for e in entries if e.success),
            "failed": sum(1 for e in entries if not e.success),
            "by_action": {},
            "by_device": {},
        }
        
        # Count by action
        for entry in entries:
            if entry.action not in stats["by_action"]:
                stats["by_action"][entry.action] = 0
            stats["by_action"][entry.action] += 1
            
            if entry.device_id not in stats["by_device"]:
                stats["by_device"][entry.device_id] = 0
            stats["by_device"][entry.device_id] += 1
        
        return stats
    
    def prune(self, days: int = 30) -> int:
        """
        Remove audit entries older than specified days.
        
        Args:
            days: Keep entries from last N days
        
        Returns:
            Number of entries removed
        """
        cutoff = time.time() - (days * 24 * 3600)
        
        if not self.log_path.exists():
            return 0
        
        kept = []
        removed = 0
        
        with open(self.log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    if data.get("timestamp", 0) >= cutoff:
                        kept.append(line)
                    else:
                        removed += 1
                except json.JSONDecodeError:
                    continue
        
        # Rewrite file with kept entries
        with open(self.log_path, "w") as f:
            for line in kept:
                f.write(line + "\n")
        
        return removed


# Global audit log instance
audit_log = AuditLog()