from pathlib import Path

from scripts.build_package import (
    ROOT,
    create_windows_bundle,
    validate_artifacts,
    validate_project_metadata,
    validate_windows_bundle,
)


def test_build_script_points_to_project_root():
    assert ROOT.name == "Network diagnosis tool"
    assert (ROOT / "pyproject.toml").exists()


def test_project_metadata_is_release_ready():
    assert validate_project_metadata() == []


def test_artifact_validation_detects_missing_dist(monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.build_package.DIST_DIR", tmp_path / "dist")

    issues = validate_artifacts()

    assert "wheel artifact is missing" in issues
    assert "source distribution artifact is missing" in issues


def test_windows_bundle_validation_detects_missing_bundle(monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.build_package.WINDOWS_BUNDLE_DIR", tmp_path / "windows")

    assert validate_windows_bundle() == ["Windows distribution bundle is missing"]


def test_create_windows_bundle_copies_wheel_and_helpers(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    bundle_dir = dist_dir / "windows"
    dist_dir.mkdir()
    (dist_dir / "network_diagnostic_platform-0.1.0-py3-none-any.whl").write_text("wheel", encoding="utf-8")

    monkeypatch.setattr("scripts.build_package.DIST_DIR", dist_dir)
    monkeypatch.setattr("scripts.build_package.WINDOWS_BUNDLE_DIR", bundle_dir)

    created = create_windows_bundle()

    assert created == bundle_dir
    assert (bundle_dir / "network_diagnostic_platform-0.1.0-py3-none-any.whl").exists()
    assert "OfflineSmokeTest" in (bundle_dir / "install.ps1").read_text(encoding="utf-8")
    assert "pip uninstall" in (bundle_dir / "uninstall.ps1").read_text(encoding="utf-8")
    assert validate_windows_bundle() == []
