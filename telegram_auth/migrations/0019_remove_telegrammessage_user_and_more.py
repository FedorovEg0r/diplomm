# Generated by Django 4.1.7 on 2024-05-31 20:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("telegram_auth", "0018_telegrammessageuser_telegrammessage"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="telegrammessage",
            name="user",
        ),
        migrations.AddField(
            model_name="telegrammessage",
            name="telegram_profile",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="telegram_auth.telegramprofile",
            ),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name="TelegramMessageUser",
        ),
    ]
