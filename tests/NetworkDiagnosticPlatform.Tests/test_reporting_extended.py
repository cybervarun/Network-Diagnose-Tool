"""Tests for report generation."""

import pytest
from pathlib import Path
from NetworkDiagnosticPlatform.reporting import ReportGenerator
from NetworkDiagnosticPlatform.rule_engine import Finding


class TestReportGenerator:
    """Tests for report generation."""
    
    def create_sample_findings(self):
        """Create sample findings for testing."""
        return [
            Finding(
                title="DNS Resolution Failure",
                severity="high",
                explanation="DNS could not resolve hostnames.",
                root_cause="DNS server unreachable",
                evidence=["DNS test returned false"],
                recommended_actions=["Verify DNS servers", "Flush DNS cache"],
                learning_articles=["DNS Fundamentals"],
                escalation_criteria=["Persists after restart"],
            ),
            Finding(
                title="No Internet Connectivity",
                severity="high",
                explanation="Cannot reach external services.",
                evidence=["Ping to 8.8.8.8 failed"],
                recommended_actions=["Check firewall", "Verify gateway"],
            ),
            Finding(
                title="Firewall Active",
                severity="info",
                explanation="Windows Firewall is enabled.",
                evidence=["Firewall status ON"],
            ),
        ]
    
    def test_report_generator_initialization(self, tmp_path):
        """Test report generator initializes."""
        gen = ReportGenerator(output_dir=str(tmp_path))
        assert gen is not None
        assert gen.output_dir == tmp_path
    
    def test_generate_text_report(self):
        """Test text report generation."""
        gen = ReportGenerator()
        findings = self.create_sample_findings()
        
        report = gen.generate_text_report(findings, hostname="test-pc")
        
        assert "ENTERPRISE ENDPOINT DIAGNOSTIC REPORT" in report
        assert "DNS Resolution Failure" in report
        assert "HIGH SEVERITY" in report
        assert "INFO SEVERITY" in report
    
    def test_text_report_includes_all_sections(self):
        """Test text report includes all finding sections."""
        gen = ReportGenerator()
        finding = Finding(
            title="Test Issue",
            severity="high",
            explanation="This is a test",
            root_cause="Root cause",
            evidence=["Evidence 1"],
            recommended_actions=["Action 1"],
            learning_articles=["Article 1"],
            escalation_criteria=["Criteria 1"],
        )
        
        report = gen.generate_text_report([finding])
        
        assert "Test Issue" in report
        assert "Root Cause:" in report
        assert "Evidence:" in report
        assert "Recommended Actions:" in report
        assert "Learning Articles:" in report
        assert "Escalation Criteria:" in report
    
    def test_generate_html_report(self):
        """Test HTML report generation."""
        gen = ReportGenerator()
        findings = self.create_sample_findings()
        
        report = gen.generate_html_report(findings, hostname="test-pc")
        
        assert "<!DOCTYPE html>" in report
        assert "<html>" in report
        assert "</html>" in report
        assert "Enterprise Endpoint Diagnostic Report" in report
        assert "test-pc" in report
        assert "DNS Resolution Failure" in report
    
    def test_html_report_styling(self):
        """Test HTML report includes styling."""
        gen = ReportGenerator()
        findings = self.create_sample_findings()
        
        report = gen.generate_html_report(findings)
        
        assert "<style>" in report
        assert "</style>" in report
        assert "body {" in report
        assert ".finding" in report
    
    def test_generate_json_report(self):
        """Test JSON report generation."""
        gen = ReportGenerator()
        findings = self.create_sample_findings()
        
        report = gen.generate_json_report(findings, hostname="test-pc")
        
        import json
        data = json.loads(report)
        
        assert "metadata" in data
        assert "findings" in data
        assert data["metadata"]["hostname"] == "test-pc"
        assert len(data["findings"]) == 3
    
    def test_json_report_structure(self):
        """Test JSON report has correct structure."""
        gen = ReportGenerator()
        finding = Finding(
            title="Test",
            severity="high",
            explanation="Test explanation",
        )
        
        report = gen.generate_json_report([finding])
        
        import json
        data = json.loads(report)
        
        assert "findings_by_severity" in data["metadata"]
        assert "high" in data["metadata"]["findings_by_severity"]
        assert data["metadata"]["findings_by_severity"]["high"] == 1
    
    def test_save_text_report(self, tmp_path):
        """Test saving text report to file."""
        gen = ReportGenerator(output_dir=str(tmp_path))
        findings = self.create_sample_findings()
        
        filepath = gen.save_report(findings, format="text")
        
        assert Path(filepath).exists()
        assert filepath.endswith(".txt")
        
        # Read with UTF-8 encoding to handle box-drawing characters
        content = Path(filepath).read_text(encoding="utf-8")
        assert "ENDPOINT DIAGNOSTIC REPORT" in content or "diagnostic" in content.lower()
    
    def test_save_html_report(self, tmp_path):
        """Test saving HTML report to file."""
        gen = ReportGenerator(output_dir=str(tmp_path))
        findings = self.create_sample_findings()
        
        filepath = gen.save_report(findings, format="html")
        
        assert Path(filepath).exists()
        assert filepath.endswith(".html")
    
    def test_save_json_report(self, tmp_path):
        """Test saving JSON report to file."""
        gen = ReportGenerator(output_dir=str(tmp_path))
        findings = self.create_sample_findings()
        
        filepath = gen.save_report(findings, format="json")
        
        assert Path(filepath).exists()
        assert filepath.endswith(".json")
        
        import json
        with open(filepath) as f:
            data = json.load(f)
        assert "metadata" in data
    
    def test_no_findings_report(self):
        """Test report generation with no findings."""
        gen = ReportGenerator()
        
        text_report = gen.generate_text_report([])
        assert "No findings detected" in text_report
        
        html_report = gen.generate_html_report([])
        assert "healthy" in html_report.lower() or "no findings" in html_report.lower()
    
    def test_hostname_in_report(self):
        """Test hostname appears in reports."""
        gen = ReportGenerator()
        findings = self.create_sample_findings()
        
        text = gen.generate_text_report(findings, hostname="workstation-01")
        html = gen.generate_html_report(findings, hostname="workstation-01")
        json_report = gen.generate_json_report(findings, hostname="workstation-01")
        
        assert "workstation-01" in text
        assert "workstation-01" in html
        assert "workstation-01" in json_report
