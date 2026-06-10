"""Postgres connection helper.

Replaces the previous Pinecone client. Structured article data and vector
search now live in Postgres + pgvector, so the rest of the app talks to a
single database. A simple per-call connection is enough for current traffic;
this is the seam where a pooled connection can drop in later if the workers
put the database under load.
"""
import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://b0bot:b0bot@localhost:5432/b0bot",
)


@contextmanager
def get_connection():
    """Yield a short-lived Postgres connection that returns rows as dicts."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()
