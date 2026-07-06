# Network Diagnostic Tool Handbook

**Purpose:** a plain-language reference for the full toolkit, written for both technical and non-technical readers.

## What This Toolkit Is

The Network Diagnostic Tool is an offline-first Windows troubleshooting toolkit. It collects endpoint evidence, evaluates that evidence with deterministic rules, explains likely causes, and produces human-readable reports that support help desk, desktop support, and engineering workflows.

It is designed to answer four practical questions:

1. What is broken?
1. Why does it look that way?
1. What should we try next?
1. When should the issue be escalated?

## Who Uses It

This toolkit is useful for:

- Support staff who need a quick, repeatable diagnosis
- Engineers who want evidence instead of guesswork
- Non-technical operators who need a readable summary of what happened
- Maintainers who need to understand how the package, CLI, tests, and release workflow fit together

## Current State

As of July 7, 2026, the toolkit has:

- A working Windows-oriented evidence collector
- A deterministic rule engine with 13 built-in diagnostic rules
- A bundled offline knowledge base with troubleshooting guidance
- Text, HTML, and JSON report generation
- A command-line interface with diagnostic and release commands
- A Windows distribution bundle under `dist/windows`
- A passing automated test suite with 57 tests

The package version is `0.1.0`.

## How The Toolkit Works

The system follows a simple flow:

1. Collect evidence from the endpoint
1. Run rules against that evidence
1. Turn the findings into reports
1. Offer guidance through the knowledge base and CLI

This keeps the behavior predictable. The tool does not rely on AI for diagnosis, so the same evidence should lead to the same result every time.

## Main Components

### Evidence Collection

File: [evidence_collector.py](../src/NetworkDiagnosticPlatform/evidence_collector.py)

This component gathers diagnostic data from Windows using built-in commands and system information. It is also able to run in offline mode with mock data, which lets the test suite and development workflow remain safe and repeatable.

It captures details such as:

- Hostname
- IP addresses
- Default gateway
- DNS servers
- Firewall state
- Adapter status
- Route and reachability information

### Rule Engine

File: [rule_engine.py](../src/NetworkDiagnosticPlatform/rule_engine.py)

The rule engine examines collected evidence and creates findings. Each finding includes:

- A title
- Severity
- Explanation
- Root cause
- Supporting evidence
- Recommended actions
- Learning articles
- Dependencies
- Escalation criteria

The current rule set covers common Windows endpoint problems such as:

- DNS resolution failure
- Missing default gateway
- No internet connectivity
- Gateway unreachable
- No IP address assigned
- IPv4-only configuration
- Multiple disconnected adapters
- Unusual DNS servers
- Windows Firewall active
- No DNS servers configured
- Stale DNS cache
- Disabled adapter
- Limited network connectivity

### Reporting

File: [reporting.py](../src/NetworkDiagnosticPlatform/reporting.py)

Reports are available in three formats:

- Text: readable in the console or in a ticket
- HTML: suitable for sharing or opening in a browser
- JSON: suitable for automation or downstream tooling

Each report includes the findings, evidence, recommended actions, and escalation cues.

### Knowledge Base

File: [knowledge/__init__.py](../src/NetworkDiagnosticPlatform/knowledge/__init__.py)

The bundled knowledge base gives short troubleshooting articles that can be searched from the CLI. It is intentionally offline and local to the repo, so the guidance is available even without network access.

The current article set covers:

- DNS resolution
- Default gateway configuration
- Firewall diagnostics
- DHCP failure and APIPA addressing
- Proxy and VPN interference
- Adapter driver and power management

### Command-Line Interface

File: [cli.py](../src/NetworkDiagnosticPlatform/cli.py)

The CLI is the entry point for most users. It can:

- Run a full diagnostic
- List rules
- Show rule details
- Search the knowledge base
- Show a knowledge article
- Check release readiness

It also supports offline mode and plugin paths for custom rules.

### Packaging And Release Workflow

File: [scripts/build_package.py](../scripts/build_package.py)

