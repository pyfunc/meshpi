"""
End-to-End tests for MeshPi using Docker containers.

Run with: pytest tests/test_e2e.py -v --tb=short

These tests require Docker to be running.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from typing import Optional

import httpx
import pytest

# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(
    not os.path.exists("/var/run/docker.sock") and not shutil.which("docker"),
    reason="Docker not available"
)


def shutil_which(name: str) -> Optional[str]:
    """Check if command exists."""
    import shutil
    return shutil.which(name)


@pytest.fixture(scope="module")
def docker_compose():
    """Start Docker Compose for E2E tests."""
    if not shutil_which("docker"):
        pytest.skip("Docker not available")
    
    # Build and start containers
    subprocess.run(
        ["docker", "compose", "build", "meshpi-host"],
        capture_output=True,
        check=False
    )
    
    # Start host in background
    proc = subprocess.Popen(
        ["docker", "compose", "up", "meshpi-host"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for service to be ready
    client = httpx.Client()
    max_retries = 30
    
    for i in range(max_retries):
        try:
            response = client.get("http://localhost:7422/health", timeout=2)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(1)
    else:
        proc.terminate()
        pytest.fail("MeshPi host did not start in time")
    
    yield proc
    
    # Cleanup
    proc.terminate()
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


@pytest.fixture
def api_client():
    """HTTP client for API requests."""
    return httpx.Client(base_url="http://localhost:7422", timeout=10)


class TestHostHealth:
    """Test host service health endpoints."""
    
    def test_health_endpoint(self, docker_compose, api_client):
        """Test /health endpoint returns OK."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_info_endpoint(self, docker_compose, api_client):
        """Test /info endpoint returns host info."""
        response = api_client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "host_public_key_pem" in data
        assert "hostname" in data


class TestDeviceRegistry:
    """Test device registration and management."""
    
    def test_list_devices_empty(self, docker_compose, api_client):
        """Test listing devices when none registered."""
        response = api_client.get("/devices")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""
    
    def test_metrics_endpoint(self, docker_compose, api_client):
        """Test /metrics returns Prometheus format."""
        response = api_client.get("/metrics")
        assert response.status_code == 200
        assert "meshpi_fleet_devices_total" in response.text
        assert "meshpi_fleet_online" in response.text


class TestAlertsAPI:
    """Test alerts management API."""
    
    def test_alerts_status(self, docker_compose, api_client):
        """Test /api/alerts/status endpoint."""
        response = api_client.get("/api/alerts/status")
        assert response.status_code == 200
        data = response.json()
        assert "rules_count" in data
        assert "webhooks_count" in data
    
    def test_alerts_rules_list(self, docker_compose, api_client):
        """Test listing alert rules."""
        response = api_client.get("/api/alerts/rules")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert len(data["rules"]) > 0
    
    def test_enable_disable_rule(self, docker_compose, api_client):
        """Test enabling and disabling alert rules."""
        # Disable rule
        response = api_client.post("/api/alerts/rules/high_temperature/enable")
        assert response.status_code == 200
        
        # Re-enable rule
        response = api_client.post("/api/alerts/rules/high_temperature/enable")
        assert response.status_code == 200


class TestAuditAPI:
    """Test audit log API."""
    
    def test_audit_log_empty(self, docker_compose, api_client):
        """Test audit log when empty."""
        response = api_client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "count" in data
    
    def test_audit_stats(self, docker_compose, api_client):
        """Test audit statistics."""
        response = api_client.get("/api/audit/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "success" in data
        assert "failed" in data


class TestOtaAPI:
    """Test OTA management API."""
    
    def test_list_ota_jobs(self, docker_compose, api_client):
        """Test listing OTA jobs."""
        response = api_client.get("/api/ota/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
    
    def test_get_nonexistent_job(self, docker_compose, api_client):
        """Test getting non-existent OTA job."""
        response = api_client.get("/api/ota/jobs/nonexistent")
        assert response.status_code == 404


class TestWebSocketConnection:
    """Test WebSocket connections."""
    
    @pytest.mark.asyncio
    async def test_websocket_connect(self, docker_compose):
        """Test WebSocket connection and hello handshake."""
        import websockets
        
        uri = "ws://localhost:7422/ws/test-device-001"
        
        async with websockets.connect(uri) as ws:
            # Send hello
            await ws.send(json.dumps({
                "type": "hello",
                "device_id": "test-device-001",
                "address": "test"
            }))
            
            # Receive welcome
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            assert data["type"] == "welcome"
            assert "host" in data
    
    @pytest.mark.asyncio
    async def test_websocket_diagnostics(self, docker_compose):
        """Test sending diagnostics via WebSocket."""
        import websockets
        
        uri = "ws://localhost:7422/ws/test-device-002"
        
        async with websockets.connect(uri) as ws:
            # Send hello first
            await ws.send(json.dumps({
                "type": "hello",
                "device_id": "test-device-002",
                "address": "test"
            }))
            await ws.recv()  # welcome
            
            # Send diagnostics
            await ws.send(json.dumps({
                "type": "diagnostics",
                "seq": 1,
                "data": {
                    "cpu": {"load_1m": 1.5},
                    "memory": {"used_percent": 50},
                    "temperature": {"cpu_gpu": 45},
                    "wifi": {"signal": -60}
                }
            }))
            
            # Receive ack
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            assert data["type"] == "ack"
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, docker_compose):
        """Test ping/pong over WebSocket."""
        import websockets
        
        uri = "ws://localhost:7422/ws/test-device-003"
        
        async with websockets.connect(uri) as ws:
            # Send hello first
            await ws.send(json.dumps({
                "type": "hello",
                "device_id": "test-device-003",
                "address": "test"
            }))
            await ws.recv()  # welcome
            
            # Send ping
            await ws.send(json.dumps({"type": "ping"}))
            
            # Receive pong
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            assert data["type"] == "pong"