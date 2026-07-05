"""Network Diagnostic Platform package."""

from .rule_engine import RuleEngine, Finding
from .evidence_collector import WindowsEvidenceCollector, EvidenceSnapshot
from .reporting import ReportGenerator
from .configuration import ConfigurationManager, PlatformConfig
from .cli import DiagnosticCLI, main

__version__ = "0.1.0"
__all__ = [
    "RuleEngine",
    "Finding",
    "WindowsEvidenceCollector",
    "EvidenceSnapshot",
    "ReportGenerator",
    "ConfigurationManager",
    "PlatformConfig",
    "DiagnosticCLI",
    "main",
]

