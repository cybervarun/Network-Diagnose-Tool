"""Tests for enhanced rule engine."""

import pytest
from NetworkDiagnosticPlatform.rule_engine import RuleEngine, Finding


class TestRuleEngine:
    """Tests for the rule engine."""
    
    def test_rule_engine_initialization(self):
        """Test rule engine initializes with rules."""
        engine = RuleEngine()
        assert engine.rules is not None
        assert len(engine.rules) > 3  # At least more than original 3
    
    def test_dns_resolution_failure_rule(self):
        """Test DNS resolution failure detection."""
        engine = RuleEngine()
        evidence = {
            "dns_resolves": False,
            "default_gateway": "192.168.1.1",
            "internet_reachable": True,
            "dns_servers": ["8.8.8.8"],
            "ip_addresses": ["192.168.1.100"],
        }
        
        findings = engine.analyze(evidence)
        
        dns_findings = [f for f in findings if "DNS" in f.title]
        assert len(dns_findings) > 0
        assert dns_findings[0].severity == "high"
    
    def test_missing_gateway_rule(self):
        """Test missing gateway detection."""
        engine = RuleEngine()
        evidence = {
            "dns_resolves": True,
            "default_gateway": None,
            "internet_reachable": False,
            "ip_addresses": ["192.168.1.100"],
        }
        
        findings = engine.analyze(evidence)
        
        gateway_findings = [f for f in findings if "gateway" in f.title.lower()]
        assert len(gateway_findings) > 0
        assert gateway_findings[0].severity == "high"
    
    def test_no_internet_rule(self):
        """Test internet connectivity failure detection."""
        engine = RuleEngine()
        evidence = {
            "dns_resolves": True,
            "default_gateway": "192.168.1.1",
            "internet_reachable": False,
            "gateway_reachable": True,
        }
        
        findings = engine.analyze(evidence)
        
        internet_findings = [f for f in findings if "internet" in f.title.lower()]
        assert len(internet_findings) > 0
        assert internet_findings[0].severity == "high"
    
    def test_gateway_unreachable_rule(self):
        """Test unreachable gateway detection."""
        engine = RuleEngine()
        evidence = {
            "default_gateway": "192.168.1.1",
            "gateway_reachable": False,
        }
        
        findings = engine.analyze(evidence)
        
        gateway_findings = [
            f for f in findings
            if "gateway" in f.title.lower() and "unreachable" in f.title.lower()
        ]
        assert len(gateway_findings) > 0
    
    def test_no_ip_address_rule(self):
        """Test no IP address detection."""
        engine = RuleEngine()
        evidence = {
            "ip_addresses": [],
            "adapter_status": {"Ethernet": "Media connected"},
        }
        
        findings = engine.analyze(evidence)
        
        ip_findings = [f for f in findings if "IP Address" in f.title]
        assert len(ip_findings) > 0
    
    def test_firewall_active_rule(self):
        """Test firewall status detection."""
        engine = RuleEngine()
        evidence = {
            "firewall_status": "ON",
        }
        
        findings = engine.analyze(evidence)
        
        firewall_findings = [f for f in findings if "firewall" in f.title.lower()]
        assert len(firewall_findings) > 0
        assert firewall_findings[0].severity == "info"
    
    def test_finding_has_required_fields(self):
        """Test finding has all required fields."""
        engine = RuleEngine()
        evidence = {
            "dns_resolves": False,
            "default_gateway": "192.168.1.1",
        }
        
        findings = engine.analyze(evidence)
        
        if findings:
            finding = findings[0]
            
            assert finding.title is not None
            assert finding.severity is not None
            assert finding.explanation is not None
            assert finding.evidence is not None
            assert finding.recommended_actions is not None
            assert finding.learning_articles is not None
            assert finding.escalation_criteria is not None
    
    def test_multiple_findings(self):
        """Test multiple issues detected simultaneously."""
        engine = RuleEngine()
        evidence = {
            "dns_resolves": False,
            "default_gateway": None,
            "internet_reachable": False,
            "ip_addresses": [],
            "adapter_status": {"Ethernet": "Disconnected"},
        }
        
        findings = engine.analyze(evidence)
        
        # Should detect multiple issues
        assert len(findings) >= 3
    
    def test_plugin_rules_are_loaded_from_directory(self, tmp_path):
        """Test plugin rules can be loaded from a plugin directory."""
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        plugin_path = plugin_dir / "custom_plugin.py"
        plugin_path.write_text(
            """
from NetworkDiagnosticPlatform.rule_engine import Finding


def custom_rule(evidence):
    if evidence.get('custom_flag'):
        return Finding(
            title='Custom Plugin Finding',
            severity='medium',
            explanation='Loaded from a plugin module',
            root_cause='Plugin rule executed successfully',
            evidence=['custom_flag was true'],
            recommended_actions=['Review the plugin output'],
            learning_articles=[],
            escalation_criteria=[],
        )
    return None


def get_rules():
    return [custom_rule]
""".strip()
        )

        engine = RuleEngine(plugin_paths=[str(plugin_dir)])
        findings = engine.analyze({"custom_flag": True})

        assert any(f.title == "Custom Plugin Finding" for f in findings)

    def test_healthy_endpoint(self):
        """Test healthy endpoint produces minimal findings."""
        engine = RuleEngine()
        evidence = {
            "dns_resolves": True,
            "dns_servers": ["8.8.8.8", "8.8.4.4"],
            "default_gateway": "192.168.1.1",
            "internet_reachable": True,
            "gateway_reachable": True,
            "ip_addresses": ["192.168.1.100"],
            "firewall_status": "ON",
            "adapter_status": {"Ethernet": "Media connected"},
        }
        
        findings = engine.analyze(evidence)
        
        # Healthy endpoint might have info-level findings (like firewall)
        high_severity = [f for f in findings if f.severity in ["critical", "high"]]
        assert len(high_severity) == 0
