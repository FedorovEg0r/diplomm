# Generated by Django 4.1.7 on 2024-05-28 21:36

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("saite", "0013_telegramgroup_users_alter_telegramgroup_channel_id_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="telegramgroup",
            name="is_custom",
        ),
    ]
