from django.db import models
from django.contrib.auth.models import User
from saite import models as saite_models
from saite.models import City, TelegramGroup


class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='telegram_profile')
    chat_id = models.CharField(max_length=255, unique=True)
    token = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.chat_id}"


class UserLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.timestamp}"


class ParserSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL)
    keywords = models.TextField(blank=True)
    excludes = models.TextField(blank=True)
    groups = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} settings"


class TelegramMessage(models.Model):
    message_id = models.CharField(max_length=255)
    text = models.TextField()
    telegram_profile = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name='messages')
    button_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Message {self.message_id} from user {self.telegram_profile.chat_id}"