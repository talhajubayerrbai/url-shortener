# URL Shortener

A lightweight URL-shortening service built with **FastAPI** and deployed on **AWS ECS Fargate** via a GitHub Actions CI/CD pipeline.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe (ALB health check) |
| `POST` | `/shorten` | Accept a long URL, return a short code |
| `GET` | `/{code}` | Redirect to the original URL |

## Usage

```bash
# Shorten a URL
curl -X POST https://<host>/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/very/long/path"}'

# Response
# {"short_code": "aB3xY7z", "short_url": "http://<host>/aB3xY7z", "original_url": "https://example.com/very/long/path"}

# Follow the short link
curl -L http://<host>/aB3xY7z
```

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

Open `http://localhost:8080/docs` for the interactive Swagger UI.

## Storage

URLs are stored **in-memory** — they are lost when the container restarts. For persistence, swap the `_store` dict with DynamoDB or Redis.

## Architecture

- **ECS Fargate** — serverless container runtime, no EC2 to manage.
- **Application Load Balancer** — stable public DNS, health checks on `/health`.
- **ECR** — private Docker image registry.
- **S3 backend** — Terraform state stored remotely.
