import json

from django.test import Client, TestCase
from django.urls import reverse

from .models import ShortURL, generate_code


class GenerateCodeTest(TestCase):
    def test_default_length(self):
        code = generate_code()
        self.assertEqual(len(code), 7)

    def test_custom_length(self):
        code = generate_code(length=12)
        self.assertEqual(len(code), 12)

    def test_alphanumeric(self):
        for _ in range(50):
            code = generate_code()
            self.assertTrue(code.isalnum(), f"Non-alphanumeric code: {code}")


class ShortenViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("shorten")

    # --- JSON API ---

    def test_create_returns_201(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"url": "https://example.com"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("code", data)
        self.assertIn("short_url", data)
        self.assertEqual(data["original_url"], "https://example.com")

    def test_create_custom_code(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"url": "https://example.com", "code": "mylink"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["code"], "mylink")

    def test_create_duplicate_code_409(self):
        ShortURL.objects.create(code="taken", original_url="https://a.com")
        resp = self.client.post(
            self.url,
            data=json.dumps({"url": "https://b.com", "code": "taken"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)

    def test_missing_url_400(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_scheme_400(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"url": "ftp://badscheme.com"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_code_too_long_400(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"url": "https://example.com", "code": "a" * 21}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_json_400(self):
        resp = self.client.post(
            self.url,
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    # --- Form POST ---

    def test_create_form_post(self):
        resp = self.client.post(self.url, data={"url": "https://form.example.com"})
        self.assertEqual(resp.status_code, 201)

    def test_create_stores_in_db(self):
        self.client.post(
            self.url,
            data=json.dumps({"url": "https://stored.example.com"}),
            content_type="application/json",
        )
        self.assertEqual(ShortURL.objects.count(), 1)


class RedirectViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.short = ShortURL.objects.create(code="abc123", original_url="https://destination.com")

    def test_redirect_302(self):
        resp = self.client.get(reverse("redirect", kwargs={"code": "abc123"}))
        self.assertRedirects(resp, "https://destination.com", fetch_redirect_response=False)

    def test_redirect_increments_clicks(self):
        self.client.get(reverse("redirect", kwargs={"code": "abc123"}))
        self.short.refresh_from_db()
        self.assertEqual(self.short.clicks, 1)

    def test_redirect_updates_last_accessed(self):
        self.assertIsNone(self.short.last_accessed)
        self.client.get(reverse("redirect", kwargs={"code": "abc123"}))
        self.short.refresh_from_db()
        self.assertIsNotNone(self.short.last_accessed)

    def test_redirect_unknown_code_404(self):
        resp = self.client.get(reverse("redirect", kwargs={"code": "zzz999"}))
        self.assertEqual(resp.status_code, 404)


class StatsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.short = ShortURL.objects.create(code="st1234", original_url="https://stats.example.com")

    def test_stats_200(self):
        resp = self.client.get(reverse("stats", kwargs={"code": "st1234"}))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], "st1234")
        self.assertEqual(data["clicks"], 0)
        self.assertIsNone(data["last_accessed"])

    def test_stats_after_click(self):
        self.client.get(reverse("redirect", kwargs={"code": "st1234"}))
        resp = self.client.get(reverse("stats", kwargs={"code": "st1234"}))
        self.assertEqual(resp.json()["clicks"], 1)

    def test_stats_unknown_404(self):
        resp = self.client.get(reverse("stats", kwargs={"code": "nope00"}))
        self.assertEqual(resp.status_code, 404)


class HealthViewTest(TestCase):
    def test_health_ok(self):
        resp = self.client.get(reverse("health"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})
