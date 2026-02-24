"""
Tests for meshpi monitoring modules (audit, metrics, alerts, ota).
"""

import pytest
import tempfile
from pathlib import Path

# Audit tests
class TestAuditLog:
    """Tests for AuditLog class."""
    
    def test_audit_log_write_and_read(self, tmp_path):
        """Test writing and reading audit entries."""
        from meshpi.audit import AuditLog, AuditAction
        
        log_path = tmp_path / "audit.jsonl"
        audit = AuditLog(log_path)
        
        # Write entry
        audit.write("rpi-test", AuditAction.CONFIG_APPLY, detail={"key": "value"})
        
        # Read entry
        entries = audit.read(device_id="rpi-test")
        assert len(entries) == 1
        assert entries[0].device_id == "rpi-test"
        assert entries[0].action == "config_apply"
        assert entries[0].success is True
    
    def test_audit_log_filter_by_action(self, tmp_path):
        """Test filtering by action type."""
        from meshpi.audit import AuditLog
        
        audit = AuditLog(tmp_path / "audit.jsonl")
        audit.write("device1", "config_apply")
        audit.write("device1", "device_reboot")
        audit.write("device2", "config_apply")
        
        entries = audit.read(action="config_apply")
        assert len(entries) == 2
    
    def test_audit_log_get_failures(self, tmp_path):
        """Test getting failed operations."""
        from meshpi.audit import AuditLog
        
        audit = AuditLog(tmp_path / "audit.jsonl")
        audit.write("device1", "config_apply", success=True)
        audit.write("device1", "config_apply", success=False)
        audit.write("device2", "device_reboot", success=False)
        
        failures = audit.get_failures(hours=1)
        assert len(failures) == 2
    
    def test_audit_log_stats(self, tmp_path):
        """Test getting audit statistics."""
        from meshpi.audit import AuditLog
        
        audit = AuditLog(tmp_path / "audit.jsonl")
        audit.write("device1", "config_apply")
        audit.write("device1", "device_reboot")
        audit.write("device2", "config_apply")
        
        stats = audit.get_stats(hours=1)
        assert stats["total"] == 3
        assert stats["success"] == 3
        assert stats["failed"] == 0


# Metrics tests
class TestMetricsHistory:
    """Tests for MetricsHistory class."""
    
    def test_metrics_history_record_and_read(self, tmp_path):
        """Test recording and reading metrics."""
        from meshpi.metrics import MetricsHistory
        
        history = MetricsHistory(str(tmp_path / "metrics.db"))
        
        # Record metrics
        history.record("rpi-test", {
            "cpu": {"load_1m": 1.5},
            "memory": {"used_percent": 50},
            "temperature": {"cpu_gpu": 45},
            "wifi": {"signal": -60}
        })
        
        # Read history
        rows = history.get_history("rpi-test", hours=1)
        assert len(rows) == 1
        # SELECT ts, cpu, memory, temperature, wifi_signal -> index 1 = cpu
        assert rows[0][1] == 1.5  # CPU load value
        assert rows[0][2] == 50   # Memory percent
    
    def test_metrics_history_prune(self, tmp_path):
        """Test pruning old metrics."""
        from meshpi.metrics import MetricsHistory
        
        history = MetricsHistory(str(tmp_path / "metrics.db"))
        
        # Record some metrics
        for i in range(5):
            history.record("rpi-test", {"cpu": {"load_1m": i}})
        
        # Prune (should remove all since days=0)
        removed = history.prune(days=0)
        assert removed >= 5


# Alert tests
class TestAlertEngine:
    """Tests for AlertEngine class."""
    
    def test_alert_rule_high_temperature(self):
        """Test high temperature alert rule."""
        from meshpi.alerts import AlertEngine, AlertRule
        
        rule = AlertRule(
            name="test_temp",
            condition=lambda d: d.get("temperature", 0) > 80,
            message_template="High temp: {temperature}"
        )
        
        engine = AlertEngine(rules=[rule])
        
        # Should trigger
        diag = {"temperature": 85}
        assert rule.condition(diag) is True
        
        # Should not trigger
        diag = {"temperature": 70}
        assert rule.condition(diag) is False
    
    def test_alert_engine_status(self):
        """Test getting alert engine status."""
        from meshpi.alerts import AlertEngine
        
        engine = AlertEngine(webhooks=["https://example.com/webhook"])
        status = engine.get_status()
        
        assert status["webhooks_count"] == 1
        assert status["rules_count"] > 0
    
    def test_alert_enable_disable_rule(self):
        """Test enabling and disabling rules."""
        from meshpi.alerts import AlertEngine
        
        engine = AlertEngine()
        
        # Disable rule
        engine.disable_rule("high_temperature")
        rule = next(r for r in engine.rules if r.name == "high_temperature")
        assert rule.enabled is False
        
        # Enable rule
        engine.enable_rule("high_temperature")
        rule = next(r for r in engine.rules if r.name == "high_temperature")
        assert rule.enabled is True


# OTA tests
class TestOtaManager:
    """Tests for OtaManager class."""
    
    def test_ota_job_creation(self):
        """Test creating OTA job."""
        from meshpi.ota import OtaJob, OtaStatus
        
        job = OtaJob(
            job_id="test-001",
            image_url="https://example.com/image.img",
            target_version="2025.01",
            target_devices=["rpi-test"]
        )
        
        assert job.job_id == "test-001"
        assert job.status == OtaStatus.IDLE
        assert job.rollout_percent == 100
    
    def test_ota_manager_init(self, tmp_path):
        """Test OtaManager initialization."""
        from meshpi.ota import OtaManager
        
        manager = OtaManager(storage_path=tmp_path / "ota")
        
        assert manager.active_jobs == {}
        assert manager.device_status == {}
    
    def test_ota_status_enum(self):
        """Test OtaStatus enum values."""
        from meshpi.ota import OtaStatus
        
        assert OtaStatus.IDLE.value == "idle"
        assert OtaStatus.DOWNLOADING.value == "downloading"
        assert OtaStatus.COMPLETED.value == "completed"
        assert OtaStatus.FAILED.value == "failed"
        assert OtaStatus.ROLLED_BACK.value == "rolled_back"
    
    def test_ota_device_status(self):
        """Test OtaDeviceStatus dataclass."""
        from meshpi.ota import OtaDeviceStatus, OtaStatus
        
        status = OtaDeviceStatus(
            device_id="rpi-test",
            job_id="job-001",
            status=OtaStatus.APPLYING,
            progress=50.0
        )
        
        assert status.device_id == "rpi-test"
        assert status.progress == 50.0
        assert status.current_partition == "A"