from __future__ import annotations

import importlib.util
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """Diagnostic finding with evidence and recommendations."""
    
    title: str
    severity: str  # critical, high, medium, low, info
    explanation: str
    root_cause: str = ""
    evidence: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    learning_articles: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    escalation_criteria: List[str] = field(default_factory=list)


class RuleEngine:
    """Deterministic rule engine for endpoint diagnostic findings."""

    def __init__(self, plugin_paths: Optional[List[str]] = None) -> None:
        """Initialize rule engine with all built-in and optional plugin rules."""
        self.rules: List[Callable[[Dict[str, Any]], Optional[Finding]]] = [
            # Critical connectivity rules
            self._rule_no_dns,
            self._rule_no_gateway,
            self._rule_no_internet,
            self._rule_gateway_unreachable,
            
            # Network configuration rules
            self._rule_no_ip_address,
            self._rule_ipv4_only,
            self._rule_multiple_adapters_down,
            self._rule_unusual_dns_servers,
            
            # Firewall and security
            self._rule_firewall_may_block,
            
            # DNS and name resolution
            self._rule_dns_server_invalid,
            self._rule_dns_cache_may_be_stale,
            
            # Adapter issues
            self._rule_adapter_disabled,
            self._rule_limited_or_no_internet,
        ]
        self.plugin_paths = plugin_paths or []
        self._load_plugin_rules()

    def _load_plugin_rules(self) -> None:
        """Load optional rule modules from plugin directories."""
        for plugin_path in self.plugin_paths:
            path = Path(plugin_path)
            if not path.exists():
                logger.warning(f"Plugin path does not exist: {path}")
                continue

            if path.is_dir():
                for module_file in sorted(path.glob("*.py")):
                    if module_file.name.startswith("__"):
                        continue
                    self._load_plugin_module(module_file)
            elif path.is_file() and path.suffix == ".py":
                self._load_plugin_module(path)

    def _load_plugin_module(self, module_path: Path) -> None:
        """Import a plugin Python module and register its exported rules."""
        try:
            module_name = f"network_diagnostic_plugin_{module_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Unable to load plugin module: {module_path}")
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            plugin_rules = getattr(module, "get_rules", None)
            if callable(plugin_rules):
                loaded_rules = plugin_rules()
                if isinstance(loaded_rules, list):
                    self.rules.extend(loaded_rules)
                    logger.info(f"Loaded {len(loaded_rules)} rules from plugin {module_path}")
                else:
                    self.rules.append(loaded_rules)
                    logger.info(f"Loaded 1 rule from plugin {module_path}")
            else:
                logger.warning(f"Plugin module does not define get_rules(): {module_path}")
        except Exception as exc:
            logger.warning(f"Failed to load plugin module {module_path}: {exc}")

    def analyze(self, evidence: Dict[str, Any]) -> List[Finding]:
        """Analyze evidence and return findings.
        
        Args:
            evidence: Dictionary of system evidence
            
        Returns:
            List of Finding objects
        """
        findings: List[Finding] = []
        for rule in self.rules:
            try:
                finding = rule(evidence)
                if finding is not None:
                    findings.append(finding)
            except Exception as e:
                logger.error(f"Error executing rule {rule.__name__}: {e}")
        
        return findings

    # === CRITICAL CONNECTIVITY RULES ===
    
    def _rule_no_dns(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """DNS resolution failure - cannot resolve hostnames."""
        if evidence.get("dns_resolves") is False:
            return Finding(
                title="DNS Resolution Failure",
                severity="high",
                explanation="The endpoint cannot resolve domain names to IP addresses. This prevents connecting to services by hostname and indicates a DNS configuration or resolver issue.",
                root_cause="DNS servers are unreachable, misconfigured, or not responding. The resolver cache may also be corrupted.",
                evidence=[
                    "DNS resolution test returned false",
                    f"Configured DNS servers: {evidence.get('dns_servers', [])}",
                ],
                recommended_actions=[
                    "Verify DNS server settings: Settings > Network > DNS settings",
                    "Test DNS with: nslookup microsoft.com",
                    "Flush DNS cache: ipconfig /flushdns",
                    "Restart DNS Client service: net stop dnscache && net start dnscache",
                    "Try alternate DNS servers (8.8.8.8, 1.1.1.1)",
                    "Check firewall rules blocking DNS (port 53)",
                ],
                learning_articles=[
                    "DNS Resolution Fundamentals for Windows",
                    "Common DNS Configuration Errors",
                ],
                dependencies=["Internet connectivity", "DNS servers accessible"],
                escalation_criteria=[
                    "Issue persists after service restart",
                    "Multiple DNS servers configured but all fail",
                    "Only internal resources fail to resolve",
                ],
            )
        return None

    def _rule_no_gateway(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """Missing default gateway configuration."""
        if evidence.get("default_gateway") in (None, ""):
            return Finding(
                title="Missing Default Gateway",
                severity="high",
                explanation="No default gateway is configured, which prevents the endpoint from routing traffic beyond the local subnet. The system cannot reach remote networks or the internet.",
                root_cause="Network adapter TCP/IP configuration is incomplete or corrupted. The DHCP server may not be providing gateway information.",
                evidence=[
                    "Default gateway value is empty or missing",
                    f"IP addresses configured: {evidence.get('ip_addresses', [])}",
                ],
                recommended_actions=[
                    "Check DHCP configuration: ipconfig /renew",
                    "Manually configure gateway via Settings > Network settings",
                    "Verify network adapter is configured for DHCP or has static IP with gateway",
                    "Run: netsh int ipv4 show config",
                    "Restart network adapter: ipconfig /release && ipconfig /renew",
                    "Check DHCP server availability on network",
                ],
                learning_articles=[
                    "Default Gateway Configuration in Enterprise Networks",
                    "DHCP vs Static IP Configuration",
                ],
                dependencies=["Network adapter active", "DHCP or static IP configured"],
                escalation_criteria=[
                    "Gateway address cannot be configured",
                    "Gateway visible but not in routing table",
                ],
            )
        return None

    def _rule_no_internet(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """No internet connectivity detected."""
        if evidence.get("internet_reachable") is False:
            return Finding(
                title="No Internet Connectivity",
                severity="high",
                explanation="The endpoint cannot reach external services (tested with 8.8.8.8). This could be caused by firewall policies, routing issues, or upstream network problems.",
                root_cause="Outbound firewall rules may be blocking traffic, default gateway may be unreachable, or ISP/upstream network has issues.",
                evidence=[
                    "Internet reachability test returned false",
                    f"Default gateway reachable: {evidence.get('gateway_reachable', False)}",
                    f"Gateway address: {evidence.get('default_gateway', 'N/A')}",
                ],
                recommended_actions=[
                    "Test gateway connectivity: ping {gateway}",
                    "Check firewall outbound rules via Windows Defender Firewall",
                    "Verify firewall status: netsh advfirewall show allprofiles state",
                    "Test DNS servers: ping 8.8.8.8",
                    "Check proxy settings: netsh winhttp show proxy",
                    "Review network tracing: tracert 8.8.8.8",
                    "Contact network administrator to verify ISP connectivity",
                ],
                learning_articles=[
                    "Internet Connectivity Troubleshooting",
                    "Firewall Outbound Rules",
                    "Network Tracing and Route Analysis",
                ],
                dependencies=["Gateway reachable", "DNS functional", "Firewall configured"],
                escalation_criteria=[
                    "Issue affects multiple endpoints",
                    "Gateway is reachable but internet is not",
                    "Firewall is disabled but still no connectivity",
                ],
            )
        return None

    def _rule_gateway_unreachable(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """Default gateway configured but not reachable."""
        if (evidence.get("default_gateway") not in (None, "") and 
            evidence.get("gateway_reachable") is False):
            return Finding(
                title="Default Gateway Unreachable",
                severity="high",
                explanation="The default gateway is configured but does not respond to ping. The network path to the gateway is broken or the gateway is offline.",
                root_cause="Gateway device is powered off, misconfigured, or there is a layer 2 connectivity issue. The endpoint may be on wrong subnet.",
                evidence=[
                    "Default gateway configured: {evidence.get('default_gateway')}",
                    "Gateway ping test failed",
                ],
                recommended_actions=[
                    "Verify gateway IP is correct: route print",
                    "Check physical network connection and LED indicators",
                    "Try pinging other local devices to isolate issue",
                    "Restart network adapter: Disable/Enable in Device Manager",
                    "Verify MAC address table on switch if available",
                    "Check for static ARP entries: arp -a",
                    "Contact network team to verify gateway availability",
                ],
                learning_articles=[
                    "Layer 2 Connectivity Issues",
                    "Gateway Configuration Best Practices",
                ],
                dependencies=["Network adapter connected", "Gateway online"],
                escalation_criteria=[
                    "Multiple endpoints cannot reach gateway",
                    "Restarting adapter does not resolve issue",
                ],
            )
        return None

    # === NETWORK CONFIGURATION RULES ===
    
    def _rule_no_ip_address(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """No IP address assigned to adapter."""
        if not evidence.get("ip_addresses"):
            return Finding(
                title="No IP Address Assigned",
                severity="high",
                explanation="No IPv4 or IPv6 addresses are configured on network adapters. The endpoint cannot communicate on the network.",
                root_cause="DHCP failed to assign address, static configuration is missing, or network adapter is not properly configured.",
                evidence=[
                    "IP address list is empty",
                    f"Adapter status: {evidence.get('adapter_status', {})}",
                ],
                recommended_actions=[
                    "Restart DHCP client: net stop dhcp && net start dhcp",
                    "Renew IP address: ipconfig /renew",
                    "Check adapter status: ipconfig /all",
                    "Verify adapter driver is installed and enabled",
                    "Manually assign static IP if DHCP unavailable",
                    "Check link lights on network switch port",
                    "Restart network adapter service",
                ],
                learning_articles=[
                    "DHCP Client Troubleshooting",
                    "Static IP Configuration",
                ],
                dependencies=["DHCP server available or static config"],
                escalation_criteria=[
                    "Manual static IP assignment fails",
                    "Multiple adapters have no address",
                ],
            )
        return None

    def _rule_ipv4_only(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """Only IPv4, no IPv6 (may indicate configuration issue)."""
        ips = evidence.get("ip_addresses", [])
        has_ipv4 = any(':' not in ip for ip in ips)
        has_ipv6 = any(':' in ip for ip in ips)
        
        if has_ipv4 and not has_ipv6 and len(ips) == 1:
            return Finding(
                title="IPv6 Not Configured",
                severity="low",
                explanation="Only IPv4 is configured. While IPv4-only is supported, modern enterprise networks typically support both IPv4 and IPv6.",
                root_cause="IPv6 may be disabled or not properly configured on the adapter.",
                evidence=[
                    f"IP addresses: {ips}",
                    "No IPv6 addresses found",
                ],
                recommended_actions=[
                    "Check IPv6 status: netsh int ipv6 show interface",
                    "Enable IPv6 if disabled: netsh int ipv6 set state enabled",
                    "Restart adapter after enabling IPv6",
                    "Verify DHCPv6 is available on network",
                ],
                learning_articles=[
                    "IPv6 in Enterprise Networks",
                    "Dual-stack Configuration",
                ],
                dependencies=["IPv6 infrastructure available"],
                escalation_criteria=["IPv6-only services are required"],
            )
        return None

    def _rule_multiple_adapters_down(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """Multiple adapters show disconnected status."""
        adapters = evidence.get("adapter_status", {})
        disconnected = [a for a, s in adapters.items() if "disconnected" in s.lower()]
        
        if len(disconnected) > 1:
            return Finding(
                title="Multiple Network Adapters Disconnected",
                severity="medium",
                explanation="Multiple network adapters are showing as disconnected. This may indicate hardware issues or driver problems.",
                root_cause="Network interface cards may be failing, drivers need updating, or hardware is not fully seated.",
                evidence=[
                    f"Disconnected adapters: {disconnected}",
                    f"Total adapters: {len(adapters)}",
                ],
                recommended_actions=[
                    "Check Device Manager for adapter warnings",
                    "Update network adapter drivers",
                    "Review event logs for hardware errors",
                    "Test physical connections and cable",
                    "Reseat PCI/PCIe network adapters if applicable",
                ],
                learning_articles=[
                    "Network Adapter Hardware Troubleshooting",
                    "Driver Management",
                ],
                dependencies=["Hardware functional"],
                escalation_criteria=[
                    "All adapters disconnected",
                    "Hardware replacement needed",
                ],
            )
        return None

    def _rule_unusual_dns_servers(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """DNS servers appear to be unusual or suspicious."""
        dns_servers = evidence.get("dns_servers", [])
        
        # Check for unusual DNS servers
        suspicious = []
        for dns in dns_servers:
            if dns.startswith("127.") or dns == "::1":
                suspicious.append(f"{dns} (localhost - misconfigured)")
            elif dns.startswith("169.254."):
                suspicious.append(f"{dns} (APIPA - auto-assigned fallback)")
        
        if suspicious:
            return Finding(
                title="Unusual DNS Server Configuration",
                severity="medium",
                explanation="DNS servers are configured to unusual addresses that may indicate misconfiguration or DHCP failure.",
                root_cause="Localhost DNS configuration, APIPA fallback due to DHCP failure, or manual misconfiguration.",
                evidence=[
                    f"Suspicious DNS entries: {suspicious}",
                    f"All configured DNS: {dns_servers}",
                ],
                recommended_actions=[
                    "Use ipconfig /all to verify DNS configuration",
                    "Reset DNS to standard servers: Set-DnsClientServerAddress",
                    "Renew DHCP if using DHCP: ipconfig /renew",
                    "Configure to public DNS if corporate DNS unavailable: 8.8.8.8, 8.8.4.4",
                    "Contact network administrator for correct DNS servers",
                ],
                learning_articles=[
                    "DNS Server Configuration Best Practices",
                    "APIPA and DHCP Fallback",
                ],
                dependencies=["Correct DNS servers available"],
                escalation_criteria=[
                    "Cannot set correct DNS servers",
                    "Incorrect configuration enforced by GPO",
                ],
            )
        return None

    # === FIREWALL AND SECURITY RULES ===
    
    def _rule_firewall_may_block(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """Firewall is enabled and may be blocking traffic."""
        firewall = evidence.get("firewall_status", "").upper()
        
        if firewall == "ON":
            return Finding(
                title="Windows Firewall Active",
                severity="info",
                explanation="Windows Defender Firewall is enabled. Verify it is not blocking required applications or services.",
                root_cause="Firewall rules may need to be configured for applications.",
                evidence=[
                    "Firewall status: Active",
                ],
                recommended_actions=[
                    "Review firewall profiles: netsh advfirewall show allprofiles",
                    "Check for blocked applications: Windows Defender Firewall > Allow app through firewall",
                    "Create firewall rules for required services as needed",
                    "If testing connectivity, temporarily add rule to allow ping: netsh advfirewall firewall add rule name='Allow ICMP' protocol=icmpv4 dir=in action=allow",
                    "Do not disable firewall; configure rules instead",
                ],
                learning_articles=[
                    "Windows Firewall Rule Management",
                    "Firewall and Network Diagnostics",
                ],
                dependencies=["Firewall accessible for configuration"],
                escalation_criteria=[
                    "Cannot create firewall rules",
                    "Firewall rules not applying as expected",
                ],
            )
        return None

    # === DNS AND NAME RESOLUTION RULES ===
    
    def _rule_dns_server_invalid(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """DNS servers are configured but may be invalid."""
        dns_servers = evidence.get("dns_servers", [])
        
        if not dns_servers:
            return Finding(
                title="No DNS Servers Configured",
                severity="high",
                explanation="No DNS servers are configured, making name resolution impossible.",
                root_cause="DHCP failed to provide DNS servers or they were not configured manually.",
                evidence=[
                    "DNS server list is empty",
                ],
                recommended_actions=[
                    "Renew DHCP to receive DNS servers: ipconfig /renew",
                    "Manually configure DNS servers: Settings > Network > DNS settings",
                    "Use ipconfig /all to verify current configuration",
                    "Contact network administrator for correct DNS servers",
                    "Try temporary DNS servers: 8.8.8.8, 8.8.4.4",
                ],
                learning_articles=[
                    "DNS Configuration and Resolution",
                    "Enterprise DNS Services",
                ],
                dependencies=["DNS servers available on network"],
                escalation_criteria=[
                    "Cannot configure DNS servers",
                    "DNS servers configured but cannot resolve names",
                ],
            )
        return None

    def _rule_dns_cache_may_be_stale(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """DNS cache may be stale if resolution fails intermittently."""
        if evidence.get("dns_resolves") is False:
            return Finding(
                title="DNS Cache Possibly Stale",
                severity="low",
                explanation="If DNS intermittently fails, the resolver cache may contain stale entries or the cache service may be unresponsive.",
                root_cause="DNS Client service cache corruption or service unresponsiveness.",
                evidence=[
                    "DNS resolution test failed",
                ],
                recommended_actions=[
                    "Flush DNS cache: ipconfig /flushdns",
                    "Restart DNS Client service: net stop dnscache && net start dnscache",
                    "Check DNS Client service status: Get-Service dnscache",
                    "Verify cache size hasn't exceeded limits",
                ],
                learning_articles=[
                    "DNS Caching and Performance",
                    "Windows DNS Client Service",
                ],
                dependencies=["DNS Client service accessible"],
                escalation_criteria=[
                    "DNS cache repeatedly becomes corrupted",
                    "DNS Client service crashes frequently",
                ],
            )
        return None

    # === ADAPTER ISSUES ===
    
    def _rule_adapter_disabled(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """Network adapter appears to be disabled."""
        adapters = evidence.get("adapter_status", {})
        disabled = [a for a, s in adapters.items() if "disabled" in s.lower()]
        
        if disabled and evidence.get("ip_addresses"):
            return Finding(
                title="Network Adapter Disabled",
                severity="medium",
                explanation="One or more network adapters show as disabled while others are active. This may indicate intentional configuration or hardware issues.",
                root_cause="Adapter disabled via Device Manager, network settings, or adapter power management.",
                evidence=[
                    f"Disabled adapters: {disabled}",
                ],
                recommended_actions=[
                    "Enable adapter in Device Manager if needed",
                    "Check Power Management settings for adapter",
                    "Verify adapter is not disabled via Settings",
                    "Review Group Policy for adapter restrictions",
                ],
                learning_articles=[
                    "Network Adapter Management",
                    "Device Manager Configuration",
                ],
                dependencies=["Admin privileges"],
                escalation_criteria=[
                    "Cannot enable adapter",
                    "Adapter re-disables automatically",
                ],
            )
        return None

    def _rule_limited_or_no_internet(self, evidence: Dict[str, Any]) -> Optional[Finding]:
        """Endpoint shows limited or no connectivity."""
        if (evidence.get("ip_addresses") and 
            evidence.get("default_gateway") and 
            not evidence.get("internet_reachable")):
            return Finding(
                title="Limited Network Connectivity",
                severity="high",
                explanation="Endpoint has local configuration but cannot reach external resources. This may indicate network isolation or routing issues.",
                root_cause="Firewall rules, routing misconfiguration, or network segmentation preventing internet access.",
                evidence=[
                    "IP address configured",
                    "Gateway configured and reachable",
                    "Internet reachability test failed",
                ],
                recommended_actions=[
                    "Verify firewall rules allow outbound access",
                    "Test connectivity to gateway: ping {gateway}",
                    "Trace route to external host: tracert 8.8.8.8",
                    "Check for network isolation or segmentation policies",
                    "Review proxy settings: netsh winhttp show proxy",
                    "Test with different destination: ping 1.1.1.1",
                ],
                learning_articles=[
                    "Network Segmentation and Isolation",
                    "Routing Troubleshooting",
                ],
                dependencies=["Network infrastructure functional"],
                escalation_criteria=[
                    "Affects multiple endpoints",
                    "Routing table appears corrupted",
                ],
            )
        return None
