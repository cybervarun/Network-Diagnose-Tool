from NetworkDiagnosticPlatform.cli import DiagnosticCLI
from NetworkDiagnosticPlatform.cli import main


def test_cli_can_search_knowledge_base():
    cli = DiagnosticCLI()
    results = cli.search_knowledge("firewall")

    assert results
    assert any(result["id"] == "firewall_troubleshooting" for result in results)


def test_cli_can_list_knowledge_articles():
    cli = DiagnosticCLI()
    articles = cli.list_knowledge()

    assert len(articles) >= 6
    assert any(article["id"] == "dns_resolution" for article in articles)


def test_cli_can_show_knowledge_article_detail():
    cli = DiagnosticCLI()
    article = cli.show_knowledge_article("dhcp_apipa")

    assert article is not None
    assert article["checks"]


def test_cli_missing_knowledge_detail_returns_none():
    cli = DiagnosticCLI()

    assert cli.show_knowledge_article("missing") is None


def test_cli_knowledge_detail_command_returns_error_for_missing_article(monkeypatch):
    monkeypatch.setattr("sys.argv", ["network-diagnostic", "--knowledge-detail", "missing"])

    assert main() == 2
