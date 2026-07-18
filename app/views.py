import json

from django.db import IntegrityError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import ShortURL


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Create short URL  POST /
# ---------------------------------------------------------------------------

@method_decorator(csrf_exempt, name="dispatch")
class ShortenView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        content_type = request.content_type or ""
        if "application/json" in content_type:
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return HttpResponseBadRequest("Invalid JSON")
            original_url = body.get("url", "").strip()
            custom_code = body.get("code", "").strip() or None
        else:
            original_url = request.POST.get("url", "").strip()
            custom_code = request.POST.get("code", "").strip() or None

        if not original_url:
            return JsonResponse({"error": "url is required"}, status=400)

        if not original_url.startswith(("http://", "https://")):
            return JsonResponse({"error": "url must start with http:// or https://"}, status=400)

        if custom_code and len(custom_code) > 20:
            return JsonResponse({"error": "custom code must be ≤ 20 characters"}, status=400)

        try:
            short = ShortURL.create_unique(original_url, custom_code)
        except IntegrityError:
            return JsonResponse({"error": f"code '{custom_code}' is already taken"}, status=409)
        except RuntimeError as exc:
            return JsonResponse({"error": str(exc)}, status=500)

        base = request.build_absolute_uri("/")
        return JsonResponse(
            {
                "code": short.code,
                "short_url": f"{base}{short.code}",
                "original_url": short.original_url,
                "created_at": short.created_at.isoformat(),
            },
            status=201,
        )


# ---------------------------------------------------------------------------
# Redirect  GET /<code>
# ---------------------------------------------------------------------------

def redirect_view(request: HttpRequest, code: str) -> HttpResponse:
    short = get_object_or_404(ShortURL, code=code)
    short.record_click()
    return redirect(short.original_url, permanent=False)


# ---------------------------------------------------------------------------
# Stats  GET /<code>/stats
# ---------------------------------------------------------------------------

def stats_view(request: HttpRequest, code: str) -> JsonResponse:
    short = get_object_or_404(ShortURL, code=code)
    base = request.build_absolute_uri("/")
    return JsonResponse(
        {
            "code": short.code,
            "short_url": f"{base}{short.code}",
            "original_url": short.original_url,
            "clicks": short.clicks,
            "created_at": short.created_at.isoformat(),
            "last_accessed": short.last_accessed.isoformat() if short.last_accessed else None,
        }
    )
