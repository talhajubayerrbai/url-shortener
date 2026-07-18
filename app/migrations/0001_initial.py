from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ShortURL",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=20, unique=True)),
                ("original_url", models.URLField(max_length=2048)),
                ("clicks", models.PositiveBigIntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_accessed", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Short URL",
                "verbose_name_plural": "Short URLs",
                "ordering": ["-created_at"],
            },
        ),
    ]
