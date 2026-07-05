"""Evidence collection layer for Windows endpoint diagnostics."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvidenceSnapshot:
    """Captured evidence from endpoint diagnostics."""
    
    timestamp: str
    hostname: str
    os_version: str
    dns_servers: list[str]
    dns_resolves: bool
    default_gateway: Optional[str]
    ip_addresses: list[str]
    gateway_reachable: bool
    internet_reachable: bool
    firewall_status: str
    adapter_status: Dict[str, str]
    ipconfig_output: str
    route_output: str
    nslookup_output: str
    ping_gateway_output: str
    ping_internet_output: str
    netstat_output: str
    tracert_output: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rule engine analysis."""
        return asdict(self)


class WindowsEvidenceCollector:
    """Collects diagnostic evidence from Windows endpoint."""
    
    def __init__(self, offline_mode: bool = False) -> None:
        """Initialize collector.
        
        Args:
            offline_mode: If True, returns mock data for testing
        """
        self.offline_mode = offline_mode
        self.collected_evidence: Optional[EvidenceSnapshot] = None
    
    def collect_all(self) -> EvidenceSnapshot:
        """Collect all available diagnostic evidence.
        
        Returns:
            EvidenceSnapshot: Captured endpoint state
        """
        if self.offline_mode:
            snapshot = self._create_mock_evidence()
            self.collected_evidence = snapshot
            return snapshot
        
        try:
            logger.info("Starting evidence collection...")
            
            snapshot = EvidenceSnapshot(
                timestamp=datetime.now().isoformat(),
                hostname=self._get_hostname(),
                os_version=self._get_os_version(),
                dns_servers=self._get_dns_servers(),
                dns_resolves=self._test_dns_resolution(),
                default_gateway=self._get_default_gateway(),
                ip_addresses=self._get_ip_addresses(),
                gateway_reachable=self._test_gateway_reachability(),
                internet_reachable=self._test_internet_connectivity(),
                firewall_status=self._get_firewall_status(),
                adapter_status=self._get_adapter_status(),
                ipconfig_output=self._run_command("ipconfig /all"),
                route_output=self._run_command("route print"),
                nslookup_output=self._run_command("nslookup google.com"),
                ping_gateway_output=self._run_command(f"ping {self._get_default_gateway()} -n 1", timeout=5),
                ping_internet_output=self._run_command("ping 8.8.8.8 -n 1", timeout=5),
                netstat_output=self._run_command("netstat -an"),
                tracert_output=self._run_command("tracert -w 1000 8.8.8.8", timeout=10),
            )
            
            self.collected_evidence = snapshot
            logger.info("Evidence collection completed successfully")
            return snapshot
            
        except Exception as e:
            logger.error(f"Evidence collection failed: {e}")
            raise
    
    def _run_command(self, command: str, timeout: int = 30) -> str:
        """Run Windows command and capture output.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Command output or error message
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout if result.stdout else result.stderr
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timeout: {command}")
            return f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Command execution failed: {command} - {e}")
            return f"Error executing command: {e}"
    
    def _get_hostname(self) -> str:
        """Get endpoint hostname."""
        try:
            return subprocess.run(
                "hostname",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
        except Exception as e:
            logger.warning(f"Failed to get hostname: {e}")
            return "unknown"
    
    def _get_os_version(self) -> str:
        """Get Windows OS version."""
        try:
            result = subprocess.run(
                "systeminfo",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout
            for line in result.split('\n'):
                if 'OS Version' in line:
                    return line.split(':')[1].strip()
            return "unknown"
        except Exception as e:
            logger.warning(f"Failed to get OS version: {e}")
            return "unknown"
    
    def _get_dns_servers(self) -> list[str]:
        """Get configured DNS servers."""
        try:
            output = self._run_command("ipconfig /all")
            dns_servers = []
            for line in output.split('\n'):
                if 'DNS Server' in line:
                    server = line.split(':')[1].strip()
                    if server and server not in dns_servers:
                        dns_servers.append(server)
            return dns_servers
        except Exception as e:
            logger.warning(f"Failed to get DNS servers: {e}")
            return []
    
    def _test_dns_resolution(self) -> bool:
        """Test if DNS resolution works."""
        try:
            result = subprocess.run(
                "nslookup microsoft.com",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Successful if no timeout and contains address
            return "Address:" in result.stdout and "**" not in result.stdout
        except Exception as e:
            logger.warning(f"DNS resolution test failed: {e}")
            return False
    
    def _get_default_gateway(self) -> Optional[str]:
        """Get default gateway IP address."""
        try:
            result = subprocess.run(
                "route print",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout
            
            for line in result.split('\n'):
                if '0.0.0.0' in line and '0.0.0.0' not in line.split()[0]:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if '.' in part and i < len(parts) - 2:
                            return part
            return None
        except Exception as e:
            logger.warning(f"Failed to get default gateway: {e}")
            return None
    
    def _get_ip_addresses(self) -> list[str]:
        """Get all active IP addresses."""
        try:
            output = self._run_command("ipconfig")
            ips = []
            for line in output.split('\n'):
                if 'IPv4 Address' in line or 'IP Address' in line:
                    ip = line.split(':')[1].strip()
                    if ip and ip not in ips:
                        ips.append(ip)
            return ips
        except Exception as e:
            logger.warning(f"Failed to get IP addresses: {e}")
            return []
    
    def _test_gateway_reachability(self) -> bool:
        """Test if default gateway is reachable."""
        gateway = self._get_default_gateway()
        if not gateway:
            return False
        
        try:
            result = subprocess.run(
                f"ping {gateway} -n 1",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Gateway reachability test failed: {e}")
            return False
    
    def _test_internet_connectivity(self) -> bool:
        """Test internet connectivity."""
        try:
            result = subprocess.run(
                "ping 8.8.8.8 -n 1",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Internet connectivity test failed: {e}")
            return False
    
    def _get_firewall_status(self) -> str:
        """Get Windows Defender Firewall status."""
        try:
            result = subprocess.run(
                "netsh advfirewall show allprofiles state",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout
            
            if "State" in result:
                for line in result.split('\n'):
                    if "State" in line:
                        return line.split('State')[1].strip()
            return "unknown"
        except Exception as e:
            logger.warning(f"Failed to get firewall status: {e}")
            return "unknown"
    
    def _get_adapter_status(self) -> Dict[str, str]:
        """Get status of network adapters."""
        try:
            output = self._run_command("ipconfig /all")
            adapters = {}
            current_adapter = ""
            
            for line in output.split('\n'):
                if 'adapter' in line.lower() and ':' in line:
                    current_adapter = line.split(':')[0].strip()
                elif 'Media State' in line and current_adapter:
                    status = line.split(':')[1].strip()
                    adapters[current_adapter] = status
            
            return adapters
        except Exception as e:
            logger.warning(f"Failed to get adapter status: {e}")
            return {}
    
    def _create_mock_evidence(self) -> EvidenceSnapshot:
        """Create mock evidence for testing."""
        return EvidenceSnapshot(
            timestamp=datetime.now().isoformat(),
            hostname="test-pc",
            os_version="Windows 10 Pro (Build 19045)",
            dns_servers=["8.8.8.8", "8.8.4.4"],
            dns_resolves=True,
            default_gateway="192.168.1.1",
            ip_addresses=["192.168.1.100"],
            gateway_reachable=True,
            internet_reachable=True,
            firewall_status="ON",
            adapter_status={"Ethernet": "Media connected"},
            ipconfig_output="Mock ipconfig output",
            route_output="Mock route output",
            nslookup_output="Mock nslookup output",
            ping_gateway_output="Reply from 192.168.1.1",
            ping_internet_output="Reply from 8.8.8.8",
            netstat_output="Mock netstat output",
            tracert_output="Mock tracert output",
        )
    
    def export_evidence(self, filepath: str) -> None:
        """Export collected evidence to JSON file.
        
        Args:
            filepath: Path to save evidence JSON
        """
        if not self.collected_evidence:
            logger.error("No evidence collected yet")
            return
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.collected_evidence.to_dict(), f, indent=2)
            logger.info(f"Evidence exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export evidence: {e}")
