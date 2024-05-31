from django.contrib import admin
from .models import City, TelegramGroup
from .models import News


class TelegramGroupInline(admin.TabularInline):
    model = TelegramGroup
    extra = 1


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [TelegramGroupInline]


@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ('group_tag', 'city', 'get_users')
    search_fields = ('group_tag', 'city__name')
    list_filter = ('city',)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)
