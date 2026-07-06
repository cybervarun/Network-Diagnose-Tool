param(
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
