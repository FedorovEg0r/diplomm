import os
import django
import re
import asyncio
from telethon import TelegramClient, events
from telethon.errors import RpcCallFailError, FloodWaitError, UsernameNotOccupiedError, ChannelPrivateError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, Channel, MessageMediaWebPage
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from datetime import datetime, timezone
import telebot
from telebot.apihelper import ApiTelegramException
from telebot import types
import urllib.parse
import shortuuid
from aiogram.enums import ParseMode

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diplom.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from saite.models import TelegramGroup, AdPost
from telegram_auth.models import TelegramProfile, ParserSetting, User, TelegramMessage
from django.db.models.signals import post_save
from django.dispatch import receiver

api_id = 24503676
api_hash = '0423f4e40d705df79f59c74e2fc67276'
TOKEN = '6794656536:AAHRrqdax_iANoWmeAeMbX6C_YomWgWxsDw'
bot = telebot.TeleBot(TOKEN)

client = TelegramClient('session_name2', api_id, api_hash, system_version="4.16.30-vxCUSTOM")


async def is_recent_message(message):
    now = datetime.now(timezone.utc)
    date = message.date.replace(tzinfo=timezone.utc)
    time_difference = (now - date).total_seconds()
    return time_difference < 30


async def join_channels():
    tags = list(TelegramGroup.objects.all().values_list('group_tag', flat=True))
    for tag in tags:
        await join_channel(tag)


async def join_channel(tag):
    try:
        result = await client(ResolveUsernameRequest(tag.lstrip('@')))
        if not result.chats and not result.users:
            raise UsernameNotOccupiedError(request=ResolveUsernameRequest(tag.lstrip('@')))
        await client(JoinChannelRequest(tag))
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
        await client(JoinChannelRequest(tag))
    except ChannelPrivateError:
        handle_invalid_channel(tag)
    except UsernameNotOccupiedError:
        handle_invalid_channel(tag)
    except ValueError as e:
        if 'No user has "{}" as username'.format(tag) in str(e):
            handle_invalid_channel(tag)
        else:
            raise


def handle_invalid_channel(tag):
    try:
        invalid_group = TelegramGroup.objects.get(group_tag=tag)
        users_with_invalid_group = ParserSetting.objects.filter(groups__icontains=tag).values_list('user', flat=True)

        for user_id in users_with_invalid_group:
            try:
                user = User.objects.get(id=user_id)
                chat_id = user.telegram_profile.chat_id
                bot.send_message(chat_id,
                                 f"Канал с тегом {tag} был удален из ваших настроек, т. к. не существует или "
                                 f"недоступен для входа.")

                parser_setting = ParserSetting.objects.get(user_id=user_id)
                groups = parser_setting.groups.split(',')
                groups = [group.strip() for group in groups if group.strip() != tag]
                parser_setting.groups = ','.join(groups)
                parser_setting.save()

            except User.DoesNotExist:
                continue
            except ParserSetting.DoesNotExist:
                continue

        invalid_group.delete()
    except TelegramGroup.DoesNotExist:
        pass


async def leave_channel(tag):
    try:
        await client(LeaveChannelRequest(await client.get_input_entity(tag)))
    except Exception as e:
        print(f"Ошибка при отписке от канала {tag}: {e}")
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
        await client(LeaveChannelRequest(await client.get_input_entity(tag)))


