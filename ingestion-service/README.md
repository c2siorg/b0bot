# ingestion-service

Polls cybersecurity RSS feeds, deduplicates articles by URL hash, embeds them,
and upserts the results into Postgres + pgvector. Communicates with the rest of
the system only through Postgres and the job queue — never by importing another
service.

## Status

Polls active rows from the shared ``sources`` table (seeded on first DB init),
enqueues ``article.discovered`` jobs, generates embeddings, and upserts into
Postgres + pgvector. Sources added on the api-service ``/sources`` page with
``status = pending`` are ignored until activated in the database.

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
| `POLLING_INTERVAL_SECONDS` | `900` | RSS polling interval |
| `RSS_FEED_TIMEOUT` | `10` | Per-feed fetch timeout (seconds) |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `HUGGINGFACE_TOKEN` | — | HF token for metadata LLM |
| `METADATA_LLM_MODEL` | `CohereLabs/tiny-aya-global` | Metadata LLM model |
| `METADATA_LLM_PROVIDER` | `cohere` | HF inference provider |

During ingest, articles get `cve_id` (regex), then `severity`, `affected_system`, and `topic_tags`
from Cohere via HF when a token is set, with regex/keyword fallback if the call fails.

RSS feed URLs normally come from the ``sources`` table (``status = active``).
``feeds.py`` keeps the same default list as a fallback if the table is empty
or Postgres is unreachable.

To live-check all feeds locally:

```bash
RUN_FEED_INTEGRATION=1 python3 -m pytest tests/test_feeds.py -v
```
