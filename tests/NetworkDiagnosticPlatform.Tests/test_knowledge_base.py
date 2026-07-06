from NetworkDiagnosticPlatform.knowledge import KnowledgeBase


def test_knowledge_base_search_returns_relevant_articles():
    kb = KnowledgeBase()
    results = kb.search("firewall")

    assert results
    assert any(result["id"] == "firewall_troubleshooting" for result in results)


def test_knowledge_base_includes_phase_three_articles():
    kb = KnowledgeBase()

    assert len(kb.articles) >= 6
    assert kb.get("dhcp_apipa")["category"] == "Address Assignment"
    assert "Policy and Remote Access" in kb.categories()


def test_knowledge_base_searches_symptoms_and_related_rules():
    kb = KnowledgeBase()

    symptom_results = kb.search("169.254")
    rule_results = kb.search("gateway_unreachable")

    assert any(result["id"] == "dhcp_apipa" for result in symptom_results)
    assert any(result["id"] == "gateway_configuration" for result in rule_results)


def test_knowledge_article_detail_has_actionable_sections():
    kb = KnowledgeBase()
    article = kb.get("proxy_vpn_interference")

    assert article is not None
    assert article["symptoms"]
    assert article["checks"]
    assert article["fixes"]
    assert article["escalation"]
