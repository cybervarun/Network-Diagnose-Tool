"""Tests for evidence collection."""

import pytest
from NetworkDiagnosticPlatform.evidence_collector import (
    WindowsEvidenceCollector,
    EvidenceSnapshot
)


class TestWindowsEvidenceCollector:
    """Tests for Windows evidence collector."""
    
    def test_collector_initialization(self):
        """Test collector can be initialized."""
        collector = WindowsEvidenceCollector(offline_mode=True)
        assert collector is not None
        assert collector.offline_mode is True
    
    def test_collect_all_offline_mode(self):
        """Test evidence collection in offline mode."""
        collector = WindowsEvidenceCollector(offline_mode=True)
        evidence = collector.collect_all()
        
        assert evidence is not None
        assert isinstance(evidence, EvidenceSnapshot)
        assert evidence.hostname == "test-pc"
        assert evidence.os_version != ""
        assert evidence.timestamp != ""
    
    def test_evidence_snapshot_has_required_fields(self):
        """Test evidence snapshot has all required fields."""
        collector = WindowsEvidenceCollector(offline_mode=True)
        evidence = collector.collect_all()
        
        assert evidence.timestamp is not None
        assert evidence.hostname is not None
        assert evidence.os_version is not None
        assert evidence.dns_servers is not None
        assert evidence.dns_resolves is not None
        assert evidence.default_gateway is not None
        assert evidence.ip_addresses is not None
        assert evidence.gateway_reachable is not None
        assert evidence.internet_reachable is not None
    
    def test_evidence_to_dict_conversion(self):
        """Test evidence can be converted to dictionary."""
        collector = WindowsEvidenceCollector(offline_mode=True)
        evidence = collector.collect_all()
        
        evidence_dict = evidence.to_dict()
        
        assert isinstance(evidence_dict, dict)
        assert "hostname" in evidence_dict
        assert "dns_resolves" in evidence_dict
        assert "default_gateway" in evidence_dict
        assert "internet_reachable" in evidence_dict
    
    def test_export_evidence_to_json(self, tmp_path):
        """Test evidence can be exported to JSON file."""
        collector = WindowsEvidenceCollector(offline_mode=True)
        evidence = collector.collect_all()
        
        export_file = tmp_path / "evidence.json"
        # Create new collector just for this test since export needs collected_evidence set
        export_collector = WindowsEvidenceCollector(offline_mode=True)
        export_collector.collect_all()
        export_collector.export_evidence(str(export_file))
        
        assert export_file.exists()
        
        import json
        with open(export_file) as f:
            data = json.load(f)
        
        assert data["hostname"] == "test-pc"
        assert "timestamp" in data
