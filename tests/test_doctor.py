"""
Tests for meshpi.doctor module.
"""

import pytest
from meshpi.doctor import parse_target, RemoteDoctor


class TestParseTarget:
    """Tests for parse_target function."""

    def test_parse_target_with_user(self):
        """Parse target with user specified."""
        user, host, port = parse_target("pi@192.168.1.100")
        assert user == "pi"
        assert host == "192.168.1.100"
        assert port == 22

    def test_parse_target_without_user(self):
        """Parse target without user (default user)."""
        user, host, port = parse_target("192.168.1.100")
        assert user == "pi"  # Default user
        assert host == "192.168.1.100"
        assert port == 22

    def test_parse_target_with_port(self):
        """Parse target with custom port."""
        user, host, port = parse_target("pi@192.168.1.100:2222")
        assert user == "pi"
        assert host == "192.168.1.100"
        assert port == 2222

    def test_parse_target_hostname(self):
        """Parse target with hostname."""
        user, host, port = parse_target("pi@raspberrypi")
        assert user == "pi"
        assert host == "raspberrypi"
        assert port == 22

    def test_parse_target_hostname_with_port(self):
        """Parse target with hostname and custom port."""
        user, host, port = parse_target("pi@raspberrypi:2222")
        assert user == "pi"
        assert host == "raspberrypi"
        assert port == 2222

    def test_parse_target_just_hostname(self):
        """Parse target with just hostname."""
        user, host, port = parse_target("raspberrypi")
        assert user == "pi"  # Default user
        assert host == "raspberrypi"
        assert port == 22

    def test_parse_target_just_hostname_with_port(self):
        """Parse target with just hostname and port."""
        user, host, port = parse_target("raspberrypi:2222")
        assert user == "pi"
        assert host == "raspberrypi"
        assert port == 2222


class TestRemoteDoctor:
    """Tests for RemoteDoctor class."""

    def test_remote_doctor_init(self):
        """Test RemoteDoctor initialization."""
        doctor = RemoteDoctor("192.168.1.100", "pi", 22)
        assert doctor.host == "192.168.1.100"
        assert doctor.user == "pi"
        assert doctor.port == 22
        assert doctor.client is None
        assert not doctor._connected

    def test_remote_doctor_custom_port(self):
        """Test RemoteDoctor with custom port."""
        doctor = RemoteDoctor("192.168.1.100", "pi", 2222)
        assert doctor.port == 2222

    def test_remote_doctor_disconnect_without_connection(self):
        """Test disconnect when not connected."""
        doctor = RemoteDoctor("192.168.1.100", "pi", 22)
        # Should not raise an error
        doctor.disconnect()
        assert not doctor._connected