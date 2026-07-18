from django.contrib import admin

from .models import ShortURL


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ("code", "original_url", "clicks", "created_at", "last_accessed")
    search_fields = ("code", "original_url")
    readonly_fields = ("code", "clicks", "created_at", "last_accessed")
    ordering = ("-created_at",)
