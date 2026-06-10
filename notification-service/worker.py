"""Notification service entrypoint.

Schedules digest jobs, reads subscriber preferences from Postgres, matches
recent articles, and sends email digests over SMTP. Delivery is recorded in
``digest_deliveries`` so a digest is never sent twice.

This is a scaffold. The scheduler, article matching, and SMTP sending land in
the subscription weeks of the timeline. For now the service starts cleanly and
idles, so it can be wired into the compose stack alongside Postgres and Redis.
"""
import logging
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("notification-service")

DIGEST_CHECK_INTERVAL_SECONDS = int(os.getenv("DIGEST_CHECK_INTERVAL", "3600"))


def main() -> None:
    logger.info(
        "notification-service starting (check interval: %ss)",
        DIGEST_CHECK_INTERVAL_SECONDS,
    )
    logger.info("Digest scheduling + SMTP delivery not implemented yet — idling")
    while True:
        # Read subscriber prefs -> match articles -> send digest -> log delivery.
        time.sleep(DIGEST_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
