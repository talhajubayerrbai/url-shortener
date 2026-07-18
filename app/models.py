import random
import string

from django.db import models
from django.utils import timezone


def generate_code(length: int = 7) -> str:
    """Generate a random alphanumeric short code."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


class ShortURL(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    original_url = models.URLField(max_length=2048)
    clicks = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Short URL"
        verbose_name_plural = "Short URLs"

    def __str__(self) -> str:
        return f"{self.code} → {self.original_url[:60]}"

    @classmethod
    def create_unique(cls, original_url: str, custom_code: str | None = None) -> "ShortURL":
        """Create a ShortURL, generating a collision-free code if needed."""
        if custom_code:
            return cls.objects.create(code=custom_code, original_url=original_url)
        for _ in range(10):
            code = generate_code()
            if not cls.objects.filter(code=code).exists():
                return cls.objects.create(code=code, original_url=original_url)
        raise RuntimeError("Failed to generate a unique code — try again.")

    def record_click(self) -> None:
        self.clicks += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=["clicks", "last_accessed"])
