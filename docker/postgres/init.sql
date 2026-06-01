-- B0Bot PostgreSQL schema (GSoC 2026)
-- Applied automatically on first Postgres container start.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE articles (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url              TEXT NOT NULL,
    url_hash         TEXT NOT NULL,
    title            TEXT NOT NULL,
    content          TEXT NOT NULL,
    summary          TEXT,
    author           TEXT,
    source_name      TEXT NOT NULL,
    feed_url         TEXT,
    image_url        TEXT,
    published_at     TIMESTAMPTZ,
    ingested_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cve_id           TEXT,
    severity         TEXT CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    affected_system  TEXT,
    topic_tags       TEXT[] NOT NULL DEFAULT '{}',
    embedding_status TEXT NOT NULL DEFAULT 'pending'
                     CHECK (embedding_status IN ('pending', 'indexed', 'failed')),
    embedding        vector(384),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT articles_url_hash_unique UNIQUE (url_hash)
);

CREATE INDEX articles_published_at_idx     ON articles (published_at DESC);
CREATE INDEX articles_source_name_idx      ON articles (source_name);
CREATE INDEX articles_severity_idx         ON articles (severity);
CREATE INDEX articles_topic_tags_idx       ON articles USING GIN (topic_tags);
CREATE INDEX articles_embedding_status_idx ON articles (embedding_status);

CREATE INDEX articles_embedding_hnsw_idx
    ON articles USING hnsw (embedding vector_cosine_ops);

CREATE TABLE subscribers (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            TEXT NOT NULL UNIQUE,
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'active', 'unsubscribed')),
    digest_frequency TEXT NOT NULL DEFAULT 'daily'
                     CHECK (digest_frequency IN ('daily', 'weekly')),
    otp_hash         TEXT,
    otp_expires_at   TIMESTAMPTZ,
    verified_at      TIMESTAMPTZ,
    digest_sent_at   TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE subscriber_interests (
    subscriber_id UUID NOT NULL REFERENCES subscribers (id) ON DELETE CASCADE,
    tag           TEXT NOT NULL,
    PRIMARY KEY (subscriber_id, tag)
);

CREATE TABLE digest_deliveries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_id   UUID NOT NULL REFERENCES subscribers (id),
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    article_ids     UUID[] NOT NULL,
    provider        TEXT,
    status          TEXT NOT NULL DEFAULT 'sent'
                    CHECK (status IN ('sent', 'failed')),
    error_message   TEXT,
    idempotency_key TEXT NOT NULL UNIQUE
);

CREATE TABLE processed_jobs (
    idempotency_key TEXT PRIMARY KEY,
    event_type      TEXT NOT NULL,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
