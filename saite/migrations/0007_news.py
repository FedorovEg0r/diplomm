# Generated by Django 4.1.7 on 2024-05-28 13:00

from django.db import migrations, models
import django_ckeditor_5.fields


class Migration(migrations.Migration):
    dependencies = [
        ("saite", "0006_delete_parser"),
    ]

    operations = [
        migrations.CreateModel(
            name="News",
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
                (
                    "content",
                    django_ckeditor_5.fields.CKEditor5Field(verbose_name="Text"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
