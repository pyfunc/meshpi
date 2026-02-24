"""
meshpi.alerts
=============
Alert engine for MeshPi fleet monitoring.

Provides configurable alerts with webhook notifications.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable, Any
from pathlib import Path
import yaml

import httpx


@dataclass
class AlertRule:
    """
    Alert rule definition.
    
    Attributes:
        name: Unique rule name
        condition: Function that takes diagnostics dict and returns True if alert should fire
        message_template: Message template with {placeholders} for diag values
        cooldown_seconds: Minimum time between repeated alerts
        severity: Alert severity (info, warning, critical)
        enabled: Whether rule is active
    """
    name: str
    condition: Callable[[dict], bool]
    message_template: str
    cooldown_seconds: int = 300
    severity: str = "warning"
    enabled: bool = True


@dataclass
class AlertConfig:
    """
    Alert configuration from YAML file.
    """
    webhooks: list[str] = field(default_factory=list)
    rules: list[dict] = field(default_factory=list)
    enabled: bool = True
    check_interval: int = 60


# Default alert rules
DEFAULT_RULES = [
    AlertRule(
        name="high_temperature",
        condition=lambda d: d.get("temperature", {}).get("cpu_gpu", 0) > 80,
        message_template="🌡️ {device_id}: Temperature {temperature}°C exceeds 80°C threshold",
        cooldown_seconds=300,
        severity="warning",
    ),
    AlertRule(
        name="critical_temperature",
        condition=lambda d: d.get("temperature", {}).get("cpu_gpu", 0) > 90,
        message_template="🔥 {device_id}: CRITICAL temperature {temperature}°C!",
        cooldown_seconds=60,
        severity="critical",
    ),
    AlertRule(
        name="device_offline",
        condition=lambda d: not d.get("online", True),
        message_template="❌ {device_id}: Device is offline",
        cooldown_seconds=60,
        severity="critical",
    ),
    AlertRule(
        name="high_cpu",
        condition=lambda d: d.get("cpu", {}).get("load_1m", 0) > 3.0,
        message_template="🔥 {device_id}: High CPU load {cpu_load}",
        cooldown_seconds=600,
        severity="warning",
    ),
    AlertRule(
        name="low_memory",
        condition=lambda d: d.get("memory", {}).get("used_percent", 0) > 90,
        message_template="💾 {device_id}: Memory usage {memory_percent}% is critical",
        cooldown_seconds=300,
        severity="warning",
    ),
    AlertRule(
        name="under_voltage",
        condition=lambda d: d.get("power", {}).get("under_voltage", False),
        message_template="⚡ {device_id}: Under-voltage detected - check power supply",
        cooldown_seconds=600,
        severity="warning",
    ),
    AlertRule(
        name="cpu_throttled",
        condition=lambda d: d.get("power", {}).get("currently_throttled", False),
        message_template="🐢 {device_id}: CPU is throttled - check cooling",
        cooldown_seconds=600,
        severity="warning",
    ),
    AlertRule(
        name="no_internet",
        condition=lambda d: not d.get("network", {}).get("ping_ok", True),
        message_template="🌐 {device_id}: No internet connectivity",
        cooldown_seconds=300,
        severity="info",
    ),
    AlertRule(
        name="weak_wifi",
        condition=lambda d: d.get("wifi", {}).get("signal", -100) > -80,
        message_template="📶 {device_id}: Weak WiFi signal {wifi_signal}dBm",
        cooldown_seconds=900,
        severity="info",
    ),
]


class AlertEngine:
    """
    Alert engine for monitoring device health and sending notifications.
    
    Example:
        engine = AlertEngine(webhooks=["https://hooks.slack.com/..."])
        await engine.evaluate("rpi-kitchen", diag_dict)
    """
    
    def __init__(
        self,
        webhooks: list[str] = None,
        rules: list[AlertRule] = None,
        config_path: Path = None,
    ):
        self.webhooks = webhooks or []
        self.rules = rules or DEFAULT_RULES.copy()
        self._last_fired: dict[str, float] = {}
        self._config_path = config_path or (Path.home() / ".meshpi" / "alerts.yml")
        
        # Load config if exists
        self._load_config()
    
    def _load_config(self) -> None:
        """Load alert configuration from YAML file."""
        if not self._config_path.exists():
            return
        
        try:
            with open(self._config_path) as f:
                config = yaml.safe_load(f) or {}
            
            # Load webhooks
            if "webhooks" in config:
                self.webhooks.extend(config["webhooks"])
            
            # Load custom rules
            for rule_def in config.get("rules", []):
                rule = self._parse_rule(rule_def)
                if rule:
                    # Replace existing rule with same name or add new
                    self.rules = [r for r in self.rules if r.name != rule.name]
                    self.rules.append(rule)
                    
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to load alert config: {e}")
    
    def _parse_rule(self, rule_def: dict) -> AlertRule | None:
        """Parse rule definition from config."""
        if "name" not in rule_def:
            return None
        
        name = rule_def["name"]
        threshold = rule_def.get("threshold", 80)
        cooldown = rule_def.get("cooldown", 300)
        severity = rule_def.get("severity", "warning")
        
        # Create condition based on rule type
        if name == "high_temperature":
            return AlertRule(
                name=name,
                condition=lambda d, t=threshold: d.get("temperature", {}).get("cpu_gpu", 0) > t,
                message_template=f"🌡️ {{device_id}}: Temperature {{temperature}}°C exceeds {t}°C",
                cooldown_seconds=cooldown,
                severity=severity,
            )
        elif name == "low_memory":
            return AlertRule(
                name=name,
                condition=lambda d, t=threshold: d.get("memory", {}).get("used_percent", 0) > t,
                message_template=f"💾 {{device_id}}: Memory usage {{memory_percent}}% exceeds {t}%",
                cooldown_seconds=cooldown,
                severity=severity,
            )
        elif name == "high_cpu":
            return AlertRule(
                name=name,
                condition=lambda d, t=threshold: d.get("cpu", {}).get("load_1m", 0) > t,
                message_template=f"🔥 {{device_id}}: CPU load {{cpu_load}} exceeds {t}",
                cooldown_seconds=cooldown,
                severity=severity,
            )
        
        return None
    
    def add_webhook(self, url: str) -> None:
        """Add a webhook URL."""
        if url not in self.webhooks:
            self.webhooks.append(url)
    
    def remove_webhook(self, url: str) -> None:
        """Remove a webhook URL."""
        if url in self.webhooks:
            self.webhooks.remove(url)
    
    def enable_rule(self, name: str) -> None:
        """Enable a specific rule."""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = True
                return
    
    def disable_rule(self, name: str) -> None:
        """Disable a specific rule."""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = False
                return
    
    async def evaluate(self, device_id: str, diag: dict) -> list[str]:
        """
        Evaluate all rules against device diagnostics.
        
        Args:
            device_id: Device identifier
            diag: Device diagnostics dictionary
        
        Returns:
            List of alert messages that were triggered
        """
        triggered = []
        now = time.time()
        
        # Add device_id to diag for message formatting
        diag = {**diag, "device_id": device_id}
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            key = f"{device_id}:{rule.name}"
            
            try:
                if rule.condition(diag):
                    # Check cooldown
                    if now - self._last_fired.get(key, 0) < rule.cooldown_seconds:
                        continue
                    
                    # Fire alert
                    self._last_fired[key] = now
                    
                    # Format message
                    message = self._format_message(rule.message_template, diag)
                    triggered.append(message)
                    
                    # Send to webhooks
                    await self._send_webhooks(message, device_id, rule.name, rule.severity)
                    
            except Exception as e:
                import warnings
                warnings.warn(f"Alert rule '{rule.name}' failed: {e}")
        
        return triggered
    
    def _format_message(self, template: str, diag: dict) -> str:
        """Format message template with diagnostic values."""
        # Extract commonly used values
        temp = diag.get("temperature", {})
        cpu = diag.get("cpu", {})
        mem = diag.get("memory", {})
        wifi = diag.get("wifi", {})
        
        values = {
            "device_id": diag.get("device_id", "unknown"),
            "temperature": temp.get("cpu_gpu") or temp.get("zone_0", "N/A"),
            "cpu_load": cpu.get("load_1m", "N/A"),
            "memory_percent": mem.get("used_percent", "N/A"),
            "wifi_signal": wifi.get("signal", "N/A"),
        }
        
        try:
            return template.format(**values)
        except KeyError:
            return template
    
    async def _send_webhooks(
        self, 
        message: str, 
        device_id: str,
        alert_type: str,
        severity: str
    ) -> None:
        """Send alert to all configured webhooks."""
        if not self.webhooks:
            return
        
        payload = {
            "text": message,
            "device_id": device_id,
            "alert_type": alert_type,
            "severity": severity,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in self.webhooks:
                try:
                    # Detect webhook type and format accordingly
                    if "slack.com" in url:
                        await client.post(url, json={"text": message})
                    elif "discord.com" in url:
                        await client.post(url, json={
                            "content": message,
                            "username": "MeshPi Alerts",
                        })
                    else:
                        # Generic webhook
                        await client.post(url, json=payload)
                except Exception as e:
                    import warnings
                    warnings.warn(f"Webhook {url} failed: {e}")
    
    def get_status(self) -> dict:
        """Get alert engine status."""
        return {
            "webhooks_count": len(self.webhooks),
            "rules_count": len(self.rules),
            "rules_enabled": sum(1 for r in self.rules if r.enabled),
            "recent_alerts": len([k for k, t in self._last_fired.items() 
                                  if time.time() - t < 3600]),
        }


def load_alerts_config(config_path: Path = None) -> AlertConfig:
    """
    Load alerts configuration from YAML file.
    
    Example config file:
    ```yaml
    webhooks:
      - https://hooks.slack.com/services/XXX/YYY/ZZZ
      - https://discord.com/api/webhooks/XXX/YYY
    
    rules:
      - name: high_temperature
        threshold: 80
        cooldown: 300
        severity: warning
    ```
    """
    config_path = config_path or (Path.home() / ".meshpi" / "alerts.yml")
    
    if not config_path.exists():
        return AlertConfig()
    
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}
    
    return AlertConfig(
        webhooks=data.get("webhooks", []),
        rules=data.get("rules", []),
        enabled=data.get("enabled", True),
        check_interval=data.get("check_interval", 60),
    )


def create_default_config(config_path: Path = None) -> None:
    """Create default alerts configuration file."""
    config_path = config_path or (Path.home() / ".meshpi" / "alerts.yml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = """# MeshPi Alerts Configuration
# 
# Add webhook URLs to receive alert notifications

webhooks:
  # - https://hooks.slack.com/services/XXX/YYY/ZZZ
  # - https://discord.com/api/webhooks/XXX/YYY

# Custom alert rules (override defaults)
rules:
  # - name: high_temperature
  #   threshold: 80
  #   cooldown: 300
  #   severity: warning

  # - name: low_memory
  #   threshold: 90
  #   cooldown: 300
  #   severity: warning

# Global settings
enabled: true
check_interval: 60  # seconds
"""
    
    config_path.write_text(default_config)


# Global alert engine instance
_alert_engine: AlertEngine | None = None


def get_alert_engine() -> AlertEngine:
    """Get or create global alert engine instance."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine