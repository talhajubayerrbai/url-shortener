# URL Shortener

A fast, minimal URL shortener built with **Python / Django 5** and **PostgreSQL**, deployed on **AWS EC2** via Nginx + Gunicorn.

## Features

| Endpoint | Method | Description |
|---|---|---|
| `/` | `POST` | Create a short URL |
| `/<code>` | `GET` | Redirect to the original URL |
| `/<code>/stats` | `GET` | Click stats for a short link |
| `/health/` | `GET` | Health check (used by CI) |
| `/admin/` | `GET` | Django admin |

## Quick Start (local)

```bash
# 1. Clone
git clone <repo-url> && cd url-shortener

# 2. Create .env
cp .env.example .env
# edit .env — set SECRET_KEY, DATABASE_URL, DEBUG=True

# 3. Install dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Migrate & run
python manage.py migrate
python manage.py runserver
```

## API Usage

### Create a short URL

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/path"}'
```

Response `201`:
```json
{
  "code": "aB3kX9z",
  "short_url": "http://localhost:8000/aB3kX9z",
  "original_url": "https://example.com/very/long/path",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Custom short code

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "code": "gh"}'
```

### View stats

```bash
curl http://localhost:8000/aB3kX9z/stats
```

Response `200`:
```json
{
  "code": "aB3kX9z",
  "short_url": "http://localhost:8000/aB3kX9z",
  "original_url": "https://example.com/very/long/path",
  "clicks": 42,
  "created_at": "2024-01-15T10:30:00Z",
  "last_accessed": "2024-01-16T08:22:11Z"
}
```

## Running Tests

```bash
python manage.py test app --verbosity=2
```

## Architecture

```
User → Nginx :80 → Gunicorn :8000 → Django → PostgreSQL
```

Deployed on a single EC2 `t3.micro` with an Elastic IP in `us-east-1`.
Infrastructure is managed by Terraform (state in platform-managed S3).

## CI/CD

The GitHub Actions pipeline runs on every push to `main`:

1. **lint** — flake8
2. **test** — Django test suite (SQLite)
3. **provision** — Terraform apply (EC2 + EIP + SG)
4. **configure** — SSH deploy (git pull, migrate, restart)
5. **verify** — `/health/` smoke test
