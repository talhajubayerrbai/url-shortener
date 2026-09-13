import os
import random
import string
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

app = FastAPI(title="URL Shortener", version="1.0.0")

# In-memory store: short_code -> original_url
_store: dict[str, str] = {}


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str


def _generate_code(length: int = 7) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        if code not in _store:
            return code


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe used by the ALB target group."""
    return {"status": "ok", "store_size": len(_store)}


@app.post("/shorten", response_model=ShortenResponse, tags=["urls"])
def shorten(body: ShortenRequest) -> ShortenResponse:
    """Accept a long URL and return a short code."""
    original = str(body.url)
    code = _generate_code()
    _store[code] = original
    base = os.getenv("BASE_URL", "http://localhost:8080")
    return ShortenResponse(
        short_code=code,
        short_url=f"{base}/{code}",
        original_url=original,
    )


@app.get("/{code}", tags=["urls"])
def redirect(code: str):
    """Redirect to the original URL for the given short code."""
    if code not in _store:
        raise HTTPException(status_code=404, detail=f"Code '{code}' not found")
    return RedirectResponse(url=_store[code], status_code=302)
