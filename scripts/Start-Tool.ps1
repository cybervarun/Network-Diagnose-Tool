param(
    [switch]$Offline,
    [string]$OutputDir = ".\reports",
    [switch]$ReleaseCheck,
    [switch]$KnowledgeList,
    [switch]$KnowledgeSearch,
    [string]$KnowledgeQuery,
    [switch]$KnowledgeDetail,
    [string[]]$PluginPath,
    [switch]$Help
)

function Show-Help {
    Write-Host @"
Network Diagnostic Toolkit - Portable Edition
-------------------------------------------

Usage:
  .\Start-Tool.ps1 [-Offline] [-o <OutputDir>] [options]

Options:
  -Offline                 Run in offline mode (uses mock data)
  -o <OutputDir>           Directory for reports (default: .\reports)
  -ReleaseCheck            Show release-readiness summary
  -KnowledgeList           List bundled troubleshooting articles
  -KnowledgeSearch <Query> Search offline guidance
  -KnowledgeDetail <ID>    Show detailed article
  -PluginPath <Path>...    Additional plugin directories
  -Help                    Show this help

Examples:
  .\Start-Tool.ps1 -Offline
  .\Start-Tool.ps1 -o "C:\Temp\Reports"
  .\Start-Tool.ps1 -KnowledgeSearch dns
  .\Start-Tool.ps1 -ReleaseCheck
"@
    exit 0
}

# Parse arguments manually since Get-Help isn't used
$args | ForEach-Object {
    switch ($_) {
        "-Offline"          { $Offline = $true }
        "-o"                { $OutputDir = $args[$args.IndexOf($_) + 1] }
        "-OutputDir"        { $OutputDir = $args[$args.IndexOf($_) + 1] }
        "-ReleaseCheck"     { $ReleaseCheck = $true }
        "-KnowledgeList"    { $KnowledgeList = $true }
        "-KnowledgeSearch"  { $KnowledgeSearch = $true }
        "-KnowledgeQuery"   { $KnowledgeQuery = $args[$args.IndexOf($_) + 1] }
        "-KnowledgeDetail"  { $KnowledgeDetail = $args[$args.IndexOf($_) + 1] }
        "-PluginPath"       { $PluginPath += @($args[$args.IndexOf($_) + 1]) }
        "-Help"             { Show-Help }
        default {
            Write-Error "Unknown parameter: $_"
            Show-Help
        }
    }
}

# Resolve the toolkit root (directory where this script resides)
$ToolkitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ToolkitRoot

# Add the portable Python path
$PythonPath = [System.Environment]::GetEnvironmentVariable("PYTHONPATH", [System.EnvironmentVariableTarget]::Process)
if (-not $PythonPath) { $PythonPath = "" }
if (-not ($PythonPath -split ';' | Where-Object { $_ -eq $ToolkitRoot })) {
    $PythonPath += if ($PythonPath) { ";$ToolkitRoot" } else { $ToolkitRoot }
    [System.Environment]::SetEnvironmentVariable("PYTHONPATH", $PythonPath, [System.EnvironmentVariableTarget]::Process)
}

# Import the CLI module and delegate to it
try {
    $CliModulePath = Join-Path $ToolkitRoot "src\NetworkDiagnosticPlatform\cli.py"
    if (-not (Test-Path $CliModulePath)) {
        Write-Error "CLI module not found at $CliModulePath"
        exit 1
    }

    # Use PowerShell's Add-Type to load the CLI assembly (requires Python for edge cases)
    # Instead, directly invoke Python with the CLI entry point
    $PythonExe = (Get-Command python).Source
    if (-not $PythonExe) {
        Write-Error "Python executable not found in PATH"
        exit 1
    }

    $ArgsList = @()
    $ArgsList += "-m"
    $ArgsList += "NetworkDiagnosticPlatform.cli"
    if ($Offline) { $ArgsList += "--offline" }
    if ($ReleaseCheck) { $ArgsList += "--release-check" }
    if ($KnowledgeList) { $ArgsList += "--knowledge-list" }
    if ($KnowledgeSearch) { $ArgsList += "--knowledge-search"; $ArgsList += $KnowledgeQuery }
    if ($KnowledgeDetail) { $ArgsList += "--knowledge-detail"; $ArgsList += $KnowledgeDetail }
    if ($PluginPath) { $ArgsList += "--plugin-path"; $ArgsList += $PluginPath }
    if ($Help) { Show-Help }

    # Append output directory if specified
    if ($OutputDir) { $ArgsList += "-o"; $ArgsList += $OutputDir }

    # Execute Python with the CLI
    $Result = & $PythonExe @ArgsList
    exit $LASTEXITCODE
}
catch {
    Write-Error "Failed to execute CLI: $_"
    exit 1
}