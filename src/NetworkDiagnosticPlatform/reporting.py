from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .rule_engine import Finding

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates reports from diagnostic findings in multiple formats."""

    def __init__(self, output_dir: str = ".") -> None:
        """Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_text_report(self, findings: List[Finding], hostname: str = "endpoint") -> str:
        """Generate plain-text report.
        
        Args:
            findings: List of findings
            hostname: Endpoint hostname
            
        Returns:
            Formatted text report
        """
        if not findings:
            return "No findings detected."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "╔════════════════════════════════════════════════════════════════╗",
            "║        ENTERPRISE ENDPOINT DIAGNOSTIC REPORT                    ║",
            "╚════════════════════════════════════════════════════════════════╝",
            "",
            f"Hostname: {hostname}",
            f"Generated: {timestamp}",
            f"Total Findings: {len(findings)}",
            "",
        ]

        # Group findings by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(
            findings,
            key=lambda f: severity_order.get(f.severity.lower(), 99)
        )

        current_severity = None
        for finding in sorted_findings:
            if finding.severity != current_severity:
                current_severity = finding.severity
                lines.append("")
                lines.append(f"─── {current_severity.upper()} SEVERITY ───")
                lines.append("")

            lines.append(f"▶ {finding.title}")
            lines.append(f"  Severity: [{finding.severity.upper()}]")
            lines.append("")
            lines.append(f"  Explanation:")
            lines.append(f"  {finding.explanation}")
            lines.append("")

            if finding.root_cause:
                lines.append(f"  Root Cause:")
                lines.append(f"  {finding.root_cause}")
                lines.append("")

            if finding.evidence:
                lines.append("  Supporting Evidence:")
                for evidence in finding.evidence:
                    lines.append(f"  • {evidence}")
                lines.append("")

            if finding.recommended_actions:
                lines.append("  Recommended Actions:")
                for i, action in enumerate(finding.recommended_actions, 1):
                    lines.append(f"  {i}. {action}")
                lines.append("")

            if finding.learning_articles:
                lines.append("  💡 Learning Articles:")
                for article in finding.learning_articles:
                    lines.append(f"  • {article}")
                lines.append("")

            if finding.escalation_criteria:
                lines.append("  ⚠️ Escalation Criteria:")
                for criteria in finding.escalation_criteria:
                    lines.append(f"  • {criteria}")
                lines.append("")

        lines.append("─" * 66)
        lines.append("End of Report")

        return "\n".join(lines)

    def generate_html_report(self, findings: List[Finding], hostname: str = "endpoint") -> str:
        """Generate HTML report.
        
        Args:
            findings: List of findings
            hostname: Endpoint hostname
            
        Returns:
            HTML formatted report
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Group findings by severity
        severity_groups = {}
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#17a2b8",
            "info": "#0c5460"
        }
        
        for finding in findings:
            severity = finding.severity.lower()
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(finding)

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "<title>Enterprise Endpoint Diagnostic Report</title>",
            "<style>",
            """
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                }
                .container {
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    padding: 40px;
                }
                .header {
                    border-bottom: 3px solid #667eea;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                }
                .header h1 {
                    margin: 0 0 10px 0;
                    color: #667eea;
                }
                .metadata {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 30px;
                    font-size: 14px;
                }
                .metadata-item {
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 4px;
                }
                .metadata-item strong {
                    display: block;
                    color: #667eea;
                    margin-bottom: 5px;
                }
                .finding {
                    margin: 20px 0;
                    padding: 20px;
                    border-left: 5px solid;
                    border-radius: 4px;
                    background: #f8f9fa;
                }
                .severity-critical { border-left-color: #dc3545; background: #f8d7da; }
                .severity-high { border-left-color: #fd7e14; background: #fff3cd; }
                .severity-medium { border-left-color: #ffc107; background: #fff3cd; }
                .severity-low { border-left-color: #17a2b8; background: #d1ecf1; }
                .severity-info { border-left-color: #0c5460; background: #d1ecf1; }
                .finding-title {
                    font-size: 18px;
                    font-weight: bold;
                    margin: 0 0 10px 0;
                }
                .severity-badge {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    margin-left: 10px;
                }
                .section-title {
                    font-weight: bold;
                    color: #333;
                    margin-top: 15px;
                    margin-bottom: 8px;
                    font-size: 13px;
                }
                .evidence-list, .actions-list, .articles-list, .escalation-list {
                    margin: 10px 0;
                    padding-left: 20px;
                }
                .evidence-list li, .actions-list li, .articles-list li, .escalation-list li {
                    margin: 5px 0;
                    font-size: 14px;
                }
                .no-findings {
                    padding: 40px;
                    text-align: center;
                    color: #666;
                    font-size: 18px;
                }
                .summary {
                    background: #e7f3ff;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin-bottom: 30px;
                    border-radius: 4px;
                }
                .summary-item {
                    display: inline-block;
                    margin-right: 30px;
                    font-size: 14px;
                }
                .summary-count {
                    font-weight: bold;
                    color: #2196F3;
                }
                .footer {
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }
            """,
            "</style>",
            "</head>",
            "<body>",
            '<div class="container">',
            '<div class="header">',
            '<h1>Enterprise Endpoint Diagnostic Report</h1>',
            f'<p style="margin: 0; color: #666;">Comprehensive network and system diagnostics</p>',
            '</div>',
            '<div class="metadata">',
            f'<div class="metadata-item"><strong>Hostname:</strong> {hostname}</div>',
            f'<div class="metadata-item"><strong>Generated:</strong> {timestamp}</div>',
            '</div>',
        ]

        if findings:
            # Summary
            severity_counts = {}
            for finding in findings:
                severity = finding.severity.lower()
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            html_parts.append('<div class="summary">')
            html_parts.append('<strong>Summary:</strong><br>')
            for severity in ["critical", "high", "medium", "low", "info"]:
                if severity in severity_counts:
                    html_parts.append(
                        f'<div class="summary-item">{severity.capitalize()}: '
                        f'<span class="summary-count">{severity_counts[severity]}</span></div>'
                    )
            html_parts.append('</div>')

            # Findings grouped by severity
            for severity in ["critical", "high", "medium", "low", "info"]:
                if severity not in severity_groups:
                    continue

                html_parts.append(f'<h2 style="color: {severity_colors[severity]}; margin-top: 30px;">'
                                f'{severity.upper()} SEVERITY FINDINGS</h2>')

                for finding in severity_groups[severity]:
                    html_parts.append(
                        f'<div class="finding severity-{severity}">'
                    )
                    html_parts.append(
                        f'<div class="finding-title">'
                        f'{finding.title}'
                        f'<span class="severity-badge" style="background-color: {severity_colors[severity]};">'
                        f'{finding.severity.upper()}</span></div>'
                    )

                    html_parts.append(f'<p><strong>Explanation:</strong></p>')
                    html_parts.append(f'<p>{finding.explanation}</p>')

                    if finding.root_cause:
                        html_parts.append(f'<p><strong>Root Cause:</strong></p>')
                        html_parts.append(f'<p>{finding.root_cause}</p>')

                    if finding.evidence:
                        html_parts.append(
                            '<p class="section-title">Supporting Evidence:</p>'
                            '<ul class="evidence-list">'
                        )
                        for evidence in finding.evidence:
                            html_parts.append(f'<li>{evidence}</li>')
                        html_parts.append('</ul>')

                    if finding.recommended_actions:
                        html_parts.append(
                            '<p class="section-title">Recommended Actions:</p>'
                            '<ol class="actions-list">'
                        )
                        for action in finding.recommended_actions:
                            html_parts.append(f'<li>{action}</li>')
                        html_parts.append('</ol>')

                    if finding.learning_articles:
                        html_parts.append(
                            '<p class="section-title">💡 Learning Articles:</p>'
                            '<ul class="articles-list">'
                        )
                        for article in finding.learning_articles:
                            html_parts.append(f'<li>{article}</li>')
                        html_parts.append('</ul>')

                    if finding.escalation_criteria:
                        html_parts.append(
                            '<p class="section-title">⚠️ Escalation Criteria:</p>'
                            '<ul class="escalation-list">'
                        )
                        for criteria in finding.escalation_criteria:
                            html_parts.append(f'<li>{criteria}</li>')
                        html_parts.append('</ul>')

                    html_parts.append('</div>')
        else:
            html_parts.append('<div class="no-findings">No findings detected. System appears healthy.</div>')

        html_parts.extend([
            '<div class="footer">',
            f'<p>Report generated on {timestamp} by Enterprise Endpoint Diagnostic Platform</p>',
            '</div>',
            '</div>',
            '</body>',
            '</html>',
        ])

        return "\n".join(html_parts)

    def generate_json_report(self, findings: List[Finding], hostname: str = "endpoint") -> str:
        """Generate JSON report.
        
        Args:
            findings: List of findings
            hostname: Endpoint hostname
            
        Returns:
            JSON formatted report
        """
        report_data = {
            "metadata": {
                "hostname": hostname,
                "generated": datetime.now().isoformat(),
                "total_findings": len(findings),
                "findings_by_severity": {}
            },
            "findings": []
        }

        # Count by severity
        for finding in findings:
            severity = finding.severity.lower()
            report_data["metadata"]["findings_by_severity"][severity] = \
                report_data["metadata"]["findings_by_severity"].get(severity, 0) + 1

            report_data["findings"].append({
                "title": finding.title,
                "severity": finding.severity,
                "explanation": finding.explanation,
                "root_cause": finding.root_cause,
                "evidence": finding.evidence,
                "recommended_actions": finding.recommended_actions,
                "learning_articles": finding.learning_articles,
                "dependencies": finding.dependencies,
                "escalation_criteria": finding.escalation_criteria,
            })

        return json.dumps(report_data, indent=2)

    def save_report(self, findings: List[Finding], hostname: str = "endpoint", 
                   format: str = "text") -> str:
        """Save report to file.
        
        Args:
            findings: List of findings
            hostname: Endpoint hostname
            format: Report format (text, html, json)
            
        Returns:
            Path to saved report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "html":
            filename = f"diagnostic_report_{hostname}_{timestamp}.html"
            content = self.generate_html_report(findings, hostname)
        elif format == "json":
            filename = f"diagnostic_report_{hostname}_{timestamp}.json"
            content = self.generate_json_report(findings, hostname)
        else:
            filename = f"diagnostic_report_{hostname}_{timestamp}.txt"
            content = self.generate_text_report(findings, hostname)

        filepath = self.output_dir / filename
        
        try:
            filepath.write_text(content, encoding="utf-8")
            logger.info(f"Report saved to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise

    def generate(self, findings: List[Finding]) -> str:
        """Legacy method for backward compatibility."""
        return self.generate_text_report(findings)
