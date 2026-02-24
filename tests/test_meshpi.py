"""Tests for MeshPi package."""

import os
import pytest


def test_placeholder():
    """Placeholder test to verify the test setup works."""
    assert True


# Check if meshpi is installed
meshpi_installed = True
try:
    import meshpi
except ImportError:
    meshpi_installed = False


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import():
    """Verify the main package can be imported."""
    import meshpi  # noqa: F401


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_cli():
    """Verify CLI module can be imported."""
    pytest.importorskip("click")
    from meshpi import cli
    assert hasattr(cli, 'main')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_host():
    """Verify host module can be imported."""
    pytest.importorskip("uvicorn")
    pytest.importorskip("fastapi")
    from meshpi import host
    assert hasattr(host, 'app')
    assert hasattr(host, 'run_host')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_client():
    """Verify client module can be imported."""
    pytest.importorskip("zeroconf")
    pytest.importorskip("httpx")
    from meshpi import client
    assert hasattr(client, 'run_scan')
    assert hasattr(client, 'run_daemon')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_crypto():
    """Verify crypto module can be imported."""
    pytest.importorskip("cryptography")
    from meshpi import crypto
    assert hasattr(crypto, 'get_or_create_host_keys')
    assert hasattr(crypto, 'get_or_create_client_keys')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_config():
    """Verify config module can be imported."""
    from meshpi import config
    assert hasattr(config, 'load_config')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_diagnostics():
    """Verify diagnostics module can be imported."""
    from meshpi import diagnostics
    assert hasattr(diagnostics, 'collect')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_registry():
    """Verify registry module can be imported."""
    from meshpi import registry
    assert hasattr(registry, 'registry')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_pendrive():
    """Verify pendrive module can be imported."""
    pytest.importorskip("cryptography")
    from meshpi import pendrive
    assert hasattr(pendrive, 'export_to_pendrive')
    assert hasattr(pendrive, 'apply_from_pendrive')


@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
def test_import_hardware():
    """Verify hardware module can be imported."""
    from meshpi.hardware import profiles
    assert hasattr(profiles, 'list_profiles')


# ─────────────────────────────────────────────────────────────────────────────
# Crypto tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
class TestCrypto:
    """Tests for crypto module."""

    def test_key_generation(self, tmp_path):
        """Test RSA key pair generation."""
        pytest.importorskip("cryptography")
        from meshpi.crypto import get_or_create_host_keys, public_key_to_pem
        
        # Use temp directory for test
        import meshpi.crypto
        original_dir = meshpi.crypto.MESHPI_DIR
        meshpi.crypto.MESHPI_DIR = tmp_path
        
        try:
            priv, pub = get_or_create_host_keys()
            assert priv is not None
            assert pub is not None
            
            # Second call should return same keys (compare PEM representation)
            priv2, pub2 = get_or_create_host_keys()
            pub_pem1 = public_key_to_pem(pub)
            pub_pem2 = public_key_to_pem(pub2)
            assert pub_pem1 == pub_pem2
        finally:
            meshpi.crypto.MESHPI_DIR = original_dir

    def test_public_key_to_pem(self, tmp_path):
        """Test PEM encoding of public key."""
        pytest.importorskip("cryptography")
        from meshpi.crypto import get_or_create_host_keys, public_key_to_pem
        import meshpi.crypto
        
        original_dir = meshpi.crypto.MESHPI_DIR
        meshpi.crypto.MESHPI_DIR = tmp_path
        
        try:
            _, pub = get_or_create_host_keys()
            pem = public_key_to_pem(pub)
            assert isinstance(pem, bytes)
            assert b'-----BEGIN PUBLIC KEY-----' in pem
            assert b'-----END PUBLIC KEY-----' in pem
        finally:
            meshpi.crypto.MESHPI_DIR = original_dir


