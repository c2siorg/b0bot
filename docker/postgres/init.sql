-- B0Bot database schema.
-- Runs automatically on first container start (mounted into
-- /docker-entrypoint-initdb.d). Replaces the previous Pinecone vector store:
-- structured article data and vector search now live together in Postgres.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Articles (structured + vector) ──────────────────────────
CREATE TABLE IF NOT EXISTS articles (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url              TEXT NOT NULL,
    url_hash         TEXT NOT NULL,              -- SHA-256 of normalized URL (dedup key)
    title            TEXT NOT NULL,
    content          TEXT NOT NULL,              -- raw/snippet body from RSS
    summary          TEXT,                       -- LLM summary (filled later by agent)
    author           TEXT,
    source_name      TEXT NOT NULL,              -- e.g. "The Hacker News", "Cyware"
    feed_url         TEXT,                       -- RSS feed URL this article came from
    image_url        TEXT,
    published_at     TIMESTAMPTZ,
    ingested_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cve_id           TEXT,                       -- e.g. CVE-2024-1234 (nullable at ingest)
    severity         TEXT CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    affected_system  TEXT,
    topic_tags       TEXT[] NOT NULL DEFAULT '{}',
    embedding_status TEXT NOT NULL DEFAULT 'pending'
                     CHECK (embedding_status IN ('pending','indexed','failed')),
    embedding        vector(384),               -- NULL until embed worker runs
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT articles_url_hash_unique UNIQUE (url_hash)
);

CREATE INDEX IF NOT EXISTS articles_published_at_idx     ON articles (published_at DESC);
CREATE INDEX IF NOT EXISTS articles_source_name_idx      ON articles (source_name);
CREATE INDEX IF NOT EXISTS articles_severity_idx         ON articles (severity);
CREATE INDEX IF NOT EXISTS articles_topic_tags_idx       ON articles USING GIN (topic_tags);
CREATE INDEX IF NOT EXISTS articles_embedding_status_idx ON articles (embedding_status);

CREATE INDEX IF NOT EXISTS articles_embedding_hnsw_idx
    ON articles USING hnsw (embedding vector_cosine_ops);

-- ─── Subscriptions ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscribers (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            TEXT NOT NULL UNIQUE,
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','active','unsubscribed')),
    digest_frequency TEXT NOT NULL DEFAULT 'daily'
                     CHECK (digest_frequency IN ('daily','weekly')),
    otp_hash         TEXT,
    otp_expires_at   TIMESTAMPTZ,
    verified_at      TIMESTAMPTZ,
    digest_sent_at   TIMESTAMPTZ,               -- last digest sent (prevent duplicates)
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscriber_interests (
    subscriber_id UUID NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
    tag           TEXT NOT NULL,                 -- e.g. Malware, Ransomware, CVE
    PRIMARY KEY (subscriber_id, tag)
);

-- ─── Digest delivery log ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS digest_deliveries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_id   UUID NOT NULL REFERENCES subscribers(id),
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    article_ids     UUID[] NOT NULL,
    provider        TEXT,
    status          TEXT NOT NULL DEFAULT 'sent'
                    CHECK (status IN ('sent','failed')),
    error_message   TEXT,
    idempotency_key TEXT NOT NULL UNIQUE
);

-- ─── Queue idempotency markers ─────────────────────────────────
CREATE TABLE IF NOT EXISTS processed_jobs (
    idempotency_key TEXT PRIMARY KEY,
    event_type      TEXT NOT NULL,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Seed data ─────────────────────────────────────────────────
-- A few sample articles so the API and UI have something to render before the
-- ingestion service is online. url_hash is derived the same way ingestion will
-- derive it, so re-ingesting these URLs is a no-op (ON CONFLICT DO NOTHING).
INSERT INTO articles (url, url_hash, title, content, author, source_name,
                      published_at, severity, topic_tags, embedding_status)
VALUES
    ('https://thehackernews.com/sample/critical-rce-apache',
     encode(digest('https://thehackernews.com/sample/critical-rce-apache', 'sha256'), 'hex'),
     'Critical RCE found in Apache HTTP Server',
     'A critical remote code execution vulnerability was disclosed affecting multiple versions of the Apache HTTP Server. Administrators are urged to patch immediately.',
     'The Hacker News',
     'The Hacker News',
     NOW() - INTERVAL '1 day',
     'CRITICAL',
     ARRAY['CVE','RCE'],
     'pending'),
    ('https://www.bleepingcomputer.com/sample/ransomware-healthcare',
     encode(digest('https://www.bleepingcomputer.com/sample/ransomware-healthcare', 'sha256'), 'hex'),
     'Ransomware campaign targets healthcare providers',
     'A new ransomware campaign is actively targeting hospitals and healthcare providers, encrypting patient record systems and demanding payment.',
     'Bleeping Computer',
     'Bleeping Computer',
     NOW() - INTERVAL '2 days',
     'HIGH',
     ARRAY['Ransomware','Healthcare'],
     'pending')
ON CONFLICT (url_hash) DO NOTHING;