async def send_media_message(telegram_bot, chat_id, event, text_msg, keyboard):
    media = event.message.media
    if isinstance(media, MessageMediaPhoto):
        file_path = await event.message.download_media()
        with open(file_path, 'rb') as photo:
            telegram_bot.send_photo(chat_id, photo, caption=text_msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        os.remove(file_path)
    elif isinstance(media, MessageMediaDocument):
        file_path = await event.message.download_media()
        if media.document.mime_type.startswith('audio'):
            with open(file_path, 'rb') as audio:
                telegram_bot.send_audio(chat_id, audio, caption=text_msg, reply_markup=keyboard,
                                        parse_mode=ParseMode.HTML)
        elif media.document.mime_type.startswith('video'):
            with open(file_path, 'rb') as video:
                telegram_bot.send_video(chat_id, video, caption=text_msg, reply_markup=keyboard,
                                        parse_mode=ParseMode.HTML)
        else:
            with open(file_path, 'rb') as document:
                telegram_bot.send_document(chat_id, document, caption=text_msg, reply_markup=keyboard,
                                           parse_mode=ParseMode.HTML)
        os.remove(file_path)
    elif isinstance(media, MessageMediaWebPage):
        telegram_bot.send_message(chat_id, text_msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        telegram_bot.send_message(chat_id, text_msg, reply_markup=keyboard, disable_web_page_preview=True,
                                  parse_mode=ParseMode.HTML)


async def normal_handler(event):
    if not await is_recent_message(event.message):
        return
    msg = event.message.message

    chan_tag = event.chat.username
    chan_tag_full = '@' + chan_tag
    media = event.message.media
    file_path = None

    try:
        telegram_group = TelegramGroup.objects.get(group_tag=chan_tag_full)
    except TelegramGroup.DoesNotExist:
        return

    users_with_city = ParserSetting.objects.filter(city=telegram_group.city, city__isnull=False).values_list('user',
                                                                                                             flat=True)
    users_with_custom_group = ParserSetting.objects.filter(groups__icontains=chan_tag_full).values_list('user',
                                                                                                        flat=True)
    all_users = set(users_with_city) | set(users_with_custom_group)

    message_link = f"https://t.me/{chan_tag}/{event.message.id}"

    for user_id in all_users:
        try:
            telegram_profile = TelegramProfile.objects.get(user_id=user_id)
        except TelegramProfile.DoesNotExist:
            continue

        parser = ParserSetting.objects.get(user_id=user_id)
        keywords = parser.keywords.split(',')
        excludes = parser.excludes.split(',') if parser.excludes else []

        found_keywords = [word.strip() for word in keywords if
                          re.search(r'\b' + re.escape(word.strip()) + r'\b', msg, re.IGNORECASE)]
        found_excludes = [word.strip() for word in excludes if
                          re.search(r'\b' + re.escape(word.strip()) + r'\b', msg, re.IGNORECASE)]

        if found_keywords and not found_excludes:
            # keywords_str = ', '.join(found_keywords)
            text_msg = (f"Из канала {telegram_group.group_tag}:\n\n{msg}\n\n"
                        # f"Найдено по ключевым словам: {keywords_str}\n\n"
                        f"<a href='{message_link}'><b>Ссылка на сообщение</b></a>")
            chat_id = telegram_profile.chat_id

            button_id = shortuuid.ShortUUID().random(length=8)
            calendar_button = types.InlineKeyboardButton(
                'Добавить событие в Google Календарь',
                callback_data=f'add_event_to_google_calendar:{button_id}'
            )
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(calendar_button)

            TelegramMessage.objects.create(
                telegram_profile=telegram_profile,
                message_id=event.message.id,
                text=msg,
                button_id=button_id
            )

            try:
                await send_media_message(bot, chat_id, event, text_msg, keyboard)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
                await send_media_message(bot, chat_id, event, text_msg, keyboard)
            except ApiTelegramException as e:
                if "message caption is too long" in str(e):
                    msg = msg[:-(56 + len(telegram_group.group_tag))] + "\n<b><i>(продолжение в посте)</i></b>"

                    text_msg = (f"Из канала {telegram_group.group_tag}:\n\n{msg}\n\n"
                                # f"Найдено по ключевым словам: {keywords_str}\n\n"
                                f"<a href='{message_link}'><b>Ссылка на сообщение</b></a>")
                    try:
                        await send_media_message(bot, chat_id, event, text_msg, keyboard)
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                        await send_media_message(bot, chat_id, event, text_msg, keyboard)


async def check_new_groups():
    while True:
        try:
            if client.is_connected():
                current_channels = set(TelegramGroup.objects.all().values_list('group_tag', flat=True))
                dialogs = await client.get_dialogs()
                subscribed_channels = set('@' + dialog.entity.username for dialog in dialogs if
                                          isinstance(dialog.entity, Channel) and dialog.entity.username)

                new_channels = current_channels - subscribed_channels
                removed_channels = subscribed_channels - current_channels

                for tag in new_channels:
                    try:
                        await join_channel(tag)
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                        await join_channel(tag)

                for tag in removed_channels:
                    try:
                        await leave_channel(tag)
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                        await leave_channel(tag)

        except RpcCallFailError as e:
            await asyncio.sleep(60)

        except Exception as e:
            print(f"An error occurred: {e}")

        await asyncio.sleep(60)


async def main():
    await client.start()
    await join_channels()
    asyncio.create_task(check_new_groups())
    await client.run_until_disconnected()


if __name__ == '__main__':
    client.add_event_handler(normal_handler, events.NewMessage())
    asyncio.run(main())
