from django.contrib import admin
from .models import ParserSetting


@admin.register(ParserSetting)
class ParserSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'groups', 'keywords', 'excludes')
    search_fields = ('user',)

from django.contrib import admin
from .models import TelegramMessage, TelegramMessageUser

@admin.register(TelegramMessageUser)
class TelegramMessageUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id')
    search_fields = ('chat_id',)

@admin.register(TelegramMessage)
class TelegramMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'user', 'text', 'button_id')
    search_fields = ('message_id', 'text', 'user__chat_id')
    list_filter = ('user',)