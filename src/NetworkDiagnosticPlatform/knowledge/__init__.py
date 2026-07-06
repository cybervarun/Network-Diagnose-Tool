"""Offline troubleshooting knowledge base for diagnostic guidance."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class KnowledgeArticle:
    """Structured troubleshooting article bundled with the package."""

    id: str
    title: str
    summary: str
    category: str
    severity: str
    symptoms: List[str] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)
    fixes: List[str] = field(default_factory=list)
    escalation: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    related_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable article representation."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "severity": self.severity,
            "symptoms": list(self.symptoms),
            "checks": list(self.checks),
            "fixes": list(self.fixes),
            "escalation": list(self.escalation),
            "keywords": list(self.keywords),
            "related_rules": list(self.related_rules),
        }


class KnowledgeBase:
    """Simple in-repo knowledge base for troubleshooting articles."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or Path(__file__).resolve().parent)
        self.articles: Dict[str, KnowledgeArticle] = self._load_builtin_articles()

    def _load_builtin_articles(self) -> Dict[str, KnowledgeArticle]:
        """Load bundled troubleshooting articles."""
        articles = [
            KnowledgeArticle(
                id="dns_resolution",
                title="DNS Resolution Fundamentals",
                summary="Understand how DNS failures affect name resolution and how to test them.",
                category="Name Resolution",
                severity="high",
                symptoms=[
                    "Websites fail by hostname but work by IP address",
                    "nslookup returns timeouts or server failure responses",
                    "Internal application names intermittently fail",
                ],
                checks=[
                    "Run nslookup microsoft.com and compare against a known-good endpoint",
                    "Run ipconfig /all and verify each adapter has expected DNS servers",
                    "Confirm UDP and TCP port 53 are allowed to the configured resolver",
                ],
                fixes=[
                    "Flush the resolver cache with ipconfig /flushdns",
                    "Renew adapter configuration with ipconfig /renew when DNS comes from DHCP",
                    "Temporarily test with approved alternate DNS servers",
                ],
                escalation=[
                    "All configured DNS servers fail from multiple endpoints",
                    "Only internal zones fail or return stale records",
                ],
                keywords=["dns", "resolution", "nslookup", "resolver", "hostname"],
                related_rules=["dns_resolution_failure", "dns_cache_may_be_stale"],
            ),
            KnowledgeArticle(
                id="gateway_configuration",
                title="Default Gateway Configuration",
                summary="Review gateway setup, DHCP behavior, and routing basics.",
                category="Routing",
                severity="high",
                symptoms=[
                    "Local subnet resources work but remote networks fail",
                    "route print does not show a usable default route",
                    "The adapter has an IP address but no default gateway",
                ],
                checks=[
                    "Run ipconfig /all and confirm gateway, subnet mask, and DHCP source",
                    "Run route print and inspect the 0.0.0.0/0 or ::/0 route",
                    "Ping the gateway address from the affected endpoint",
                ],
                fixes=[
                    "Renew DHCP configuration with ipconfig /release and ipconfig /renew",
                    "Correct static IP, subnet mask, and gateway settings together",
                    "Restart or re-enable the affected network adapter",
                ],
                escalation=[
                    "The gateway is configured correctly but unreachable from several endpoints",
                    "The route table is rewritten by policy or VPN software",
                ],
                keywords=["gateway", "routing", "dhcp", "route", "subnet"],
                related_rules=["missing_gateway", "gateway_unreachable"],
            ),
            KnowledgeArticle(
                id="firewall_troubleshooting",
                title="Firewall and Network Diagnostics",
                summary="Check outbound rules and profile state when connectivity appears blocked.",
                category="Security Controls",
                severity="medium",
                symptoms=[
                    "Connectivity works for some applications but not others",
                    "Ping, browser, or line-of-business traffic is blocked unexpectedly",
                    "The active firewall profile changed after network roaming",
                ],
                checks=[
                    "Run netsh advfirewall show allprofiles state",
                    "Review inbound and outbound rules for the affected application or port",
                    "Confirm the network profile is Domain, Private, or Public as expected",
                ],
                fixes=[
                    "Create the narrowest required allow rule for the application or port",
                    "Correct the network profile when Windows selected the wrong profile",
                    "Avoid disabling the firewall as a permanent fix",
                ],
                escalation=[
                    "Rules are enforced by Group Policy and conflict with business needs",
                    "Expected rules are present but packet captures still show blocked traffic",
                ],
                keywords=["firewall", "outbound", "inbound", "rules", "profile"],
                related_rules=["firewall_active", "no_internet"],
            ),
            KnowledgeArticle(
                id="dhcp_apipa",
                title="DHCP Failure and APIPA Addressing",
                summary="Identify automatic 169.254.x.x addressing and restore DHCP lease assignment.",
                category="Address Assignment",
                severity="high",
                symptoms=[
                    "Endpoint receives a 169.254.x.x address",
                    "No DHCP server appears in ipconfig /all output",
                    "Connectivity is limited to link-local peers",
                ],
                checks=[
                    "Run ipconfig /all and look for Autoconfiguration IPv4 Address",
                    "Run ipconfig /renew and capture any DHCP timeout message",
                    "Check switch port, VLAN assignment, and DHCP relay configuration",
                ],
                fixes=[
                    "Reconnect the cable or Wi-Fi network and renew the lease",
                    "Correct VLAN or DHCP scope assignment",
                    "Assign a temporary static address only for controlled recovery",
                ],
                escalation=[
                    "Multiple endpoints on the same VLAN receive APIPA addresses",
                    "DHCP relay or scope exhaustion is suspected",
                ],
                keywords=["dhcp", "apipa", "169.254", "lease", "scope", "autoconfiguration"],
                related_rules=["no_ip_address", "unusual_dns_servers"],
            ),
            KnowledgeArticle(
                id="proxy_vpn_interference",
                title="Proxy and VPN Interference",
                summary="Diagnose proxy, split tunnel, and VPN client behavior that changes network paths.",
                category="Policy and Remote Access",
                severity="medium",
                symptoms=[
                    "Internet works off VPN but fails after connecting",
                    "Only browser traffic works because a proxy is configured",
                    "Corporate resources work while public endpoints fail",
                ],
                checks=[
                    "Run netsh winhttp show proxy",
                    "Compare route print before and after VPN connection",
                    "Review PAC file, browser proxy, and VPN split-tunnel policy",
                ],
                fixes=[
                    "Reset WinHTTP proxy when it is stale: netsh winhttp reset proxy",
                    "Reconnect the VPN client after refreshing network credentials",
                    "Ask the VPN owner to correct split-tunnel or DNS suffix policy",
                ],
                escalation=[
                    "Routes or proxy settings are managed by endpoint policy",
                    "Only users in a specific VPN group are affected",
                ],
                keywords=["proxy", "vpn", "winhttp", "split tunnel", "pac", "route"],
                related_rules=["no_internet", "limited_network_connectivity"],
            ),
            KnowledgeArticle(
                id="adapter_driver_power",
                title="Adapter Driver and Power Management",
                summary="Resolve disabled, disconnected, or power-managed network adapters.",
                category="Adapter Health",
                severity="medium",
                symptoms=[
                    "Device Manager shows warning icons on network adapters",
                    "Connectivity drops after sleep or docking changes",
                    "Multiple adapters report disabled or disconnected states",
                ],
                checks=[
                    "Check Device Manager for adapter status and driver date",
                    "Review System event logs for NDIS or driver reset events",
                    "Inspect adapter Power Management settings",
                ],
                fixes=[
                    "Install the approved OEM or enterprise network driver",
                    "Disable power saving for critical wired adapters",
                    "Re-enable the adapter and test after a reboot",
                ],
                escalation=[
                    "The adapter repeatedly disables itself after driver refresh",
                    "Hardware errors appear in the System event log",
                ],
                keywords=["adapter", "driver", "power", "disabled", "device manager", "ndis"],
                related_rules=["adapter_disabled", "multiple_adapters_down"],
            ),
        ]
        return {article.id: article for article in articles}

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Return matching articles for a search query."""
        query = query.strip().lower()
        if not query:
            return []

        matches: List[Dict[str, Any]] = []
        for article in self.articles.values():
            haystack = " ".join(
                [
                    article.id,
                    article.title,
                    article.summary,
                    article.category,
                    *article.symptoms,
                    *article.checks,
                    *article.fixes,
                    *article.keywords,
                    *article.related_rules,
                ]
            ).lower()
            if query in haystack:
                matches.append(article.to_dict())
        return matches

    def get(self, article_id: str) -> Dict[str, Any] | None:
        """Return a specific article by id."""
        article = self.articles.get(article_id)
        return article.to_dict() if article else None

    def list_articles(self) -> List[Dict[str, Any]]:
        """Return all articles ordered by category and title."""
        return [
            article.to_dict()
            for article in sorted(self.articles.values(), key=lambda item: (item.category, item.title))
        ]

    def categories(self) -> List[str]:
        """Return available article categories."""
        return sorted({article.category for article in self.articles.values()})
