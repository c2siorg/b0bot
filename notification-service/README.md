# notification-service

Schedules and sends email digests to subscribers. Reads subscriber preferences
and matching articles from Postgres, sends over SMTP, and records each delivery
in `digest_deliveries` for idempotency. Communicates only through Postgres and
the job queue — never by importing another service.

## Status

Implemented baseline digest flow:
- Finds due active subscribers (`daily` / `weekly`)
- Selects recent articles in the time window
- Sends digest email through SMTP
- Records each attempt in `digest_deliveries` with idempotency

Future improvement:
- Add tag/embedding-aware filtering and ranking once reliable subscriber
	preferences and article metadata are available.

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
| `MAX_DIGEST_ARTICLES` | `10` | Maximum articles per digest |
| `SMTP_HOST` / `SMTP_PORT` | — | SMTP server (Mailhog added later) |
| `SMTP_USER` / `SMTP_PASSWORD` | — | SMTP auth (optional if relay allows anonymous) |
| `SMTP_FROM` | — | Sender email address |
| `SMTP_USE_TLS` | `true` | Enable STARTTLS |
