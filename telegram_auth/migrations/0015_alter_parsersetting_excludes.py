# Generated by Django 4.1.7 on 2024-05-28 22:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("telegram_auth", "0014_remove_parsersetting_groups_parsersetting_groups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="parsersetting",
            name="excludes",
            field=models.TextField(blank=True, null=True),
        ),
    ]