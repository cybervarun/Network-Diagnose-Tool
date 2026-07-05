from NetworkDiagnosticPlatform.reporting import ReportGenerator
from NetworkDiagnosticPlatform.rule_engine import Finding


def test_report_includes_findings():
    generator = ReportGenerator()
    report = generator.generate([
        Finding(
            title="DNS resolution failure",
            severity="high",
            explanation="DNS could not resolve hostnames.",
            evidence=["DNS test returned false"],
            recommended_actions=["Validate DNS servers"],
        )
    ])

    assert "ENTERPRISE ENDPOINT DIAGNOSTIC REPORT" in report or "DIAGNOSTIC REPORT" in report
    assert "DNS resolution failure" in report
    assert "Validate DNS servers" in report


def test_report_text_format():
    """Test basic text report generation."""
    generator = ReportGenerator()
    findings = [
        Finding(
            title="Test Finding",
            severity="high",
            explanation="Test explanation",
            evidence=["Test evidence"],
            recommended_actions=["Test action"],
        )
    ]
    
    report = generator.generate_text_report(findings)
    
    assert "Test Finding" in report
    assert "high" in report.lower()
    assert "Test action" in report


def test_empty_findings_report():
    """Test report with no findings."""
    generator = ReportGenerator()
    report = generator.generate([])
    
    assert "No findings detected" in report

