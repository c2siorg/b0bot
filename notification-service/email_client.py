"""SMTP email sender for notification-service."""

import smtplib
from email.message import EmailMessage

from config import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_TIMEOUT_SECONDS,
    SMTP_USE_TLS,
    SMTP_USER,
)


def send_email(to_email: str, subject: str, body: str, html_body: str | None = None) -> None:
    if not SMTP_HOST or not SMTP_FROM:
        raise RuntimeError("SMTP_HOST and SMTP_FROM must be configured")

    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
