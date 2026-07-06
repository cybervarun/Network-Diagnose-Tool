from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
WINDOWS_BUNDLE_DIR = DIST_DIR / "windows"
PORTABLE_BUNDLE_DIR = DIST_DIR / "portable"
PORTABLE_ARCHIVE = DIST_DIR / "network-diagnostic-tool-portable.zip"
REQUIRED_METADATA = [
    "name",
    "version",
    "description",
    "readme",
    "requires-python",
]

INSTALL_SCRIPT = r"""param(
    [string]$InstallScope = "User",
    [switch]$OfflineSmokeTest
)

$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$wheel = Get-ChildItem -Path $bundleRoot -Filter "*.whl" | Select-Object -First 1

if (-not $wheel) {
    throw "No wheel file found beside install.ps1."
}

Write-Host "Installing Network Diagnostic Platform from $($wheel.Name)"

$pipArgs = @("install", "--force-reinstall", $wheel.FullName)
if ($InstallScope -eq "User") {
    $pipArgs = @("install", "--user", "--force-reinstall", $wheel.FullName)
}

& py -m pip @pipArgs
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed with exit code $LASTEXITCODE"
}

Write-Host "Installed console command: network-diagnostic"

if ($OfflineSmokeTest) {
    Write-Host "Running offline smoke test..."
    & network-diagnostic --offline --format json --output ".\smoke-reports"
    if ($LASTEXITCODE -ne 0) {
        throw "offline smoke test failed with exit code $LASTEXITCODE"
    }
}
"""

UNINSTALL_SCRIPT = r"""$ErrorActionPreference = "Stop"

Write-Host "Uninstalling Network Diagnostic Platform"
& py -m pip uninstall -y network-diagnostic-platform

if ($LASTEXITCODE -ne 0) {
    throw "pip uninstall failed with exit code $LASTEXITCODE"
}
"""

BUNDLE_README = """# Network Diagnostic Platform Windows Bundle

This folder contains the wheel and PowerShell helper scripts for installing
Network Diagnostic Platform on Windows endpoints.

## Install

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\install.ps1 -InstallScope User -OfflineSmokeTest
```

Use `-InstallScope Machine` from an elevated PowerShell prompt when the package
should be installed for all users.

## Verify

```powershell
network-diagnostic --release-check
network-diagnostic --offline --format json --output .\\reports
```

## Uninstall

```powershell
.\\uninstall.ps1
```
"""

PORTABLE_LAUNCHER = r"""param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ToolArgs
)

$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcPath = Join-Path $bundleRoot "src"

if (-not (Test-Path $srcPath)) {
    throw "Portable source folder not found: $srcPath"
}

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $pythonCommand = @("py")
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python 3.10 or newer was not found. Use the packaged executable release when Python is unavailable."
    }
    $pythonCommand = @("python")
}

$env:PYTHONPATH = "$srcPath;$env:PYTHONPATH"
if (-not $ToolArgs -or $ToolArgs.Count -eq 0) {
    $ToolArgs = @("--offline", "--output", (Join-Path $bundleRoot "reports"))
}

& $pythonCommand[0] -m NetworkDiagnosticPlatform.cli @ToolArgs
exit $LASTEXITCODE
"""

PORTABLE_CMD = r"""@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Diagnostic.ps1" %*
exit /b %ERRORLEVEL%
"""

PORTABLE_SMOKE_TEST = r"""$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $bundleRoot "Start-Diagnostic.ps1") --offline --format json --output (Join-Path $bundleRoot "smoke-reports")
if ($LASTEXITCODE -ne 0) {
    throw "Portable smoke test failed with exit code $LASTEXITCODE"
}
Write-Host "Portable smoke test completed successfully."
"""

