from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import City, TelegramGroup
from telegram_auth.views import update_parser_settings
from telegram_auth.models import ParserSetting
import json
import logging
from .forms import NewsForm
from .models import News
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def main_page(request):
    return render(request, 'main.html')


@csrf_exempt
def news_page(request):
    if request.method == 'POST' and request.user.is_staff:
        data = json.loads(request.body)
        form = NewsForm(data)
        if form.is_valid():
            news = form.save()
            return JsonResponse({'id': news.id})
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = NewsForm()

    news = News.objects.all().order_by('-created_at')
    return render(request, 'news.html', {'form': form, 'news': news, 'is_admin': request.user.is_staff})


@csrf_exempt
def delete_news(request, news_id):
    if request.method == 'DELETE' and request.user.is_staff:
        try:
            news = News.objects.get(id=news_id)
            news.delete()
            return JsonResponse({'success': True})
        except News.DoesNotExist:
            return JsonResponse({'error': 'News not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)


def about_page(request):
    user_count = User.objects.count()
    city_count = City.objects.count()
    context = {
        'user_count': user_count,
        'city_count': city_count,
    }
    return render(request, 'about.html', context)


from django.shortcuts import render, redirect
from .models import City
from .forms import ParserForm
from django.contrib.auth.decorators import login_required


@login_required
def manage_keywords(request):
    user = request.user
    existing_parser = ParserSetting.objects.filter(user=user).first()
    existing_city = existing_parser.city if existing_parser else None
    existing_keywords = existing_parser.keywords if existing_parser else ""
    existing_excludes = existing_parser.excludes if existing_parser else ""
    existing_groups = existing_parser.groups if existing_parser else ""

    if request.method == 'POST':
        form = ParserForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data['city']
            keywords = form.cleaned_data['keywords']
            excludes = form.cleaned_data['excludes']
            groups = form.cleaned_data['groups']
            custom_settings = request.POST.get('custom-settings-checkbox')

            logger.debug(
                f"Received POST data: city={city}, keywords={keywords}, excludes={excludes}, groups={groups}, "
                f"custom_settings={custom_settings}")

            if custom_settings:
                city = None

            ParserSetting.objects.filter(user=user).delete()

            parser = ParserSetting.objects.create(
                user=user,
                city=city,
                keywords=keywords,
                excludes=excludes,
                groups=groups,
            )

            request._body = json.dumps({
                'city_id': city.id if city else None,
                'keywords': keywords,
                'excludes': excludes,
                'groups': groups,
            }).encode('utf-8')
            response = update_parser_settings(request)

            return redirect('main-page')
    else:
        form = ParserForm(initial={'city': existing_city, 'keywords': existing_keywords, 'excludes': existing_excludes,
                                   'groups': existing_groups})

    cities = City.objects.all()
    return render(request, 'manage_keywords.html', {
        'form': form,
        'cities': cities,
        'keywords': existing_keywords,
        'existing_city': existing_city,
        'excludes': existing_excludes,
        'groups': existing_groups,
    })


def get_groups(request, city_id):
    groups = TelegramGroup.objects.filter(city_id=city_id).values('group_tag')
    return JsonResponse({'groups': list(groups)})
