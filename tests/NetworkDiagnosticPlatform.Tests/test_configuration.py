"""Tests for configuration management."""

import pytest
from pathlib import Path
from NetworkDiagnosticPlatform.configuration import (
    RuleConfig,
    PlatformConfig,
    ConfigurationManager
)


class TestRuleConfig:
    """Tests for rule configuration."""
    
    def test_rule_config_creation(self):
        """Test rule config can be created."""
        rule = RuleConfig(
            name="Test Rule",
            enabled=True,
            description="Test description",
            priority=100
        )
        
        assert rule.name == "Test Rule"
        assert rule.enabled is True
        assert rule.priority == 100


class TestPlatformConfig:
    """Tests for platform configuration."""
    
    def test_platform_config_initialization(self):
        """Test platform config initializes with defaults."""
        config = PlatformConfig()
        
        assert config.platform_name == "Enterprise Endpoint Diagnostic Platform"
        assert config.version == "0.1.0"
        assert config.offline_mode is True
        assert config.log_level == "INFO"
    
    def test_platform_config_to_dict(self):
        """Test platform config can be converted to dictionary."""
        config = PlatformConfig()
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert "platform_name" in data
        assert "version" in data
        assert "rules" in data
    
    def test_platform_config_save_and_load(self, tmp_path):
        """Test platform config can be saved and loaded."""
        filepath = tmp_path / "config.json"
        
        # Create and save config
        config = PlatformConfig(version="1.2.3")
        config.save(filepath)
        
        assert filepath.exists()
        
        # Load config
        loaded = PlatformConfig.load(filepath)
        assert loaded.version == "1.2.3"


class TestConfigurationManager:
    """Tests for configuration manager."""
    
    def test_configuration_manager_initialization(self, tmp_path):
        """Test configuration manager initializes."""
        mgr = ConfigurationManager(config_dir=tmp_path)
        
        assert mgr is not None
        assert mgr.config is not None
        assert mgr.main_config_path.exists()
    
    def test_enable_disable_rules(self, tmp_path):
        """Test enabling and disabling rules."""
        mgr = ConfigurationManager(config_dir=tmp_path)
        
        # Get a rule to test with
        rules = mgr.config.rules
        if rules:
            rule_name = list(rules.keys())[0]
            
            # Disable it
            mgr.disable_rule(rule_name)
            assert mgr.config.rules[rule_name].enabled is False
            
            # Enable it
            mgr.enable_rule(rule_name)
            assert mgr.config.rules[rule_name].enabled is True
    
    def test_set_rule_parameter(self, tmp_path):
        """Test setting rule parameters."""
        mgr = ConfigurationManager(config_dir=tmp_path)
        
        rules = mgr.config.rules
        if rules:
            rule_name = list(rules.keys())[0]
            mgr.set_rule_parameter(rule_name, "test_param", "test_value")
            
            assert mgr.config.rules[rule_name].parameters["test_param"] == "test_value"
    
    def test_get_enabled_rules(self, tmp_path):
        """Test getting only enabled rules."""
        mgr = ConfigurationManager(config_dir=tmp_path)
        
        enabled = mgr.get_enabled_rules()
        
        assert isinstance(enabled, dict)
        for rule in enabled.values():
            assert rule.enabled is True
    
    def test_save_and_import_config(self, tmp_path):
        """Test exporting and importing configuration."""
        mgr = ConfigurationManager(config_dir=tmp_path)
        
        export_path = tmp_path / "exported_config.json"
        mgr.export_config(export_path)
        
        assert export_path.exists()
        
        # Create new manager and import
        mgr2 = ConfigurationManager(config_dir=tmp_path / "new_config")
        mgr2.import_config(export_path)
        
        # Verify they have same number of rules
        assert len(mgr2.config.rules) == len(mgr.config.rules)
