# Network Diagnostic Platform Windows Bundle

This folder contains the wheel and PowerShell helper scripts for installing
Network Diagnostic Platform on Windows endpoints.

## Install

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1 -InstallScope User -OfflineSmokeTest
```

Use `-InstallScope Machine` from an elevated PowerShell prompt when the package
should be installed for all users.

## Verify

```powershell
network-diagnostic --release-check
network-diagnostic --offline --format json --output .\reports
```

## Uninstall

```powershell
.\uninstall.ps1
```
