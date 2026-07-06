"""Command-line interface for the diagnostic platform."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .evidence_collector import WindowsEvidenceCollector
from .rule_engine import RuleEngine
from .reporting import ReportGenerator
from .configuration import ConfigurationManager
from .knowledge import KnowledgeBase


PACKAGE_VERSION = "0.1.0"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


class DiagnosticCLI:
    """Command-line interface for the diagnostic platform."""
    
    def __init__(self) -> None:
        """Initialize CLI."""
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigurationManager()
    
    def run_full_diagnostic(self, output_dir: str = "./reports",
                           hostname: Optional[str] = None,
                           formats: Optional[list[str]] = None,
                           offline: bool = False,
                           plugin_paths: Optional[list[str]] = None) -> str:
        """Run complete diagnostic analysis.
        
        Args:
            output_dir: Directory to save reports
            hostname: Optional hostname (auto-detected if not provided)
            formats: Report formats to generate (text, html, json)
            offline: Use offline/mock mode
            
        Returns:
            Path to primary report file
        """
        self.logger.info("Starting comprehensive diagnostic analysis...")
        
        if formats is None:
            formats = self.config_manager.config.enabled_report_formats
        
        try:
            # Step 1: Collect evidence
            self.logger.info("Collecting system evidence...")
            collector = WindowsEvidenceCollector(offline_mode=offline)
            evidence = collector.collect_all()
            
            if not hostname:
                hostname = evidence.hostname
            
            self.logger.info(f"Evidence collected for {hostname}")
            
            # Step 2: Analyze with rule engine
            self.logger.info("Running diagnostic rules...")
            engine = RuleEngine(plugin_paths=plugin_paths or [])
            findings = engine.analyze(evidence.to_dict())
            
            self.logger.info(f"Analysis complete: {len(findings)} findings")
            
            # Step 3: Generate reports
            self.logger.info("Generating reports...")
            report_generator = ReportGenerator(output_dir=output_dir)
            report_paths = []
            
            for fmt in formats:
                try:
                    path = report_generator.save_report(
                        findings,
                        hostname=hostname,
                        format=fmt.lower()
                    )
                    report_paths.append(path)
                    self.logger.info(f"Saved {fmt} report: {path}")
                except Exception as e:
                    self.logger.error(f"Failed to generate {fmt} report: {e}")
            
            # Step 4: Print summary
            self._print_summary(findings, len(report_paths))
            
            return report_paths[0] if report_paths else ""
            
        except Exception as e:
            self.logger.error(f"Diagnostic analysis failed: {e}")
            raise
    
    def _print_summary(self, findings, report_count: int) -> None:
        """Print diagnostic summary to console.
        
        Args:
            findings: List of diagnostic findings
            report_count: Number of reports generated
        """
        print("\n" + "=" * 70)
        print("DIAGNOSTIC ANALYSIS SUMMARY")
        print("=" * 70)
        
        severity_counts = {}
        for finding in findings:
            severity = finding.severity.lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print(f"\nTotal Findings: {len(findings)}")
        
        if severity_counts:
            print("\nFindings by Severity:")
            for severity in ["critical", "high", "medium", "low", "info"]:
                if severity in severity_counts:
                    count = severity_counts[severity]
                    print(f"  {severity.upper():12} : {count:3} finding(s)")
        else:
            print("\nNo findings detected - System appears healthy!")
        
        print(f"\nReports Generated: {report_count}")
        print("=" * 70 + "\n")
    
    def list_rules(self) -> None:
        """List all available diagnostic rules."""
        print("\nAvailable Diagnostic Rules:")
        print("=" * 70)
        
        rules = self.config_manager.config.rules
        
        enabled_count = sum(1 for r in rules.values() if r.enabled)
        total_count = len(rules)
        
        print(f"Total Rules: {total_count} ({enabled_count} enabled, {total_count - enabled_count} disabled)")
        print()
        
        for name, rule in sorted(rules.items(), key=lambda x: -x[1].priority):
            status = "[x] ENABLED " if rule.enabled else "[ ] DISABLED"
            print(f"{status} | Priority: {rule.priority:3} | {name}")
            if rule.description:
                print(f"         {rule.description}")
    
    def show_rule_details(self, rule_name: str) -> None:
        """Show details for a specific rule.
        
        Args:
            rule_name: Name of rule to show
        """
        rules = self.config_manager.config.rules
        
        matching = [r for r in rules.keys() if rule_name.lower() in r.lower()]
        
        if not matching:
            print(f"No rules found matching '{rule_name}'")
            return
        
        for rule_key in matching:
            rule = rules[rule_key]
            print(f"\nRule: {rule_key}")
            print("=" * 70)
            print(f"Name        : {rule.name}")
            print(f"Enabled     : {rule.enabled}")
            print(f"Priority    : {rule.priority}")
            print(f"Description : {rule.description}")
            if rule.dependencies:
                print(f"Dependencies: {', '.join(rule.dependencies)}")
            if rule.parameters:
                print(f"Parameters  : {rule.parameters}")

    def show_release_readiness(self) -> None:
        """Print a lightweight release-readiness summary."""
        kb = KnowledgeBase()
        project_root = Path(__file__).resolve().parents[2]
        pyproject = project_root / "pyproject.toml"
        build_script = project_root / "scripts" / "build_package.py"
        dist_dir = project_root / "dist"
        windows_bundle_dir = dist_dir / "windows"
        wheel_count = len(list(dist_dir.glob("*.whl"))) if dist_dir.exists() else 0
        sdist_count = len(list(dist_dir.glob("*.tar.gz"))) if dist_dir.exists() else 0
        has_windows_bundle = windows_bundle_dir.exists()

        print("\nRelease Readiness Summary")
        print("=" * 70)
        print(f"- Version: {PACKAGE_VERSION}")
        print("- Console entry point: network-diagnostic")
        print(f"- Packaging metadata: {'present' if pyproject.exists() else 'missing'}")
        print(f"- Build script: {'present' if build_script.exists() else 'missing'}")
        print(f"- Current wheel artifacts: {wheel_count}")
        print(f"- Current source distributions: {sdist_count}")
        print(f"- Windows install bundle: {'present' if has_windows_bundle else 'missing'}")
        print("- Windows console output: ASCII-safe")
        print("- Core diagnostics, reporting, and plugin rule loading: implemented")
        print(f"- Knowledge articles available: {len(kb.articles)}")
        print("- Recommended release command: python scripts/build_package.py --check --windows-bundle")
        print("- Final validation: run dist\\windows\\install.ps1 -OfflineSmokeTest on a clean Windows endpoint")

    def list_knowledge(self) -> list[dict[str, object]]:
        """List bundled troubleshooting knowledge articles."""
        kb = KnowledgeBase()
        articles = kb.list_articles()
        print("\nBundled Troubleshooting Articles")
        print("=" * 70)
        for article in articles:
            print(f"- {article['id']}: {article['title']} ({article['category']})")
            print(f"  {article['summary']}")
        return articles

    def search_knowledge(self, query: str) -> list[dict[str, object]]:
        """Search the bundled troubleshooting knowledge base."""
        kb = KnowledgeBase()
        results = kb.search(query)
        if not results:
            print(f"No knowledge articles found for '{query}'")
            return []

        print(f"\nKnowledge base matches for '{query}':")
        print("=" * 70)
        for result in results:
            print(f"- {result['id']}: {result['title']}")
            print(f"  {result['summary']}")
            print(f"  Category: {result['category']} | Severity: {result['severity']}")
        return results

    def show_knowledge_article(self, article_id: str) -> dict[str, object] | None:
        """Print one bundled troubleshooting article."""
        kb = KnowledgeBase()
        article = kb.get(article_id)
        if article is None:
            print(f"No knowledge article found with id '{article_id}'")
            return None

        print(f"\n{article['title']}")
        print("=" * 70)
        print(f"ID      : {article['id']}")
        print(f"Category: {article['category']}")
        print(f"Severity: {article['severity']}")
        print(f"Summary : {article['summary']}")

        for heading, key in [
            ("Symptoms", "symptoms"),
            ("Checks", "checks"),
            ("Fixes", "fixes"),
            ("Escalation", "escalation"),
            ("Related Rules", "related_rules"),
        ]:
            values = article.get(key, [])
            if values:
                print(f"\n{heading}:")
                for value in values:
                    print(f"- {value}")
        return article


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Enterprise Windows Endpoint Diagnostic Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Run full diagnostic with default settings
  %(prog)s -o /tmp/reports          Save reports to /tmp/reports
  %(prog)s --offline                Run in offline mode (testing)
  %(prog)s --format html,json       Generate HTML and JSON reports only
  %(prog)s --list-rules             Show all available diagnostic rules
  %(prog)s --rule-details dns       Show details for DNS-related rules
  %(prog)s --knowledge-list         Show bundled troubleshooting articles
  %(prog)s --knowledge-search dns   Search offline troubleshooting guidance
  %(prog)s --release-check          Show packaging and release readiness
        """
    )
    
    parser.add_argument(
        "-o", "--output",
        dest="output_dir",
        default="./reports",
        help="Output directory for reports (default: ./reports)"
    )
    
    parser.add_argument(
        "-H", "--hostname",
        help="Endpoint hostname (auto-detected if not provided)"
    )
    
    parser.add_argument(
        "-f", "--format",
        dest="formats",
        default="text,html,json",
        help="Report formats: text, html, json (default: all)"
    )
    
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run in offline mode (uses mock data for testing)"
    )
    
    parser.add_argument(
        "-l", "--list-rules",
        action="store_true",
        help="List all available diagnostic rules and exit"
    )
    
    parser.add_argument(
        "--rule-details",
        metavar="RULE",
        help="Show details for a specific rule"
    )
    
    parser.add_argument(
        "--plugin-path",
        dest="plugin_paths",
        nargs="*",
        default=[],
        help="One or more plugin directories or Python files containing custom rules"
    )
    
    parser.add_argument(
        "--release-check",
        action="store_true",
        help="Show a lightweight release-readiness summary"
    )

    parser.add_argument(
        "--knowledge-search",
        metavar="QUERY",
        help="Search the bundled troubleshooting knowledge base"
    )

    parser.add_argument(
        "--knowledge-list",
        action="store_true",
        help="List bundled troubleshooting knowledge articles"
    )

    parser.add_argument(
        "--knowledge-detail",
        metavar="ARTICLE_ID",
        help="Show detailed guidance for a bundled troubleshooting article"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Enterprise Endpoint Diagnostic Platform v0.1.0")
    
    cli = DiagnosticCLI()
    
    try:
        # Handle special commands
        if args.list_rules:
            cli.list_rules()
            return 0
        
        if args.rule_details:
            cli.show_rule_details(args.rule_details)
            return 0

        if args.release_check:
            cli.show_release_readiness()
            return 0

        if args.knowledge_list:
            cli.list_knowledge()
            return 0

        if args.knowledge_detail:
            article = cli.show_knowledge_article(args.knowledge_detail)
            return 0 if article is not None else 2

        if args.knowledge_search:
            cli.search_knowledge(args.knowledge_search)
            return 0
        
        # Run diagnostic
        formats = [f.strip() for f in args.formats.split(",")]
        cli.run_full_diagnostic(
            output_dir=args.output_dir,
            hostname=args.hostname,
            formats=formats,
            offline=args.offline,
            plugin_paths=args.plugin_paths
        )
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
