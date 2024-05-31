from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', views.main_page, name='main-page'),
    path('aboutus/', views.about_page, name='about-page'),
    path('news/', views.news_page, name='news-page'),
    path('manage_keywords/', views.manage_keywords, name='manage_keywords'),
    path('get_groups/<int:city_id>/', views.get_groups, name='get_groups'),
    path('success/', views.success, name='success'),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
