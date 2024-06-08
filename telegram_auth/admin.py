from django.contrib import admin
from .models import ParserSetting


@admin.register(ParserSetting)
class ParserSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'groups', 'keywords', 'excludes')
    search_fields = ('user',)


from django.contrib import admin
from .models import TelegramMessage


@admin.register(TelegramMessage)
class TelegramMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'telegram_profile', 'text', 'button_id')
    search_fields = ('message_id', 'text', 'telegram_profile')
