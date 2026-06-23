# ingestion-service

Polls cybersecurity RSS feeds, deduplicates articles by URL hash, embeds them,
and upserts the results into Postgres + pgvector. Communicates with the rest of
the system only through Postgres and the job queue — never by importing another
service.

## Status

The worker consumes `article.discovered` jobs from a Redis BullMQ queue and
inserts them into Postgres with `embedding_status=pending`. RSS polling and
embedding are not implemented yet.

## Run

```bash
docker compose up ingestion-service
```

## Test the queue

```bash
# publish a test job
docker compose exec ingestion-service python scripts/publish_test_job.py

# check worker logs
docker compose logs ingestion-service

# verify in postgres
docker compose exec postgres psql -U b0bot -d b0bot \
  -c "SELECT title, url_hash, embedding_status FROM articles;"
docker compose exec postgres psql -U b0bot -d b0bot \
  -c "SELECT * FROM processed_jobs;"

# run publish again — same job should be skipped (idempotency)
docker compose exec ingestion-service python scripts/publish_test_job.py
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://b0bot:b0bot@postgres:5432/b0bot` | Postgres connection |
| `REDIS_URL` | `redis://redis:6379/0` | BullMQ queue |
| `ARTICLE_DISCOVERED_QUEUE` | `article-discovered` | Queue name |
