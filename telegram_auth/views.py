import json
from django.shortcuts import render
import logging
import secrets
import hashlib
import requests
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.apps import AppConfig
from django.core.signals import request_started
from django.contrib.auth import login
from django.shortcuts import redirect
from .models import TelegramProfile, UserLogin, ParserSetting, TelegramMessage
from saite.models import City, TelegramGroup, AdPost
from django.contrib.auth.models import User
import secrets
from django.contrib.auth import logout
from urllib.parse import urlencode
from django.db.models.signals import post_save
from django.dispatch import receiver





logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def logout_view(request):
    logout(request)
    return redirect('/')


class TelegramAuthConfig(AppConfig):
    name = 'telegram_auth'

    def ready(self):
        request_started.connect(set_webhook)


@receiver(request_started)
def set_webhook(**kwargs):
    print("Setting webhook...")
    try:
        response = requests.post(f"{TELEGRAM_API}{TELEGRAM_TOKEN}/setWebhook", data={'url': WEBHOOK_URL})
        logger.info("Webhook set successfully. Response: %s", response.json())
    except Exception as e:
        logger.error("Error setting webhook: %s", e)


@receiver(post_save, sender=AdPost)
def send_adpost_notification(sender, instance, created, **kwargs):
    if created:
        send_adpost_to_users(instance)


def send_adpost_to_users(ad):
    all_users = ParserSetting.objects.values_list('user', flat=True)
    text_msg = f"{ad.title}\n\n{ad.content}\n\n<i>реклама</i>"
    for user_id in all_users:
        try:
            telegram_profile = TelegramProfile.objects.get(user_id=user_id)
        except TelegramProfile.DoesNotExist:
            continue
        chat_id = telegram_profile.chat_id
        send_telegram_message_with_html(chat_id, text_msg)


TELEGRAM_API = 'https://api.telegram.org/bot'
TELEGRAM_TOKEN = '6794656536:AAHRrqdax_iANoWmeAeMbX6C_YomWgWxsDw'
WEBHOOK_URL = 'https://57b1-85-249-163-148.ngrok-free.app/telegram-webhook'
BASE_URL = WEBHOOK_URL.rsplit('/', 1)[0]


def send_telegram_message(chat_id, text):
    send_url = f'{TELEGRAM_API}{TELEGRAM_TOKEN}/sendMessage'
    response = requests.post(send_url, data={'chat_id': chat_id, 'text': text})
    logger.info(f"Message send attempt to chat_id {chat_id} with response: {response.json()}")


