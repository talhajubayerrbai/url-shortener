from django.urls import path

from . import views

urlpatterns = [
    path("", views.ShortenView.as_view(), name="shorten"),
    path("health/", views.health, name="health"),
    path("<str:code>/stats", views.stats_view, name="stats"),
    path("<str:code>", views.redirect_view, name="redirect"),
]
