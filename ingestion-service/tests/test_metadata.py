import os
import sys

TEST_DIR = os.path.dirname(__file__)
INGESTION_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
if INGESTION_DIR not in sys.path:
    sys.path.insert(0, INGESTION_DIR)

import metadata
from llm_metadata import _normalize_llm_result, _parse_llm_response, enrich_metadata_with_llm


def test_extract_cve_id_from_title():
    title = "Hackers exploit Windmill flaw (CVE-2026-29059)"
    assert metadata.extract_cve_id(title) == "CVE-2026-29059"


def test_extract_cve_id_returns_none_when_missing():
    assert metadata.extract_cve_id("General security news") is None


def test_severity_from_cvss_score():
    text = "The vulnerability has a CVSS score of 7.5"
    assert metadata.extract_severity_fallback(text) == "HIGH"


def test_extract_topic_tags_fallback_for_ransomware():
    text = "A new ransomware campaign targets hospitals"
    tags = metadata.extract_topic_tags_fallback(text)
    assert "ransomware" in tags
    assert "malware" not in tags


def test_enrich_article_metadata_combined():
    title = "Critical Apache flaw (CVE-2024-1234) under active exploit"
    snippet = "Administrators should patch immediately. CVSS score: 9.8"
    result = metadata.enrich_article_metadata(title, snippet)

    assert result["cve_id"] == "CVE-2024-1234"
    assert result["severity"] == "CRITICAL"
    assert "cve" in result["topic_tags"]
    assert "vulnerability" in result["topic_tags"]


def test_extract_affected_system_fallback():
    title = "Microsoft Windows zero-day exploited in the wild"
    assert metadata.extract_affected_system_fallback(title, title) == "Windows"


def test_parse_llm_response_json():
    parsed = _parse_llm_response(
        '{"severity": "HIGH", "affected_system": "Apache", "topic_tags": ["cve"]}'
    )
    assert parsed["severity"] == "HIGH"
    assert parsed["affected_system"] == "Apache"


def test_normalize_llm_result_uses_fallback_topic_tags():
    parsed = {
        "severity": "LOW",
        "affected_system": "Chrome",
        "topic_tags": ["phishing"],
    }
    result = _normalize_llm_result(
        parsed,
        "Chrome bug fixed",
        "Google patched a browser issue",
        "CVE-2024-9999",
    )
    assert result["severity"] == "LOW"
    assert result["affected_system"] == "Chrome"
    assert result["topic_tags"] == ["cve"]


def test_enrich_metadata_falls_back_when_llm_unavailable(monkeypatch):
    monkeypatch.setattr("llm_metadata._call_cohere", lambda _prompt: None)

    result = enrich_metadata_with_llm(
        "Ransomware hits hospitals (CVE-2025-1000)",
        "Critical severity attack",
    )
    assert result["cve_id"] == "CVE-2025-1000"
    assert "ransomware" in result["topic_tags"]


def test_enrich_metadata_falls_back_on_failed_llm_response(monkeypatch):
    monkeypatch.setattr("llm_metadata._call_cohere", lambda _prompt: None)

    result = enrich_metadata_with_llm(
        "Data breach exposes customer records",
        "Company confirms leak of user data",
    )
    assert "data breach" in result["topic_tags"]