def send_telegram_message_with_html(chat_id, text):
    send_url = f'{TELEGRAM_API}{TELEGRAM_TOKEN}/sendMessage'
    response = requests.post(send_url, data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'})
    logger.info(f"Message send attempt to chat_id {chat_id} with response: {response.json()}")


def generate_and_save_user_token(telegram_profile):
    salt = secrets.token_hex(16)
    data_to_hash = f"{telegram_profile.chat_id}{salt}"
    token = hashlib.sha256(data_to_hash.encode()).hexdigest()
    telegram_profile.token = token
    telegram_profile.save()
    return token


def get_user_by_chat_id(chat_id):
    try:
        telegram_profile = TelegramProfile.objects.get(chat_id=chat_id)
        return telegram_profile.user
    except TelegramProfile.DoesNotExist:
        return None


def send_welcome_message(chat_id):
    welcome_text = (
        "Привет! 👋 Я твой помощник в поиске интересных мероприятий в Телеграм. "
        "На сайте ты сможешь настроить меня, чтобы я автоматически искал для тебя мероприятия и многое другое.\n\n"
        "Чтобы начать, зарегистрируйся на нашем сайте и настрой свои предпочтения поиска. "
        "Я буду присылать тебе уведомления о новых событиях, чтобы ты всегда был в курсе происходящего! 🎉\n\n"
        "Чтобы войти на сайт, используй команду /vhod."
    )
    send_telegram_message(chat_id, welcome_text)


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import City, TelegramGroup, ParserSetting
from django.contrib.auth.models import User


@require_POST
@csrf_exempt
def update_parser_settings(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Пользователь не аутентифицирован'}, status=403)

    user = request.user
    custom_settings = request.POST.get('custom-settings-checkbox') == 'on'
    city_id = request.POST.get('city')
    keywords = request.POST.get('keywords')
    excludes = request.POST.get('excludes')
    groups = request.POST.get('groups')

    ParserSetting.objects.filter(user=user).delete()

    if custom_settings:
        user_groups = list(user.telegram_groups.all())

        user.telegram_groups.clear()

        parser = ParserSetting.objects.create(
            user=user,
            city=None,
            keywords=keywords,
            excludes=excludes,
            groups=groups,
        )

        group_ids = groups.split(',')
        for group_id in group_ids:
            telegram_group, created = TelegramGroup.objects.get_or_create(
                group_tag=group_id,
            )
            if created:
                telegram_group.save()

            telegram_group.users.add(user)

        for group in user_groups:
            if group.users.count() == 0 and group.city is None:
                group.delete()

    else:
        if not city_id:
            return JsonResponse({'status': 'error', 'message': 'Город не указан'}, status=400)

        try:
            city = City.objects.get(id=city_id)
        except City.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Некорректный город'}, status=400)

        parser = ParserSetting.objects.create(
            user=user,
            city=city,
            keywords=keywords,
            excludes=excludes,
        )

        user_groups = user.telegram_groups.all()
        for group in user_groups:
            group.users.remove(user)
            if group.users.count() == 0 and group.city is None:
                group.delete()

    message = "Настройки парсера обновлены.\n"
    if custom_settings:
        message += f"Группы: {groups}\nКлючевые слова: {keywords}\nИсключающие слова: {excludes}"
    else:
        message += f"Город: {city.name}\nКлючевые слова: {keywords}\nИсключающие слова: {excludes}"

    telegram_profile = TelegramProfile.objects.get(user=user)
    send_telegram_message(telegram_profile.chat_id, message)

    return JsonResponse({'status': 'success', 'message': message})


def analyze_event_with_yandex(event_details):
    event_details = " ".join(event_details.split())
    prompt = {
        "modelUri": "gpt://b1gt2vf0v6d27lg1fmi8/yandexgpt",
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 100
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты должен сокращать текст строго в формате трех пунктов и что бы они шли по порядку до трех пунктов ,первый пункт название, второй пункт суть, третий пункт дата.Ты должен вернуть результат строго в формате: название:\n<название события>\nсуть:\n<краткая суть>\nДата:\n<дата события в формате дд.мм.2024> и ничего больше не пиши никакие подробности и так делаее только эти три пункта."
            },
            {
                "role": "user",
                "text": event_details
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Api-Key AQVN15oITxMAsntxACMSCU7KczjLTpludAbRz3mh"
    }

    response = requests.post(url, headers=headers, json=prompt)
    result = response.json()
    print("Yandex API response:", result)  # Debug print to see the response

    if 'result' in result and 'alternatives' in result['result']:
        text = result['result']['alternatives'][0]['message']['text'].strip()
        return text
    else:
        raise ValueError("Unexpected response format: 'alternatives' key not found in response")


def create_google_calendar_link(event_details):
    lines = event_details.split('\n')
    title = ""
    description = ""
    date = ""

    for line in lines:
        if line.lower().startswith("название:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("суть:"):
            description = line.split(":", 1)[1].strip()
        elif line.lower().startswith("дата:"):
            date = line.split(":", 1)[1].strip()
            # Преобразуем дату из формата дд.мм.гггг в формат ггггммдд
            date_parts = date.split('.')
            date = f'{date_parts[2]}{date_parts[1]}{date_parts[0]}'

    query = {
        'action': 'TEMPLATE',
        'text': title,
        'details': description,
        'dates': f'{date}/{date}'
    }
    return f"https://www.google.com/calendar/render?{urlencode(query)}"


@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        message = data.get('message', {})
        callback_query = data.get('callback_query', {})

        if 'text' in message:
            chat_id = message['chat']['id']
            message_text = message['text']

            if message_text == '/start':
                send_welcome_message(chat_id)

            elif message_text == '/vhod':
                username = f"tg_{chat_id}"
                user, user_created = User.objects.get_or_create(username=username)

                if user_created:
                    user.set_password(secrets.token_urlsafe(16))
                user.save()

                telegram_profile, profile_created = TelegramProfile.objects.get_or_create(
                    user=user,
                    defaults={'chat_id': chat_id}
                )

                secure_token = generate_and_save_user_token(telegram_profile)
                login_url = f'{BASE_URL}/login/?token={secure_token}'
                send_telegram_message(chat_id, f'Используйте эту ссылку для входа на сайт: {login_url}')
                return JsonResponse({'status': 'success'})

        elif 'data' in callback_query:
            callback_data = callback_query['data']
            if callback_data.startswith('add_event_to_google_calendar:'):
                button_id = callback_data.split(':')[1]
                telegram_message = TelegramMessage.objects.get(button_id=button_id)
                telegram_profile = telegram_message.telegram_profile
                message_id = telegram_message.message_id
                message_text = telegram_message.text
                chat_id = telegram_profile.chat_id

                # Анализируем событие с помощью Yandex API
                event_details = " ".join(message_text.split())
                analysis_result = analyze_event_with_yandex(event_details)
                calendar_link = create_google_calendar_link(analysis_result)
                add_to_calendar_text = f'<a href="{calendar_link}">Добавить</a>'
                send_telegram_message_with_html(chat_id,
                                                f'Анализ события:\n{analysis_result}\n\nДобавить в Google Календарь: {add_to_calendar_text}')

                telegram_message.delete()

                return JsonResponse({'status': 'success'})

        return JsonResponse({})
    else:
        return HttpResponseNotAllowed(['POST'])


def login_by_token(request):
    token = request.GET.get('token')
    if not token:
        return HttpResponse('Токен не предоставлен', status=400)

    try:
        telegram_profile = TelegramProfile.objects.get(token=token)
        user = telegram_profile.user
        login(request, user)
        UserLogin.objects.create(user=user)
        return redirect('/')
    except TelegramProfile.DoesNotExist:
        return HttpResponse('Неверный токен', status=400)
