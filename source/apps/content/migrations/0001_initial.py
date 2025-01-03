# Generated by Django 5.1.4 on 2025-01-02 02:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("description", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                (
                    "prompt_template",
                    models.TextField(help_text="Template for AI content generation"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "content type",
                "verbose_name_plural": "content types",
            },
        ),
        migrations.CreateModel(
            name="Content",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("script", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("scheduled", "Scheduled"),
                            ("published", "Published"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "video_file",
                    models.FileField(blank=True, upload_to="content/videos/"),
                ),
                (
                    "thumbnail",
                    models.ImageField(blank=True, upload_to="content/thumbnails/"),
                ),
                ("scheduled_time", models.DateTimeField(blank=True, null=True)),
                (
                    "duration",
                    models.IntegerField(default=60, help_text="Duration in seconds"),
                ),
                ("error_message", models.TextField(blank=True)),
                ("processing_started_at", models.DateTimeField(blank=True, null=True)),
                (
                    "processing_completed_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("is_deleted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="content.contenttype",
                    ),
                ),
            ],
            options={
                "verbose_name": "content",
                "verbose_name_plural": "contents",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ContentAsset",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to="content/assets/")),
                (
                    "asset_type",
                    models.CharField(
                        choices=[
                            ("image", "Image"),
                            ("audio", "Audio"),
                            ("subtitle", "Subtitle"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                ("order", models.IntegerField(default=0)),
                (
                    "duration",
                    models.IntegerField(
                        blank=True,
                        help_text="Duration in seconds for audio/video assets",
                        null=True,
                    ),
                ),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "content",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assets",
                        to="content.content",
                    ),
                ),
            ],
            options={
                "verbose_name": "content asset",
                "verbose_name_plural": "content assets",
                "ordering": ["order", "created_at"],
            },
        ),
    ]
