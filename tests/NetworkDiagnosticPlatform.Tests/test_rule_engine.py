from NetworkDiagnosticPlatform.rule_engine import RuleEngine


def test_detects_dns_failure():
    engine = RuleEngine()
    findings = engine.analyze({"dns_resolves": False, "default_gateway": "192.168.1.1", "internet_reachable": True})

    assert any(f.title == "DNS Resolution Failure" for f in findings)


def test_detects_missing_gateway():
    engine = RuleEngine()
    findings = engine.analyze({"dns_resolves": True, "default_gateway": None, "internet_reachable": False})

    assert any(f.title == "Missing Default Gateway" for f in findings)


def test_detects_no_internet():
    engine = RuleEngine()
    findings = engine.analyze({"dns_resolves": True, "default_gateway": "192.168.1.1", "internet_reachable": False, "gateway_reachable": True})

    assert any(f.title == "No Internet Connectivity" for f in findings)

