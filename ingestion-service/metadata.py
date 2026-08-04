"""Extract CVE, severity, affected system, and topic tags from article text."""

import html
import re
from typing import Iterable

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)
CVSS_PATTERN = re.compile(
    r"CVSS\s*(?:score)?\s*(?:of\s*)?[:(]?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

KNOWN_TOPIC_TAGS = (
    "malware",
    "ransomware",
    "cve",
    "data breach",
    "vulnerability",
)

SEVERITY_KEYWORDS = (
    ("CRITICAL", ("critical severity", "critically", " zero-day ", " actively exploited ")),
    ("HIGH", ("high severity", "high-severity", " severe ", "urgent")),
    ("MEDIUM", ("medium severity", "moderate")),
    ("LOW", ("low severity", " low risk ", "minor")),
)

PRODUCT_HINTS = (
    "Windows",
    "Linux",
    "macOS",
    "Apache",
    "nginx",
    "Chrome",
    "Firefox",
    "Microsoft",
    "Google",
    "Apple",
    "Oracle",
    "VMware",
    "Cisco",
    "OpenSSL",
    "WordPress",
    "Docker",
    "Kubernetes",
)


def _strip_html(text: str) -> str:
    if not text:
        return ""
    clean = HTML_TAG_PATTERN.sub(" ", text)
    return html.unescape(clean).strip()


def _normalize_text(title: str, snippet: str) -> str:
    title = (title or "").strip()
    snippet = _strip_html(snippet or "")
    return f"{title}. {snippet}".strip(". ").strip()


def extract_cve_id(text: str) -> str | None:
    match = CVE_PATTERN.search(text or "")
    if not match:
        return None
    return match.group(0).upper()


def severity_from_cvss(score: float) -> str | None:
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    if score >= 0.1:
        return "LOW"
    return None


def extract_severity_fallback(text: str) -> str | None:
    if not text:
        return None

    cvss_match = CVSS_PATTERN.search(text)
    if cvss_match:
        try:
            severity = severity_from_cvss(float(cvss_match.group(1)))
            if severity:
                return severity
        except ValueError:
            pass

    lowered = text.lower()
    for severity, phrases in SEVERITY_KEYWORDS:
        if any(phrase in lowered for phrase in phrases):
            return severity
    return None


def extract_affected_system_fallback(title: str, text: str) -> str | None:
    haystack = f"{title or ''} {text or ''}"
    for product in PRODUCT_HINTS:
        if re.search(rf"\b{re.escape(product)}\b", haystack, re.IGNORECASE):
            return product
    return None


def _normalize_tags(tags: Iterable[str]) -> list[str]:
    allowed = {tag.lower(): tag for tag in KNOWN_TOPIC_TAGS}
    normalized: list[str] = []
    for tag in tags:
        key = (tag or "").strip().lower()
        if key in allowed and allowed[key] not in normalized:
            normalized.append(allowed[key])
    return normalized


def extract_topic_tags_fallback(text: str, cve_id: str | None = None) -> list[str]:
    if not text:
        text = ""

    lowered = text.lower()
    tags: list[str] = []

    if cve_id or "cve-" in lowered or " cve " in f" {lowered} ":
        tags.append("cve")
    if "ransomware" in lowered:
        tags.append("ransomware")
    if "malware" in lowered or "trojan" in lowered:
        tags.append("malware")
    if "data breach" in lowered or "breach" in lowered or "leak" in lowered:
        tags.append("data breach")
    if (
        "vulnerability" in lowered
        or "vulnerabilities" in lowered
        or "zero-day" in lowered
        or "zero day" in lowered
        or "flaw" in lowered
        or "exploit" in lowered
    ):
        tags.append("vulnerability")

    return _normalize_tags(tags)


def enrich_article_metadata(title: str, snippet: str) -> dict:
    """Return metadata fields using regex and keyword heuristics."""
    combined = _normalize_text(title, snippet)
    cve_id = extract_cve_id(combined)

    severity = extract_severity_fallback(combined)
    affected_system = extract_affected_system_fallback(title or "", combined)
    topic_tags = extract_topic_tags_fallback(combined, cve_id=cve_id)

    return {
        "cve_id": cve_id,
        "severity": severity,
        "affected_system": affected_system,
        "topic_tags": topic_tags,
    }
