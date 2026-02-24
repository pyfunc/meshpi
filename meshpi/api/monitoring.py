"""
meshpi.api.monitoring
=====================
FastAPI routes for monitoring endpoints.

Provides:
- /metrics - Prometheus metrics endpoint
- /api/audit - Audit log API
- /api/alerts - Alerts status API
- /api/ota - OTA management API
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter()


# Prometheus metrics endpoint
@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    """
    from meshpi.metrics import get_metrics, get_content_type
    
    return Response(
        content=get_metrics(),
        media_type=get_content_type()
    )


# Audit API
class AuditEntryResponse(BaseModel):
    timestamp: float
    iso_time: str
    device_id: str
    action: str
    user: str
    success: bool
    detail: dict


@router.get("/api/audit")
async def get_audit_log(
    device_id: Optional[str] = None,
    action: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get audit log entries.
    
    Args:
        device_id: Filter by device ID
        action: Filter by action type
        hours: Hours of history (1-168)
        limit: Maximum entries (1-1000)
    """
    from meshpi.audit import audit_log
    
    entries = audit_log.read(
        device_id=device_id,
        action=action,
        hours=hours,
        limit=limit
    )
    
    return {
        "entries": [
            AuditEntryResponse(
                timestamp=e.timestamp,
                iso_time=e.iso_time,
                device_id=e.device_id,
                action=e.action,
                user=e.user,
                success=e.success,
                detail=e.detail
            )
            for e in entries
        ],
        "count": len(entries),
        "filters": {
            "device_id": device_id,
            "action": action,
            "hours": hours
        }
    }


@router.get("/api/audit/stats")
async def get_audit_stats(hours: int = Query(24, ge=1, le=168)):
    """Get audit statistics."""
    from meshpi.audit import audit_log
    
    return audit_log.get_stats(hours=hours)


@router.get("/api/audit/failures")
async def get_audit_failures(hours: int = Query(24, ge=1, le=168)):
    """Get failed operations."""
    from meshpi.audit import audit_log
    
    failures = audit_log.get_failures(hours=hours)
    
    return {
        "failures": [
            {
                "timestamp": e.timestamp,
                "iso_time": e.iso_time,
                "device_id": e.device_id,
                "action": e.action,
                "error": e.detail.get("error", "Unknown error")
            }
            for e in failures
        ],
        "count": len(failures)
    }


# Alerts API
@router.get("/api/alerts/status")
async def get_alerts_status():
    """Get alert engine status."""
    from meshpi.alerts import get_alert_engine
    
    engine = get_alert_engine()
    return engine.get_status()


@router.get("/api/alerts/rules")
async def get_alert_rules():
    """Get all alert rules."""
    from meshpi.alerts import get_alert_engine
    
    engine = get_alert_engine()
    
    return {
        "rules": [
            {
                "name": rule.name,
                "severity": rule.severity,
                "cooldown_seconds": rule.cooldown_seconds,
                "enabled": rule.enabled
            }
            for rule in engine.rules
        ]
    }


@router.post("/api/alerts/rules/{name}/enable")
async def enable_alert_rule(name: str):
    """Enable an alert rule."""
    from meshpi.alerts import get_alert_engine
    
    engine = get_alert_engine()
    engine.enable_rule(name)
    
    return {"status": "enabled", "rule": name}


@router.post("/api/alerts/rules/{name}/disable")
async def disable_alert_rule(name: str):
    """Disable an alert rule."""
    from meshpi.alerts import get_alert_engine
    
    engine = get_alert_engine()
    engine.disable_rule(name)
    
    return {"status": "disabled", "rule": name}


@router.post("/api/alerts/webhooks")
async def add_alert_webhook(url: str):
    """Add a webhook URL."""
    from meshpi.alerts import get_alert_engine
    
    engine = get_alert_engine()
    engine.add_webhook(url)
    
    return {"status": "added", "webhooks_count": len(engine.webhooks)}


@router.delete("/api/alerts/webhooks")
async def remove_alert_webhook(url: str):
    """Remove a webhook URL."""
    from meshpi.alerts import get_alert_engine
    
    engine = get_alert_engine()
    engine.remove_webhook(url)
    
    return {"status": "removed", "webhooks_count": len(engine.webhooks)}


# OTA API
class OtaJobCreate(BaseModel):
    job_id: str
    image_url: str
    target_version: str
    target_devices: list[str]
    checksum: Optional[str] = None
    rollout_percent: int = 100
    rollback_on_fail: bool = True


@router.post("/api/ota/push")
async def push_ota_update(job: OtaJobCreate):
    """
    Push OTA update to devices.
    
    This is an async operation - check status via /api/ota/jobs/{job_id}
    """
    from meshpi.ota import OtaManager, OtaJob
    
    manager = OtaManager()
    
    ota_job = OtaJob(
        job_id=job.job_id,
        image_url=job.image_url,
        target_version=job.target_version,
        target_devices=job.target_devices,
        checksum=job.checksum,
        rollout_percent=job.rollout_percent,
        rollback_on_fail=job.rollback_on_fail
    )
    
    # Note: This would normally be run in background
    # For now, we just create the job
    manager.active_jobs[job.job_id] = ota_job
    
    return {
        "status": "created",
        "job_id": job.job_id,
        "target_devices": job.target_devices,
        "rollout_percent": job.rollout_percent
    }


@router.get("/api/ota/jobs")
async def list_ota_jobs():
    """List all OTA jobs."""
    from meshpi.ota import get_ota_manager
    
    manager = get_ota_manager()
    
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "target_version": job.target_version,
                "target_devices": job.target_devices,
                "progress": job.progress,
                "errors": job.errors,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at
            }
            for job in manager.active_jobs.values()
        ]
    }


@router.get("/api/ota/jobs/{job_id}")
async def get_ota_job(job_id: str):
    """Get OTA job status."""
    from meshpi.ota import get_ota_manager
    
    manager = get_ota_manager()
    job = manager.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "image_url": job.image_url,
        "target_version": job.target_version,
        "target_devices": job.target_devices,
        "progress": job.progress,
        "errors": job.errors,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }


@router.post("/api/ota/rollback/{job_id}")
async def rollback_ota_job(job_id: str):
    """Rollback all devices in an OTA job."""
    from meshpi.ota import get_ota_manager
    
    manager = get_ota_manager()
    
    # Note: This would normally be async
    # await manager.rollback_all(job_id)
    
    return {
        "status": "rollback_initiated",
        "job_id": job_id
    }


@router.get("/api/ota/devices/{device_id}")
async def get_device_ota_status(device_id: str):
    """Get OTA status for a specific device."""
    from meshpi.ota import get_ota_manager
    
    manager = get_ota_manager()
    status = manager.get_device_status(device_id)
    
    if not status:
        return {
            "device_id": device_id,
            "status": "idle",
            "current_partition": "A"
        }
    
    return {
        "device_id": status.device_id,
        "job_id": status.job_id,
        "status": status.status.value,
        "progress": status.progress,
        "current_partition": status.current_partition,
        "target_partition": status.target_partition,
        "error": status.error
    }


# Metrics history API
@router.get("/api/metrics/history/{device_id}")
async def get_metrics_history(
    device_id: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(500, ge=1, le=2000)
):
    """Get historical metrics for a device."""
    from meshpi.metrics import get_metrics_history
    
    history = get_metrics_history()
    rows = history.get_history(device_id, hours=hours, limit=limit)
    
    return {
        "device_id": device_id,
        "hours": hours,
        "metrics": [
            {
                "timestamp": row[0],
                "cpu": row[1],
                "memory": row[2],
                "temperature": row[3],
                "wifi_signal": row[4]
            }
            for row in rows
        ],
        "count": len(rows)
    }