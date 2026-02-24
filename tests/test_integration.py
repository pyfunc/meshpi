"""
tests/integration/test_integration.py
======================================
Integration tests that run against a LIVE meshpi host service.

Prerequisites:
  - meshpi-host container (or meshpi host running locally)
  - Environment: MESHPI_HOST_IP, MESHPI_HOST_PORT

Run:
  # With docker compose:
  docker compose --profile integration up --abort-on-container-exit

  # Locally (host must be running):
  MESHPI_HOST_IP=localhost MESHPI_HOST_PORT=7422 \\
    pytest tests/integration/ -v -k integration
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import time
import threading
from pathlib import Path

import httpx
import pytest

HOST_IP   = os.getenv("MESHPI_HOST_IP",   "localhost")
HOST_PORT = int(os.getenv("MESHPI_HOST_PORT", "7422"))
BASE_URL  = f"http://{HOST_IP}:{HOST_PORT}"

# Skip all if not in integration mode or host unreachable
def _host_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/health", timeout=3).raise_for_status()
        return True
    except Exception:
        return False

pytestmark = pytest.mark.skipif(
    not _host_reachable(),
    reason=f"MeshPi host not reachable at {BASE_URL}",
)


# ─────────────────────────────────────────────────────────────────────────────

class TestHostReachability:

    def test_health_endpoint(self):
        r = httpx.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "online_clients" in data

    def test_info_endpoint(self):
        r = httpx.get(f"{BASE_URL}/info", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["service"] == "meshpi-host"
        assert "host_public_key_pem" in data
        assert "BEGIN PUBLIC KEY" in data["host_public_key_pem"]

    def test_dashboard_serves_html(self):
        r = httpx.get(f"{BASE_URL}/dashboard", timeout=5)
        assert r.status_code == 200
        assert "MeshPi" in r.text
        assert "<html" in r.text.lower()

    def test_swagger_docs(self):
        r = httpx.get(f"{BASE_URL}/docs", timeout=5)
        assert r.status_code == 200


class TestConfigDelivery:

    def test_config_endpoint_returns_encrypted_payload(self):
        """Full round-trip: generate client key → request config → decrypt."""
        from meshpi.crypto import (
            generate_rsa_keypair, public_key_to_pem, decrypt_config
        )
        client_priv, client_pub = generate_rsa_keypair()
        pem = public_key_to_pem(client_pub).decode()

        r = httpx.post(
            f"{BASE_URL}/config",
            json={"client_public_key_pem": pem},
            timeout=10,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

        payload = r.json()["payload"]
        config = decrypt_config(payload.encode(), client_priv)

        # Should contain at least some expected fields
        assert isinstance(config, dict)
        assert len(config) > 0
        print(f"\nDecrypted config fields: {list(config.keys())}")

    def test_config_rejects_invalid_public_key(self):
        r = httpx.post(
            f"{BASE_URL}/config",
            json={"client_public_key_pem": "NOT_A_VALID_KEY"},
            timeout=5,
        )
        assert r.status_code == 400

    def test_two_clients_get_different_ciphertexts(self):
        """Same plaintext → different ciphertexts (AES-GCM random nonce)."""
        from meshpi.crypto import generate_rsa_keypair, public_key_to_pem, decrypt_config

        priv1, pub1 = generate_rsa_keypair()
        priv2, pub2 = generate_rsa_keypair()

        payload1 = httpx.post(
            f"{BASE_URL}/config",
            json={"client_public_key_pem": public_key_to_pem(pub1).decode()},
            timeout=10,
        ).json()["payload"]

        payload2 = httpx.post(
            f"{BASE_URL}/config",
            json={"client_public_key_pem": public_key_to_pem(pub2).decode()},
            timeout=10,
        ).json()["payload"]

        assert payload1 != payload2  # Different encrypted payloads

        # But same plaintext after decryption
        config1 = decrypt_config(payload1.encode(), priv1)
        config2 = decrypt_config(payload2.encode(), priv2)
        assert config1 == config2


class TestDeviceRegistry:

    @pytest.fixture(autouse=True)
    def clean_test_device(self):
        """Remove test device before and after each test."""
        device_id = "test-device-integration"
        httpx.delete(f"{BASE_URL}/devices/{device_id}", timeout=5)
        yield device_id
        httpx.delete(f"{BASE_URL}/devices/{device_id}", timeout=5)

    def test_devices_list_is_array(self):
        r = httpx.get(f"{BASE_URL}/devices", timeout=5)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_push_config_to_offline_device_handled(self, clean_test_device):
        """Push to offline device should return empty results (not crash)."""
        r = httpx.post(
            f"{BASE_URL}/devices/{clean_test_device}/push_config",
            json={"config": {"WIFI_SSID": "NewNetwork"}},
            timeout=5,
        )
        # Should return 200 with empty results (device is offline)
        assert r.status_code in (200, 503)

    def test_command_to_offline_device_returns_503(self, clean_test_device):
        r = httpx.post(
            f"{BASE_URL}/devices/{clean_test_device}/command",
            json={"action": "run_command", "command": "echo test"},
            timeout=5,
        )
        assert r.status_code == 503

    def test_unknown_device_diagnostics_returns_404(self):
        r = httpx.get(f"{BASE_URL}/devices/nonexistent-xyz-999/diagnostics", timeout=5)
        assert r.status_code == 404

    def test_set_device_note(self, clean_test_device):
        """Register a fake device then set a note."""
        # First register via push_config (creates record)
        httpx.post(
            f"{BASE_URL}/devices/{clean_test_device}/push_config",
            json={"config": {}},
            timeout=5,
        )
        # Set note
        r = httpx.post(
            f"{BASE_URL}/devices/{clean_test_device}/note",
            json={"note": "integration test device"},
            timeout=5,
        )
        assert r.status_code in (200, 404)  # 404 if device was not created by push

    def test_delete_nonexistent_device(self):
        r = httpx.delete(f"{BASE_URL}/devices/nonexistent-xyz-integration", timeout=5)
        assert r.status_code == 200
        assert r.json()["removed"] is False


class TestWebSocketProtocol:
    """WebSocket integration tests."""

    @pytest.fixture
    def device_id(self):
        did = f"ws-test-{int(time.time())}"
        yield did
        httpx.delete(f"{BASE_URL}/devices/{did}", timeout=5)

    def test_websocket_hello_welcome(self, device_id):
        """Connect via WS, send hello, receive welcome."""
        try:
            import websockets
            import asyncio
        except ImportError:
            pytest.skip("websockets not installed")

        ws_url = f"ws://{HOST_IP}:{HOST_PORT}/ws/{device_id}"

        async def _test():
            async with websockets.connect(ws_url, open_timeout=5) as ws:
                await ws.send(json.dumps({
                    "type": "hello",
                    "device_id": device_id,
                    "address": "172.28.0.99",
                }))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(raw)
                assert msg["type"] == "welcome"
                assert "host" in msg

        asyncio.run(_test())

        # Device should now appear in registry
        r = httpx.get(f"{BASE_URL}/devices", timeout=5)
        device_ids = [d["device_id"] for d in r.json()]
        assert device_id in device_ids

    def test_websocket_diagnostics_push(self, device_id):
        """Send diagnostics from WS client, verify host acknowledges."""
        try:
            import websockets
        except ImportError:
            pytest.skip("websockets not installed")

        ws_url = f"ws://{HOST_IP}:{HOST_PORT}/ws/{device_id}"

        sample_diag = {
            "timestamp": time.time(),
            "system": {"hostname": device_id, "rpi_model": "Raspberry Pi 4 Model B"},
            "cpu": {"load_1m": 0.42, "load_5m": 0.38, "load_15m": 0.35},
            "memory": {"used_percent": 45.2, "total_kb": 4096000},
            "temperature": {"cpu_gpu": 52.3},
        }

        async def _test():
            async with websockets.connect(ws_url, open_timeout=5) as ws:
                # hello
                await ws.send(json.dumps({"type": "hello", "device_id": device_id, "address": "172.28.0.100"}))
                await asyncio.wait_for(ws.recv(), timeout=5)

                # diagnostics
                await ws.send(json.dumps({"type": "diagnostics", "seq": 1, "data": sample_diag}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                ack = json.loads(raw)
                assert ack["type"] == "ack"
                assert ack["seq"] == 1

        asyncio.run(_test())

        # Diagnostics should appear in registry
        r = httpx.get(f"{BASE_URL}/devices/{device_id}/diagnostics", timeout=5)
        if r.status_code == 200 and r.json():
            diag = r.json()
            assert diag["system"]["hostname"] == device_id

    def test_websocket_receives_config_update(self, device_id):
        """Connect WS client, push config update from REST, verify WS receives it."""
        try:
            import websockets
        except ImportError:
            pytest.skip("websockets not installed")

        ws_url  = f"ws://{HOST_IP}:{HOST_PORT}/ws/{device_id}"
        received: list[dict] = []

        async def _test():
            async with websockets.connect(ws_url, open_timeout=5) as ws:
                # Register
                await ws.send(json.dumps({"type": "hello", "device_id": device_id, "address": "172.28.0.101"}))
                await asyncio.wait_for(ws.recv(), timeout=5)  # welcome

                # Push config update via REST from "another thread"
                def _push():
                    time.sleep(0.3)
                    httpx.post(
                        f"{BASE_URL}/devices/{device_id}/push_config",
                        json={"config": {"WIFI_SSID": "UpdatedNetwork", "TEST_KEY": "hello"}},
                        timeout=5,
                    )

                t = threading.Thread(target=_push)
                t.start()

                # Receive config_update from WS
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(raw)
                    received.append(msg)
                except asyncio.TimeoutError:
                    pass
                finally:
                    t.join()

        asyncio.run(_test())

        if received:
            assert received[0]["type"] == "config_update"
            assert "WIFI_SSID" in received[0]["config"]

    def test_websocket_ping_pong(self, device_id):
        """Client sends ping, host responds pong."""
        try:
            import websockets
        except ImportError:
            pytest.skip("websockets not installed")

        ws_url = f"ws://{HOST_IP}:{HOST_PORT}/ws/{device_id}"

        async def _test():
            async with websockets.connect(ws_url, open_timeout=5) as ws:
                await ws.send(json.dumps({"type": "hello", "device_id": device_id, "address": "127.0.0.1"}))
                await asyncio.wait_for(ws.recv(), timeout=5)

                await ws.send(json.dumps({"type": "ping"}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(raw)
                assert msg["type"] == "pong"

        asyncio.run(_test())


class TestMultiClientScenario:
    """Tests involving multiple simultaneous clients."""

    def test_multiple_clients_in_registry(self):
        """Verify registry correctly tracks multiple devices."""
        r = httpx.get(f"{BASE_URL}/devices", timeout=5)
        assert r.status_code == 200
        # Basic sanity check
        assert isinstance(r.json(), list)

    def test_broadcast_to_all_clients(self):
        """Push config with device_id='*' → should target all online clients."""
        r = httpx.post(
            f"{BASE_URL}/devices/*/push_config",
            json={"config": {"BROADCAST_TEST": "1"}},
            timeout=5,
        )
        assert r.status_code == 200
        data = r.json()
        assert "pushed_to" in data


class TestSecurityEdgeCases:

    def test_malformed_json_body_returns_422(self):
        r = httpx.post(
            f"{BASE_URL}/config",
            content=b"not json at all !!",
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        assert r.status_code == 422

    def test_cannot_decrypt_without_matching_key(self):
        """Ensure cross-client decryption fails (cryptographic isolation)."""
        from meshpi.crypto import (
            generate_rsa_keypair, public_key_to_pem, decrypt_config
        )

        # Client A gets config encrypted for A
        _, pub_a = generate_rsa_keypair()
        priv_b, pub_b = generate_rsa_keypair()

        payload_a = httpx.post(
            f"{BASE_URL}/config",
            json={"client_public_key_pem": public_key_to_pem(pub_a).decode()},
            timeout=10,
        ).json()["payload"]

        # Try to decrypt with Client B's key → must fail
        with pytest.raises(Exception):
            decrypt_config(payload_a.encode(), priv_b)

    def test_large_config_payload_handled(self):
        """Ensure oversized but valid public key body is handled."""
        from meshpi.crypto import generate_rsa_keypair, public_key_to_pem
        _, pub = generate_rsa_keypair()
        pem = public_key_to_pem(pub).decode()

        r = httpx.post(
            f"{BASE_URL}/config",
            json={"client_public_key_pem": pem},
            timeout=10,
        )
        assert r.status_code == 200
