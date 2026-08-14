"""Optional LLM enrichment for article metadata."""

import json
import logging
import re

from config import (
    HUGGINGFACE_TOKEN,
    METADATA_LLM_MODEL,
    METADATA_LLM_PROVIDER,
)
from metadata import (
    enrich_article_metadata,
    extract_affected_system_fallback,
    extract_severity_fallback,
    extract_topic_tags_fallback,
)

logger = logging.getLogger(__name__)

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def _build_prompt(title: str, snippet: str) -> str:
    return (
        "Analyze this cybersecurity news item and return JSON only.\n"
        "Use null when unknown. Do not guess.\n"
        f"severity must be one of CRITICAL, HIGH, MEDIUM, LOW, or null.\n"
        "Return affected_system as the main product or vendor affected, or null.\n"
        'Format: {"severity": null, "affected_system": null}\n\n'
        f"Title: {title}\n"
        f"Snippet: {snippet}\n"
    )


def _parse_llm_response(raw: str) -> dict | None:
    if not raw:
        return None

    candidate = raw.strip()
    if not candidate.startswith("{"):
        match = JSON_OBJECT_PATTERN.search(candidate)
        if not match:
            return None
        candidate = match.group(0)

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None
    return parsed


def _normalize_llm_result(parsed: dict, title: str, snippet: str, cve_id: str | None) -> dict:
    combined = f"{title}. {snippet}".strip()

    severity = parsed.get("severity")
    if isinstance(severity, str):
        severity = severity.strip().upper()
        if severity not in VALID_SEVERITIES:
            severity = None
    else:
        severity = None

    affected_system = parsed.get("affected_system")
    if isinstance(affected_system, str):
        affected_system = affected_system.strip() or None
    else:
        affected_system = None

    if severity is None:
        severity = extract_severity_fallback(combined)
    if affected_system is None:
        affected_system = extract_affected_system_fallback(title, combined)
    topic_tags = extract_topic_tags_fallback(combined, cve_id=cve_id)

    return {
        "severity": severity,
        "affected_system": affected_system,
        "topic_tags": topic_tags,
    }


def _call_cohere(prompt: str) -> str | None:
    if not HUGGINGFACE_TOKEN:
        return None

    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        logger.warning("huggingface_hub not installed; skipping metadata LLM")
        return None

    try:
        client = InferenceClient(
            provider=METADATA_LLM_PROVIDER,
            api_key=HUGGINGFACE_TOKEN,
        )
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=METADATA_LLM_MODEL,
            max_tokens=256,
            temperature=0,
        )
    except Exception:
        logger.exception("metadata LLM request failed")
        return None

    choices = getattr(response, "choices", None) or []
    if not choices:
        return None

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None) if message else None
    if isinstance(content, str):
        return content
    return None


def enrich_metadata_with_llm(title: str, snippet: str) -> dict:
    """Try LLM enrichment, then fill gaps with regex/keyword fallbacks."""
    base = enrich_article_metadata(title, snippet)

    prompt = _build_prompt(title or "", snippet or "")
    raw = _call_cohere(prompt)
    parsed = _parse_llm_response(raw) if raw else None
    if not parsed:
        return base

    llm_fields = _normalize_llm_result(parsed, title or "", snippet or "", base.get("cve_id"))
    return {
        "cve_id": base.get("cve_id"),
        "severity": llm_fields["severity"],
        "affected_system": llm_fields["affected_system"],
        "topic_tags": llm_fields["topic_tags"] or base.get("topic_tags", []),
    }
