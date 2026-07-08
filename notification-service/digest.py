"""Digest building and scheduling helpers."""

import html
import os
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_window_start(now_utc: datetime, frequency: str) -> datetime:
    if frequency == "weekly":
        return now_utc - timedelta(days=7)
    return now_utc - timedelta(days=1)


def make_idempotency_key(subscriber_id, frequency: str, window_start: datetime) -> str:
    return f"digest:{subscriber_id}:{frequency}:{window_start.isoformat()}"


def select_articles_for_digest(articles: list[dict], limit: int = 10) -> list[dict]:
    """Select top articles for digest.

    Current strategy: pick latest articles by time only.

    TODO: Add semantic/tag-based filtering and ranking in future,
    once topic tags / embedding-based subscriber preferences are available.
    """
    return articles[:limit]


_TEMPLATE_PATH = Path(__file__).parent / "templates" / "digest_email.html"
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")


def _article_redirect_url(article_url: str) -> str:
    if not article_url:
        return _FRONTEND_URL
    # Redirect through frontend route so users land on your product UX.
    return f"{_FRONTEND_URL.rstrip('/')}/news?url={quote_plus(article_url)}"


def _render_article_rows(articles: list[dict]) -> str:
    rows = []
    for idx, article in enumerate(articles, start=1):
        title = html.escape(article.get("title") or "Untitled")
        source = html.escape(article.get("source_name") or "Unknown source")
        source_url = article.get("url") or ""
        view_url = html.escape(_article_redirect_url(source_url))
        is_last = idx == len(articles)
        border = "" if is_last else "border-bottom:1px solid #e3d9cb;"

        row = (
            f"<table role='presentation' width='100%' cellspacing='0' cellpadding='0'"
            f" style='{border}padding:16px 0;'>"
            "<tr>"
            f"<td width='28' valign='top'"
            f" style='font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;"
            f"font-size:14px;color:#999;padding-right:8px;'>{idx}.</td>"
            "<td valign='top'>"
            f"<a href='{view_url}'"
            f" style='font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;"
            f"font-size:16px;font-weight:600;line-height:1.45;color:#191919;text-decoration:none;'>"
            f"{title}</a>"
            f"<p style='margin:4px 0 0 0;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,"
            f"Helvetica,Arial,sans-serif;font-size:13px;color:#7a7a7a;'>{source}</p>"
            "</td>"
            "</tr>"
            "</table>"
        )
        rows.append(row)
    return "".join(rows)


def render_digest_email(articles: list[dict], frequency: str) -> tuple[str, str, str]:
    if frequency == "weekly":
        subject = "B0Bot weekly digest"
        heading = "This week's security news"
        period_label = "Weekly"
        subtitle = "Stories from the past seven days, picked from your subscribed feeds."
    else:
        subject = "B0Bot daily digest"
        heading = "Today's security news"
        period_label = "Daily"
        subtitle = "Stories from the past 24 hours, picked from your subscribed feeds."

    if not articles:
        text_body = "No new articles were published in this period."
        html_body = (
            "<html><body style='font-family:Georgia,serif;background:#fbf4ea;color:#191919;padding:32px;'>"
            f"<p style='font-family:sans-serif;font-size:13px;color:#ff6817;font-weight:600;'>B0Bot &middot; {period_label}</p>"
            f"<h2 style='font-family:sans-serif;color:#191919;'>{heading}</h2>"
            f"<p style='font-family:sans-serif;color:#4a4a4a;'>{text_body}</p>"
            f"<p><a href='{_FRONTEND_URL}' style='color:#ff6817;'>Browse all news</a></p>"
            "</body></html>"
        )
        return subject, text_body, html_body

    lines = ["Top cybersecurity updates:", ""]
    for idx, article in enumerate(articles, start=1):
        source = article.get("source_name") or "Unknown Source"
        title = article.get("title") or "Untitled"
        url = _article_redirect_url(article.get("url") or "")
        lines.append(f"{idx}. {title} ({source})")
        if url:
            lines.append(f"   {url}")

    text_body = "\n".join(lines)

    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    site_label = urlparse(_FRONTEND_URL).netloc or "B0Bot"
    html_body = (
        template.replace("{{SUBJECT}}", html.escape(subject))
        .replace("{{HEADING}}", heading)
        .replace("{{PERIOD_LABEL}}", period_label)
        .replace("{{SUBTITLE}}", subtitle)
        .replace("{{ARTICLE_ROWS}}", _render_article_rows(articles))
        .replace("{{FRONTEND_URL}}", html.escape(_FRONTEND_URL))
        .replace("{{SITE_LABEL}}", html.escape(site_label))
    )

    return subject, text_body, html_body
