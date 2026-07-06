"""Portable path helpers for a no-install field toolkit."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def get_toolkit_root() -> Path:
    """Return the portable toolkit root directory.

    The toolkit should run from its own folder without system installation.
    This helper prefers the current working directory when it contains the
    project structure, otherwise it falls back to the repository root.
    """
    candidates = [Path.cwd(), Path(__file__).resolve().parents[2]]
    for candidate in candidates:
        if (candidate / "src" / "NetworkDiagnosticPlatform").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    return Path.cwd()


def resolve_output_dir(output_dir: Optional[str | os.PathLike[str]]) -> Path:
    """Resolve an output directory to a portable-safe path.

    If no path is supplied, the toolkit writes reports into a local reports
    directory under the toolkit root. Absolute paths are preserved for explicit
    CLI overrides.
    """
    if output_dir is None:
        return get_toolkit_root() / "reports"

    path = Path(output_dir)
    if path.is_absolute():
        return path
    return get_toolkit_root() / path


def resolve_config_dir(config_dir: Optional[str | os.PathLike[str]]) -> Path:
    """Resolve a configuration directory relative to the toolkit root."""
    if config_dir is None:
        return get_toolkit_root() / "config"

    path = Path(config_dir)
    if path.is_absolute():
        return path
    return get_toolkit_root() / path
