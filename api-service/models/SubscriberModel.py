"""Postgres-backed subscriber store.

Handles creating and updating subscriber records for the email digest.
Used by both the /subscribe route and NotificationAgent's chat-based
subscribe flow, so there's exactly one place that writes to subscribers
and subscriber_interests, regardless of how someone subscribed.
"""
import logging

from config.Database import get_connection

logger = logging.getLogger(__name__)


class SubscriberDB:
    def create_subscriber(self, email: str, frequency: str = "daily", interests: list[str] | None = None) -> bool:
        """Insert or reactivate a subscriber and their interest tags.

        Existing subscribers (matched by email) are reactivated and have
        their frequency updated rather than duplicated. Returns False (and
        logs) if the database is unreachable or the insert fails.
        """
        interests = interests or []
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO subscribers (email, digest_frequency, status)
                    VALUES (%(email)s, %(frequency)s, 'active')
                    ON CONFLICT (email) DO UPDATE SET
                        digest_frequency = EXCLUDED.digest_frequency,
                        status = 'active',
                        updated_at = NOW()
                    RETURNING id
                    """,
                    {"email": email, "frequency": frequency},
                )
                subscriber_id = cur.fetchone()["id"]

                for tag in interests:
                    cur.execute(
                        """
                        INSERT INTO subscriber_interests (subscriber_id, tag)
                        VALUES (%(subscriber_id)s, %(tag)s)
                        ON CONFLICT DO NOTHING
                        """,
                        {"subscriber_id": subscriber_id, "tag": tag},
                    )

                conn.commit()
                return True
        except Exception as exc:
            logger.error("Failed to create subscriber: %s", exc)
            return False