# ─────────────────────────────────────────────────────────────────────────────
# Host API tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
class TestHostApp:
    """Tests for FastAPI host application."""

    @pytest.fixture
    def test_app(self, tmp_path):
        """Create test FastAPI app."""
        pytest.importorskip("uvicorn")
        pytest.importorskip("fastapi")
        from meshpi import host, crypto, config
        import meshpi.crypto
        
        # Setup temp directory
        original_dir = meshpi.crypto.MESHPI_DIR
        meshpi.crypto.MESHPI_DIR = tmp_path
        
        # Generate keys
        host._host_private_key, host._host_public_key = crypto.get_or_create_host_keys()
        
        # Create minimal config
        config_file = tmp_path / "config.env"
        config_file.write_text("HOSTNAME=test-host\nWIFI_SSID=test\n")
        host._config = {"HOSTNAME": "test-host", "WIFI_SSID": "test"}
        
        yield host.app
        
        meshpi.crypto.MESHPI_DIR = original_dir

    def test_health_endpoint(self, test_app):
        """Test /health endpoint."""
        from fastapi.testclient import TestClient
        
        with TestClient(test_app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "online_clients" in data

    def test_info_endpoint(self, test_app):
        """Test /info endpoint."""
        from fastapi.testclient import TestClient
        
        with TestClient(test_app) as client:
            response = client.get("/info")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "meshpi-host"
            assert "host_public_key_pem" in data
            assert "hostname" in data


# ─────────────────────────────────────────────────────────────────────────────
# CLI tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not meshpi_installed, reason="meshpi package not installed")
class TestCLI:
    """Tests for CLI commands."""

    def test_cli_main_group(self):
        """Test CLI main group exists."""
        pytest.importorskip("click")
        import click
        from meshpi.cli import main
        assert isinstance(main, click.Group)

    def test_cli_has_commands(self):
        """Test CLI has expected commands."""
        pytest.importorskip("click")
        from meshpi.cli import main
        
        commands = list(main.commands.keys())
        assert 'config' in commands
        assert 'host' in commands
        assert 'scan' in commands
        assert 'daemon' in commands
        assert 'diag' in commands
        assert 'hw' in commands
        assert 'agent' in commands
        assert 'pendrive' in commands
        assert 'info' in commands

    def test_cli_version(self):
        """Test CLI version."""
        import meshpi
        assert hasattr(meshpi, '__version__')
        assert meshpi.__version__


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests (with Docker)
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:
    """Integration tests requiring running host service."""

    @pytest.fixture
    def host_url(self):
        """Get host URL from environment or skip test."""
        host = os.environ.get('MESHPI_TEST_HOST', 'localhost')
        port = os.environ.get('MESHPI_TEST_PORT', '7422')
        return f"http://{host}:{port}"

    @pytest.mark.skipif(
        not os.environ.get('MESHPI_TEST_HOST'),
        reason="Set MESHPI_TEST_HOST to run integration tests"
    )
    def test_host_health(self, host_url):
        """Test host health endpoint."""
        pytest.importorskip("httpx")
        import httpx
        
        response = httpx.get(f"{host_url}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.skipif(
        not os.environ.get('MESHPI_TEST_HOST'),
        reason="Set MESHPI_TEST_HOST to run integration tests"
    )
    def test_host_info(self, host_url):
        """Test host info endpoint."""
        pytest.importorskip("httpx")
        import httpx
        
        response = httpx.get(f"{host_url}/info", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "meshpi-host"
        assert "host_public_key_pem" in data

    @pytest.mark.skipif(
        not os.environ.get('MESHPI_TEST_HOST'),
        reason="Set MESHPI_TEST_HOST to run integration tests"
    )
    def test_config_delivery(self, host_url, tmp_path):
        """Test encrypted config delivery."""
        pytest.importorskip("httpx")
        pytest.importorskip("cryptography")
        import httpx
        from meshpi.crypto import get_or_create_client_keys, public_key_to_pem, decrypt_config
        import meshpi.crypto
        
        meshpi.crypto.MESHPI_DIR = tmp_path
        
        # Generate client keys
        priv, pub = get_or_create_client_keys()
        pub_pem = public_key_to_pem(pub).decode()
        
        # Request config
        response = httpx.post(
            f"{host_url}/config",
            json={"client_public_key_pem": pub_pem},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "payload" in data