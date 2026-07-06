from pathlib import Path

from NetworkDiagnosticPlatform.portable import get_toolkit_root, resolve_config_dir, resolve_output_dir


def test_toolkit_root_defaults_to_repository_root():
    toolkit_root = get_toolkit_root()
    assert toolkit_root.name == "Network diagnosis tool"
    assert (toolkit_root / "src" / "NetworkDiagnosticPlatform").exists()


def test_output_dir_defaults_to_toolkit_reports_folder():
    toolkit_root = get_toolkit_root()
    assert resolve_output_dir(None) == toolkit_root / "reports"


def test_relative_config_dir_is_resolved_from_toolkit_root():
    toolkit_root = get_toolkit_root()
    assert resolve_config_dir("config") == toolkit_root / "config"


def test_absolute_output_dir_is_preserved():
    custom_dir = Path("C:/temp/portable-output")
    assert resolve_output_dir(custom_dir) == custom_dir