PORTABLE_README = """# Network Diagnostic Tool Portable Bundle

This folder is designed for no-install endpoint use. Carry the folder to a
Windows endpoint, run the launcher, and collect reports without installing the
toolkit on that machine.

## Requirements

- Windows endpoint
- Python 3.10 or newer available as `py` or `python`
- PowerShell for the launcher scripts

## Run A Diagnostic

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\Start-Diagnostic.ps1 --output .\\reports
```

You can also double-click or run:

```cmd
Run-Diagnostic.cmd --offline
```

## Smoke Test

```powershell
.\\Run-Offline-Smoke-Test.ps1
```

## Notes

- No `pip install` is required.
- Reports are written inside this portable folder by default.
- The `docs` folder includes the full toolkit handbook.
- Use the installer bundle only when an endpoint install is explicitly desired.
"""


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a release command from the project root."""
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)


def validate_project_metadata() -> list[str]:
    """Return packaging metadata issues that should block release."""
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
        import tomli as tomllib  # type: ignore[no-redef]

    issues: list[str] = []
    pyproject_path = ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        return ["pyproject.toml is missing"]

    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)

    project = data.get("project", {})
    for field in REQUIRED_METADATA:
        if not project.get(field):
            issues.append(f"project.{field} is missing")

    scripts = project.get("scripts", {})
    if "network-diagnostic" not in scripts:
        issues.append("network-diagnostic console entry point is missing")

    classifiers = project.get("classifiers", [])
    if not any("Microsoft :: Windows" in classifier for classifier in classifiers):
        issues.append("Windows operating system classifier is missing")

    return issues


def validate_artifacts() -> list[str]:
    """Return built artifact issues that should block release."""
    issues: list[str] = []
    wheels = sorted(DIST_DIR.glob("*.whl"))
    sdists = sorted(DIST_DIR.glob("*.tar.gz"))

    if not wheels:
        issues.append("wheel artifact is missing")
    if not sdists:
        issues.append("source distribution artifact is missing")

    for artifact in [*wheels, *sdists]:
        if artifact.stat().st_size == 0:
            issues.append(f"{artifact.name} is empty")

    return issues


def create_windows_bundle() -> Path:
    """Create a Windows install bundle from the latest wheel artifact."""
    wheels = sorted(DIST_DIR.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError("Cannot create Windows bundle because no wheel artifact exists")

    if WINDOWS_BUNDLE_DIR.exists():
        shutil.rmtree(WINDOWS_BUNDLE_DIR)
    WINDOWS_BUNDLE_DIR.mkdir(parents=True)

    wheel = wheels[-1]
    shutil.copy2(wheel, WINDOWS_BUNDLE_DIR / wheel.name)
    (WINDOWS_BUNDLE_DIR / "install.ps1").write_text(INSTALL_SCRIPT, encoding="utf-8")
    (WINDOWS_BUNDLE_DIR / "uninstall.ps1").write_text(UNINSTALL_SCRIPT, encoding="utf-8")
    (WINDOWS_BUNDLE_DIR / "README.md").write_text(BUNDLE_README, encoding="utf-8")

    return WINDOWS_BUNDLE_DIR


def create_portable_bundle() -> Path:
    """Create a no-install portable bundle that runs from source."""
    if PORTABLE_BUNDLE_DIR.exists():
        shutil.rmtree(PORTABLE_BUNDLE_DIR)
    PORTABLE_BUNDLE_DIR.mkdir(parents=True)

    shutil.copytree(
        ROOT / "src",
        PORTABLE_BUNDLE_DIR / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.egg-info"),
    )

    if (ROOT / "config").exists():
        shutil.copytree(ROOT / "config", PORTABLE_BUNDLE_DIR / "config")
    if (ROOT / "docs").exists():
        shutil.copytree(
            ROOT / "docs",
            PORTABLE_BUNDLE_DIR / "docs",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )

    shutil.copy2(ROOT / "README.md", PORTABLE_BUNDLE_DIR / "README-main.md")
    (PORTABLE_BUNDLE_DIR / "README.md").write_text(PORTABLE_README, encoding="utf-8")
    (PORTABLE_BUNDLE_DIR / "Start-Diagnostic.ps1").write_text(PORTABLE_LAUNCHER, encoding="utf-8")
    (PORTABLE_BUNDLE_DIR / "Run-Diagnostic.cmd").write_text(PORTABLE_CMD, encoding="utf-8")
    (PORTABLE_BUNDLE_DIR / "Run-Offline-Smoke-Test.ps1").write_text(PORTABLE_SMOKE_TEST, encoding="utf-8")
    (PORTABLE_BUNDLE_DIR / "reports").mkdir()

    if PORTABLE_ARCHIVE.exists():
        PORTABLE_ARCHIVE.unlink()
    shutil.make_archive(str(PORTABLE_ARCHIVE.with_suffix("")), "zip", PORTABLE_BUNDLE_DIR)

    return PORTABLE_BUNDLE_DIR


def validate_windows_bundle() -> list[str]:
    """Return Windows bundle issues that should block release."""
    issues: list[str] = []
    if not WINDOWS_BUNDLE_DIR.exists():
        return ["Windows distribution bundle is missing"]

    required_files = ["install.ps1", "uninstall.ps1", "README.md"]
    for filename in required_files:
        path = WINDOWS_BUNDLE_DIR / filename
        if not path.exists():
            issues.append(f"Windows bundle file is missing: {filename}")
        elif path.stat().st_size == 0:
            issues.append(f"Windows bundle file is empty: {filename}")

    wheels = sorted(WINDOWS_BUNDLE_DIR.glob("*.whl"))
    if not wheels:
        issues.append("Windows bundle wheel artifact is missing")
    for wheel in wheels:
        if wheel.stat().st_size == 0:
            issues.append(f"Windows bundle wheel is empty: {wheel.name}")

    return issues


def validate_portable_bundle() -> list[str]:
    """Return portable bundle issues that should block release."""
    issues: list[str] = []
    if not PORTABLE_BUNDLE_DIR.exists():
        return ["Portable bundle is missing"]

    required_files = [
        "README.md",
        "README-main.md",
        "Start-Diagnostic.ps1",
        "Run-Diagnostic.cmd",
        "Run-Offline-Smoke-Test.ps1",
        "src/NetworkDiagnosticPlatform/cli.py",
        "src/NetworkDiagnosticPlatform/rule_engine.py",
        "src/NetworkDiagnosticPlatform/knowledge/__init__.py",
    ]
    for filename in required_files:
        path = PORTABLE_BUNDLE_DIR / filename
        if not path.exists():
            issues.append(f"Portable bundle file is missing: {filename}")
        elif path.is_file() and path.stat().st_size == 0:
            issues.append(f"Portable bundle file is empty: {filename}")

    if not (PORTABLE_BUNDLE_DIR / "reports").exists():
        issues.append("Portable reports directory is missing")
    if not PORTABLE_ARCHIVE.exists():
        issues.append("Portable zip archive is missing")
    elif PORTABLE_ARCHIVE.stat().st_size == 0:
        issues.append("Portable zip archive is empty")

    return issues


def print_windows_distribution_notes() -> None:
    """Print release validation commands for Windows distribution."""
    print("\nWindows distribution readiness:")
    print("- Console script: network-diagnostic")
    print(f"- Windows bundle: {WINDOWS_BUNDLE_DIR}")
    print(f"- Portable no-install bundle: {PORTABLE_BUNDLE_DIR}")
    print(f"- Portable zip archive: {PORTABLE_ARCHIVE}")
    print("- Portable run command: powershell -ExecutionPolicy Bypass -File dist\\portable\\Start-Diagnostic.ps1 --offline")
    print("- Bundle install command: powershell -ExecutionPolicy Bypass -File dist\\windows\\install.ps1 -OfflineSmokeTest")
    print("- Offline smoke test: network-diagnostic --offline --format json")
    print("- Clean install test:")
    print(f"  {sys.executable} -m pip install --force-reinstall dist\\*.whl")
    print("- Recommended validation target: clean Windows user profile or disposable VM")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and validate release artifacts.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate metadata and built artifacts after building",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate metadata and existing artifacts without rebuilding",
    )
    parser.add_argument(
        "--windows-bundle",
        action="store_true",
        help="Create a dist/windows PowerShell install bundle",
    )
    parser.add_argument(
        "--portable-bundle",
        action="store_true",
        help="Create a no-install dist/portable bundle and zip archive",
    )
    args = parser.parse_args(argv)

    metadata_issues = validate_project_metadata()
    if metadata_issues:
        print("Packaging metadata issues:")
        for issue in metadata_issues:
            print(f"- {issue}")
        return 1

    if args.check_only:
        artifact_issues = validate_artifacts()
        bundle_issues = validate_windows_bundle()
        portable_issues = validate_portable_bundle()
        issues = [*artifact_issues, *bundle_issues, *portable_issues]
        if issues:
            print("Artifact issues:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("Release artifacts are present and non-empty.")
        print_windows_distribution_notes()
        return 0

    for path in (DIST_DIR, BUILD_DIR):
        if path.exists():
            shutil.rmtree(path)

    cmd = [sys.executable, "-m", "build"]
    result = run_command(cmd)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        return result.returncode

    print(f"Build artifacts created in {DIST_DIR}")
    if args.windows_bundle or args.check:
        bundle_dir = create_windows_bundle()
        print(f"Windows install bundle created in {bundle_dir}")
    if args.portable_bundle or args.check:
        portable_dir = create_portable_bundle()
        print(f"Portable no-install bundle created in {portable_dir}")
    print_windows_distribution_notes()

    if args.check:
        issues = [*validate_artifacts(), *validate_windows_bundle(), *validate_portable_bundle()]
        if issues:
            print("\nArtifact issues:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("\nRelease checks passed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
