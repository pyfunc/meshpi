"""
meshpi.metrics
==============
Prometheus metrics exporter for MeshPi.

Exposes metrics at /metrics endpoint for Prometheus scraping.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import Gauge, Counter, Histogram

# Lazy import to avoid dependency issues
_prometheus_available = False
try:
    from prometheus_client import (
        Gauge, Counter, Histogram, generate_latest, 
        CONTENT_TYPE_LATEST, REGISTRY
    )
    _prometheus_available = True
except ImportError:
    pass

# Metrics containers
_metrics: dict = {}


def _init_metrics():
    """Initialize Prometheus metrics."""
    global _metrics
    
    if not _prometheus_available:
        return
    
    if _metrics:
        return  # Already initialized
    
    _metrics = {
        # Device metrics
        "cpu_usage": Gauge(
            "meshpi_cpu_usage_percent",
            "CPU usage percentage",
            ["device_id"]
        ),
        "memory_usage": Gauge(
            "meshpi_memory_usage_percent", 
            "Memory usage percentage",
            ["device_id"]
        ),
        "temperature": Gauge(
            "meshpi_temperature_celsius",
            "CPU temperature in Celsius",
            ["device_id"]
        ),
        "wifi_signal": Gauge(
            "meshpi_wifi_signal_dbm",
            "WiFi signal strength in dBm",
            ["device_id"]
        ),
        "device_online": Gauge(
            "meshpi_device_online",
            "Device online status (1=online, 0=offline)",
            ["device_id"]
        ),
        "disk_usage": Gauge(
            "meshpi_disk_usage_percent",
            "Disk usage percentage",
            ["device_id", "mount"]
        ),
        
        # Network metrics
        "network_rx_bytes": Counter(
            "meshpi_network_rx_bytes_total",
            "Total bytes received",
            ["device_id", "interface"]
        ),
        "network_tx_bytes": Counter(
            "meshpi_network_tx_bytes_total",
            "Total bytes transmitted", 
            ["device_id", "interface"]
        ),
        
        # Operation counters
        "ota_updates_total": Counter(
            "meshpi_ota_updates_total",
            "Total OTA update operations",
            ["device_id", "status"]
        ),
        "config_pushes_total": Counter(
            "meshpi_config_pushes_total",
            "Total configuration push operations",
            ["device_id", "status"]
        ),
        "commands_executed_total": Counter(
            "meshpi_commands_executed_total",
            "Total commands executed",
            ["device_id", "status"]
        ),
        "alerts_triggered_total": Counter(
            "meshpi_alerts_triggered_total",
            "Total alerts triggered",
            ["device_id", "alert_type"]
        ),
        
        # Timing histograms
        "command_duration": Histogram(
            "meshpi_command_duration_seconds",
            "Command execution duration",
            ["device_id", "command_type"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        ),
        "connection_duration": Histogram(
            "meshpi_connection_duration_seconds",
            "WebSocket connection duration",
            ["device_id"],
            buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800]
        ),
        
        # Fleet overview
        "devices_total": Gauge(
            "meshpi_devices_total",
            "Total number of devices in fleet"
        ),
        "devices_online": Gauge(
            "meshpi_devices_online",
            "Number of online devices"
        ),
        "groups_total": Gauge(
            "meshpi_groups_total",
            "Total number of device groups"
        ),
    }


def is_available() -> bool:
    """Check if Prometheus client is available."""
    return _prometheus_available


def update_device_metrics(device_id: str, diag: dict) -> None:
    """
    Update Prometheus metrics from device diagnostics.
    
    Args:
        device_id: Device identifier
        diag: Diagnostics dictionary from meshpi.diagnostics.collect()
    """
    if not _prometheus_available:
        return
    
    _init_metrics()
    
    # CPU
    cpu_data = diag.get("cpu", {})
    if isinstance(cpu_data, dict):
        cpu_usage = cpu_data.get("load_1m", 0)
        if cpu_usage:
            _metrics["cpu_usage"].labels(device_id=device_id).set(cpu_usage)
    
    # Memory
    mem_data = diag.get("memory", {})
    if isinstance(mem_data, dict):
        mem_percent = mem_data.get("used_percent", 0)
        if mem_percent:
            _metrics["memory_usage"].labels(device_id=device_id).set(mem_percent)
    
    # Temperature
    temp_data = diag.get("temperature", {})
    if isinstance(temp_data, dict):
        temp = temp_data.get("cpu_gpu") or temp_data.get("zone_0")
        if temp:
            _metrics["temperature"].labels(device_id=device_id).set(temp)
    
    # WiFi
    wifi_data = diag.get("wifi", {})
    if isinstance(wifi_data, dict):
        signal = wifi_data.get("signal")
        if signal:
            _metrics["wifi_signal"].labels(device_id=device_id).set(signal)
    
    # Online status
    _metrics["device_online"].labels(device_id=device_id).set(1)


def set_device_offline(device_id: str) -> None:
    """Mark device as offline in metrics."""
    if not _prometheus_available:
        return
    
    _init_metrics()
    _metrics["device_online"].labels(device_id=device_id).set(0)


def increment_ota_counter(device_id: str, status: str) -> None:
    """Increment OTA update counter."""
    if not _prometheus_available:
        return
    
    _init_metrics()
    _metrics["ota_updates_total"].labels(device_id=device_id, status=status).inc()


def increment_config_counter(device_id: str, status: str) -> None:
    """Increment config push counter."""
    if not _prometheus_available:
        return
    
    _init_metrics()
    _metrics["config_pushes_total"].labels(device_id=device_id, status=status).inc()


def increment_command_counter(device_id: str, status: str) -> None:
    """Increment command execution counter."""
    if not _prometheus_available:
        return
    
    _init_metrics()
    _metrics["commands_executed_total"].labels(device_id=device_id, status=status).inc()


def increment_alert_counter(device_id: str, alert_type: str) -> None:
    """Increment alert counter."""
    if not _prometheus_available:
        return
    
    _init_metrics()
    _metrics["alerts_triggered_total"].labels(
        device_id=device_id, 
        alert_type=alert_type
    ).inc()


def update_fleet_metrics(total: int, online: int, groups: int) -> None:
    """Update fleet overview metrics."""
    if not _prometheus_available:
        return
    
    _init_metrics()
    _metrics["devices_total"].set(total)
    _metrics["devices_online"].set(online)
    _metrics["groups_total"].set(groups)


def get_metrics() -> bytes:
    """
    Get Prometheus metrics output.
    
    Returns:
        Prometheus-formatted metrics text
    """
    if not _prometheus_available:
        return b"# Prometheus client not available\n"
    
    _init_metrics()
    return generate_latest()


def get_content_type() -> str:
    """Get Prometheus content type."""
    if _prometheus_available:
        return CONTENT_TYPE_LATEST
    return "text/plain"


class MetricsHistory:
    """
    Local time-series storage for device metrics using SQLite.
    
    Provides historical data for graphs and analysis when
    Prometheus is not available.
    """
    
    def __init__(self, db_path: str = None):
        import sqlite3
        from pathlib import Path
        
        self.db_path = db_path or str(Path.home() / ".meshpi" / "metrics.db")
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize metrics database."""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    ts REAL,
                    device_id TEXT,
                    cpu REAL,
                    memory REAL,
                    temperature REAL,
                    wifi_signal REAL,
                    disk_usage REAL,
                    online INTEGER
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_device_ts "
                "ON metrics(device_id, ts)"
            )
    
    def record(self, device_id: str, diag: dict) -> None:
        """
        Record device metrics to database.
        
        Args:
            device_id: Device identifier
            diag: Diagnostics dictionary
        """
        import sqlite3
        import time
        
        cpu = diag.get("cpu", {})
        mem = diag.get("memory", {})
        temp = diag.get("temperature", {})
        wifi = diag.get("wifi", {})
        
        cpu_val = cpu.get("load_1m", 0) if isinstance(cpu, dict) else 0
        mem_val = mem.get("used_percent", 0) if isinstance(mem, dict) else 0
        temp_val = temp.get("cpu_gpu") or temp.get("zone_0", 0) if isinstance(temp, dict) else 0
        wifi_val = wifi.get("signal", -100) if isinstance(wifi, dict) else -100
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                (time.time(), device_id, cpu_val, mem_val, temp_val, wifi_val, 0)
            )
    
    def get_history(
        self, 
        device_id: str, 
        hours: int = 24,
        limit: int = 1000
    ) -> list:
        """
        Get historical metrics for a device.
        
        Args:
            device_id: Device identifier
            hours: Hours of history to retrieve
            limit: Maximum number of records
        
        Returns:
            List of metric tuples (ts, cpu, memory, temperature, wifi_signal)
        """
        import sqlite3
        import time
        
        since = time.time() - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT ts, cpu, memory, temperature, wifi_signal 
                FROM metrics 
                WHERE device_id = ? AND ts > ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (device_id, since, limit)
            ).fetchall()
        
        return rows
    
    def prune(self, days: int = 30) -> int:
        """
        Remove old metrics data.
        
        Args:
            days: Keep data from last N days
        
        Returns:
            Number of rows removed
        """
        import sqlite3
        import time
        
        cutoff = time.time() - (days * 24 * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM metrics WHERE ts < ?",
                (cutoff,)
            )
            return cursor.rowcount


# Global metrics history instance
_metrics_history: MetricsHistory | None = None


def get_metrics_history() -> MetricsHistory:
    """Get or create global metrics history instance."""
    global _metrics_history
    if _metrics_history is None:
        _metrics_history = MetricsHistory()
    return _metrics_history