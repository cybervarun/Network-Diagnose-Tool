"""Network Diagnostic Platform package."""

from .rule_engine import RuleEngine, Finding
from .evidence_collector import WindowsEvidenceCollector, EvidenceSnapshot
from .reporting import ReportGenerator
from .configuration import ConfigurationManager, PlatformConfig
from .knowledge import KnowledgeBase

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
    "KnowledgeBase",
]


def __getattr__(name: str):
    """Lazily expose CLI symbols without preloading the CLI module."""
    if name in {"DiagnosticCLI", "main"}:
        from .cli import DiagnosticCLI, main

        return {"DiagnosticCLI": DiagnosticCLI, "main": main}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

