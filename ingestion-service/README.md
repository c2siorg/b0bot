# ingestion-service

Polls cybersecurity RSS feeds, deduplicates articles by URL hash, embeds them,
and upserts the results into Postgres + pgvector. Communicates with the rest of
the system only through Postgres and the job queue — never by importing another
service.

## Status

Scaffold. The service starts and idles; the RSS poll, dedup, embedding, and
`article.discovered` enqueue pipeline are implemented in later weeks.

## Run

Started as part of the root `docker-compose.yml`:

```bash
docker compose up ingestion-service
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://b0bot:b0bot@postgres:5432/b0bot` | Postgres connection |
| `REDIS_URL` | `redis://redis:6379/0` | Queue / cache |
| `INGESTION_POLL_INTERVAL` | `300` | Seconds between RSS polls |
