"""Configuration management for the diagnostic platform."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class RuleConfig:
    """Configuration for a diagnostic rule."""
    
    name: str
    enabled: bool = True
    description: str = ""
    priority: int = 0  # Higher = runs first
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformConfig:
    """Main platform configuration."""
    
    platform_name: str = "Enterprise Endpoint Diagnostic Platform"
    version: str = "0.1.0"
    offline_mode: bool = True
    output_dir: str = "./reports"
    log_level: str = "INFO"
    rules: Dict[str, RuleConfig] = field(default_factory=dict)
    enabled_report_formats: List[str] = field(
        default_factory=lambda: ["text", "html", "json"]
    )
    collect_full_diagnostics: bool = True
    timeout_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert RuleConfig objects to dicts
        data["rules"] = {
            name: asdict(rule) for name, rule in self.rules.items()
        }
        return data
    
    def save(self, filepath: str | Path) -> None:
        """Save configuration to JSON file.
        
        Args:
            filepath: Path to save configuration
        """
        filepath = Path(filepath)
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Configuration saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    @staticmethod
    def load(filepath: str | Path) -> PlatformConfig:
        """Load configuration from JSON file.
        
        Args:
            filepath: Path to configuration file
            
        Returns:
            Loaded PlatformConfig
        """
        filepath = Path(filepath)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Convert rule dicts back to RuleConfig objects
            rules = {}
            for name, rule_data in data.get("rules", {}).items():
                rules[name] = RuleConfig(**rule_data)
            data["rules"] = rules
            
            return PlatformConfig(**data)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise


class ConfigurationManager:
    """Manages platform configuration and rule definitions."""
    
    def __init__(self, config_dir: str | Path = "./config") -> None:
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.main_config_path = self.config_dir / "platform.json"
        self.rules_config_path = self.config_dir / "rules.json"
        
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self) -> PlatformConfig:
        """Load existing config or create default.
        
        Returns:
            PlatformConfig instance
        """
        if self.main_config_path.exists():
            try:
                return PlatformConfig.load(self.main_config_path)
            except Exception as e:
                logger.warning(f"Failed to load config, using defaults: {e}")
        
        # Create default config with common rules
        config = PlatformConfig()
        self._add_default_rules(config)
        config.save(self.main_config_path)
        return config
    
    def _add_default_rules(self, config: PlatformConfig) -> None:
        """Add default rule configurations.
        
        Args:
            config: Configuration object to update
        """
        default_rules = {
            "dns_resolution_failure": RuleConfig(
                name="DNS Resolution Failure",
                enabled=True,
                description="Detects when DNS resolution is failing",
                priority=100,
                dependencies=["network_adapter"],
            ),
            "missing_gateway": RuleConfig(
                name="Missing Default Gateway",
                enabled=True,
                description="Detects missing default gateway configuration",
                priority=95,
                dependencies=["network_adapter"],
            ),
            "no_internet": RuleConfig(
                name="No Internet Connectivity",
                enabled=True,
                description="Detects when internet connectivity is unavailable",
                priority=90,
                dependencies=["gateway_reachability"],
            ),
            "gateway_unreachable": RuleConfig(
                name="Gateway Unreachable",
                enabled=True,
                description="Detects when configured gateway is not reachable",
                priority=85,
                dependencies=["network_adapter"],
            ),
            "no_ip_address": RuleConfig(
                name="No IP Address",
                enabled=True,
                description="Detects when no IP address is assigned",
                priority=80,
                dependencies=["network_adapter"],
            ),
            "firewall_active": RuleConfig(
                name="Firewall Active",
                enabled=True,
                description="Informational: Windows Firewall is active",
                priority=10,
                dependencies=["system_info"],
            ),
        }
        
        config.rules.update(default_rules)
    
    def enable_rule(self, rule_name: str) -> None:
        """Enable a diagnostic rule.
        
        Args:
            rule_name: Name of rule to enable
        """
        if rule_name in self.config.rules:
            self.config.rules[rule_name].enabled = True
            logger.info(f"Enabled rule: {rule_name}")
    
    def disable_rule(self, rule_name: str) -> None:
        """Disable a diagnostic rule.
        
        Args:
            rule_name: Name of rule to disable
        """
        if rule_name in self.config.rules:
            self.config.rules[rule_name].enabled = False
            logger.info(f"Disabled rule: {rule_name}")
    
    def set_rule_parameter(self, rule_name: str, param_name: str, value: Any) -> None:
        """Set a rule parameter.
        
        Args:
            rule_name: Name of rule
            param_name: Parameter name
            value: Parameter value
        """
        if rule_name in self.config.rules:
            self.config.rules[rule_name].parameters[param_name] = value
            logger.info(f"Set {rule_name}.{param_name} = {value}")
    
    def get_enabled_rules(self) -> Dict[str, RuleConfig]:
        """Get only enabled rules.
        
        Returns:
            Dictionary of enabled rule configurations
        """
        return {
            name: rule for name, rule in self.config.rules.items()
            if rule.enabled
        }
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        self.config.save(self.main_config_path)
    
    def export_config(self, filepath: str | Path) -> None:
        """Export configuration to external file.
        
        Args:
            filepath: Path to export configuration
        """
        self.config.save(filepath)
    
    def import_config(self, filepath: str | Path) -> None:
        """Import configuration from external file.
        
        Args:
            filepath: Path to import configuration from
        """
        self.config = PlatformConfig.load(filepath)
        logger.info(f"Imported configuration from {filepath}")
