"""Notification service entrypoint.

Schedules digest checks, selects recent articles, sends SMTP emails, and logs
deliveries in ``digest_deliveries`` with idempotency protection.
"""
import logging
import os
import time

from db import (
    delivery_exists,
    get_connection,
    get_due_subscribers,
    get_recent_articles,
    insert_delivery,
    update_digest_sent_at,
)
from digest import (
    get_window_start,
    make_idempotency_key,
    render_digest_email,
    select_articles_for_digest,
    utc_now,
)
from email_client import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("notification-service")

DIGEST_CHECK_INTERVAL_SECONDS = int(os.getenv("DIGEST_CHECK_INTERVAL", "3600"))
MAX_DIGEST_ARTICLES = int(os.getenv("MAX_DIGEST_ARTICLES", "10"))


def run_once() -> None:
    now = utc_now()

    with get_connection() as conn:
        subscribers = get_due_subscribers(conn, now)
        if not subscribers:
            logger.info("no due subscribers found")
            return

        logger.info("found %d due subscribers", len(subscribers))

        for sub in subscribers:
            subscriber_id = sub["id"]
            frequency = sub["digest_frequency"]
            email = sub["email"]

            window_start = get_window_start(now, frequency)
            idem_key = make_idempotency_key(subscriber_id, frequency, window_start)

            if delivery_exists(conn, idem_key):
                logger.info("skip already delivered: %s", idem_key)
                continue

            try:
                recent = get_recent_articles(conn, window_start, MAX_DIGEST_ARTICLES)
                selected = select_articles_for_digest(recent, limit=MAX_DIGEST_ARTICLES)
                subject, body, html_body = render_digest_email(selected, frequency)
                send_email(email, subject, body, html_body=html_body)

                article_ids = [row["id"] for row in selected]
                insert_delivery(
                    conn,
                    subscriber_id=subscriber_id,
                    article_ids=article_ids,
                    status="sent",
                    idempotency_key=idem_key,
                )
                update_digest_sent_at(conn, subscriber_id, now)
                conn.commit()
                logger.info("digest sent to %s (%s articles)", email, len(selected))
            except Exception as exc:
                conn.rollback()
                logger.exception("digest send failed for %s", email)
                try:
                    insert_delivery(
                        conn,
                        subscriber_id=subscriber_id,
                        article_ids=[],
                        status="failed",
                        idempotency_key=idem_key,
                        error_message=str(exc)[:1000],
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    logger.exception("failed to write failed delivery record for %s", email)


def main() -> None:
    logger.info(
        "notification-service starting (check interval: %ss)",
        DIGEST_CHECK_INTERVAL_SECONDS,
    )
    while True:
        run_once()
        time.sleep(DIGEST_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
