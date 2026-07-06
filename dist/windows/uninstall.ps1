$ErrorActionPreference = "Stop"

Write-Host "Uninstalling Network Diagnostic Platform"
& py -m pip uninstall -y network-diagnostic-platform

if ($LASTEXITCODE -ne 0) {
    throw "pip uninstall failed with exit code $LASTEXITCODE"
}
