# notification-service

Schedules and sends email digests to subscribers. Reads subscriber preferences
and matching articles from Postgres, sends over SMTP, and records each delivery
in `digest_deliveries` for idempotency. Communicates only through Postgres and
the job queue — never by importing another service.

## Status

Scaffold. The service starts and idles; digest scheduling, article matching,
and SMTP delivery are implemented in the subscription weeks.

## Run

Started as part of the root `docker-compose.yml`:

```bash
docker compose up notification-service
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://b0bot:b0bot@postgres:5432/b0bot` | Postgres connection |
| `REDIS_URL` | `redis://redis:6379/0` | Queue / cache |
| `DIGEST_CHECK_INTERVAL` | `3600` | Seconds between digest checks |
| `SMTP_HOST` / `SMTP_PORT` | — | SMTP server (Mailhog added later) |