The build workflow does more than make a wheel and sdist. It also validates packaging metadata and creates a Windows distribution bundle containing:

- The wheel file
- `install.ps1`
- `uninstall.ps1`
- A bundle README

That makes the release easier to hand to another person without asking them to figure out the repo layout first.

## How To Use It

### Development Setup

```bash
pip install -e ".[dev]"
pytest
```

### Run A Diagnostic

```bash
network-diagnostic --offline
network-diagnostic -o "./reports"
network-diagnostic -f "html,json"
```

### Explore Rules

```bash
network-diagnostic --list-rules
network-diagnostic --rule-details dns
```

### Search The Knowledge Base

```bash
network-diagnostic --knowledge-list
network-diagnostic --knowledge-search gateway
network-diagnostic --knowledge-detail dhcp_apipa
```

### Check Release Readiness

```bash
network-diagnostic --release-check
python scripts/build_package.py --check --windows-bundle
```

### Install The Windows Bundle

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\dist\windows\install.ps1 -OfflineSmokeTest
```

## What The Output Means

### Severity Levels

- `critical`: immediate action needed
- `high`: serious problem, likely blocking core connectivity
- `medium`: important issue that should be addressed soon
- `low`: informational or lower urgency
- `info`: useful context, not necessarily a defect

### Finding Fields

- `explanation` tells you what the tool observed
- `root_cause` tells you the likely reason
- `evidence` shows why the tool reached that conclusion
- `recommended_actions` suggests concrete next steps
- `learning_articles` points to the bundled guidance
- `escalation_criteria` explains when to hand the issue off

## How To Maintain It

When updating the toolkit, use this order of thinking:

1. Change the behavior
1. Add or update tests
1. Update the knowledge base if the user-facing explanation changed
1. Update packaging or release scripts if the distribution flow changed
1. Update the handbook and README so the next person sees the same story

### If You Add A New Diagnostic Rule

- Add the rule in [rule_engine.py](../src/NetworkDiagnosticPlatform/rule_engine.py)
- Add a focused test in `tests/NetworkDiagnosticPlatform.Tests/`
- Add or update a knowledge article if users need guidance
- Make sure the CLI output still reads clearly

### If You Add A New Knowledge Article

- Keep the language short and specific
- Include common symptoms, checks, fixes, and escalation criteria
- Link the article to the rules it helps explain
- Keep the article useful even if the reader has no deep Windows background

### If You Change Packaging

- Update [pyproject.toml](../pyproject.toml)
- Update [scripts/build_package.py](../scripts/build_package.py)
- Verify the Windows bundle still creates cleanly
- Keep `dist/windows` easy to hand off to another person

## Operational Notes

- The toolkit is Windows-focused
- Offline mode is important for testing and for isolated environments
- The tool is read-only from a troubleshooting perspective; it gathers evidence and suggests actions, but it does not auto-remediate
- Report generation is designed to be quick and predictable
- Packaging should remain simple enough for a support engineer to explain in one sentence

## Files To Read First

If someone is new to the project, the best order is:

1. [README.md](../README.md)
1. [cli.py](../src/NetworkDiagnosticPlatform/cli.py)
1. [rule_engine.py](../src/NetworkDiagnosticPlatform/rule_engine.py)
1. [knowledge/__init__.py](../src/NetworkDiagnosticPlatform/knowledge/__init__.py)
1. [scripts/build_package.py](../scripts/build_package.py)
1. [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)

## Short Glossary

- Evidence: the facts collected from the endpoint
- Finding: a rule-based diagnosis generated from evidence
- Bundle: the Windows install folder under `dist/windows`
- Offline mode: mock data mode for safe testing
- Escalation: the point where the issue should be handed to another team

## Summary

The toolkit is now more than a working diagnostic engine. It is a small releaseable system with evidence collection, diagnosis, reporting, knowledge, and a Windows distribution path. That makes it suitable for support use today and much easier to extend later without losing the original intent.
