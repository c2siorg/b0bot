"""Central configuration for notification-service.

Environment-backed settings and shared constants live here so worker, db,
digest, and email modules do not duplicate defaults.
"""
import os
from pathlib import Path

# ─── Postgres ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://b0bot:b0bot@postgres:5432/b0bot",
)

# ─── Digest scheduling ────────────────────────────────────────────────────────
DIGEST_CHECK_INTERVAL_SECONDS = int(os.getenv("DIGEST_CHECK_INTERVAL", "3600"))
MAX_DIGEST_ARTICLES = int(os.getenv("MAX_DIGEST_ARTICLES", "10"))
DAILY_DIGEST_WINDOW_DAYS = 1
WEEKLY_DIGEST_WINDOW_DAYS = 7

# ─── SMTP ─────────────────────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_TIMEOUT_SECONDS = 30

# ─── Digest email / frontend links ────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")
DIGEST_EMAIL_TEMPLATE = Path(__file__).parent / "templates" / "digest_email.html"

# ─── Delivery log ─────────────────────────────────────────────────────────────
DEFAULT_EMAIL_PROVIDER = "smtp"
DELIVERY_STATUS_SENT = "sent"
DELIVERY_STATUS_FAILED = "failed"
MAX_ERROR_MESSAGE_LEN = 1000
