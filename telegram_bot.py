import os
import django
import asyncio

# Настройка переменной окружения для загрузки настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diplom.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from telethon import TelegramClient, events
from telethon.errors import RpcCallFailError, FloodWaitError, UsernameNotOccupiedError, ChannelPrivateError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, Channel
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from datetime import datetime, timezone
import telebot
from telebot import types
import urllib.parse
import shortuuid
from aiogram.enums import ParseMode
from saite.models import TelegramGroup
from telegram_auth.models import TelegramProfile, ParserSetting, User, TelegramMessage, TelegramMessageUser

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
                                 f"Канал с тегом {tag} был удален из ваших настроек, т. к. не существует или недоступен для входа.")

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

    users_with_city = ParserSetting.objects.filter(city=telegram_group.city, city__isnull=False).values_list('user', flat=True)
    users_with_custom_group = ParserSetting.objects.filter(groups__icontains=chan_tag_full).values_list('user', flat=True)
    all_users = set(users_with_city) | set(users_with_custom_group)

    for user_id in all_users:
        try:
            parser = ParserSetting.objects.get(user_id=user_id)
        except ParserSetting.DoesNotExist:
            continue

        keywords = parser.keywords.split(',')
        excludes = parser.excludes.split(',') if parser.excludes else []

        found_keywords = [word.strip() for word in keywords if word.strip().casefold() in msg.casefold()]
        found_excludes = [word.strip() for word in excludes if word.strip().casefold() in msg.casefold()]

        if found_keywords and not found_excludes:
            keywords_str = ', '.join(found_keywords)
            text_msg = (f"Сообщение из канала {telegram_group.group_tag}:\n\n{msg}\n\n"
                        f"Найдено по ключевым словам: {keywords_str}\n")
            chat_id = parser.user.telegram_profile.chat_id

            try:
                button_id = shortuuid.ShortUUID().random(length=8)
                calendar_button = types.InlineKeyboardButton(
                    'Добавить событие в Google Календарь',
                    callback_data=f'add_event_to_google_calendar:{button_id}'
                )
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(calendar_button)

                user, created = TelegramMessageUser.objects.get_or_create(chat_id=chat_id)
                TelegramMessage.objects.create(user=user, message_id=event.message.id, text=msg, button_id=button_id)

                if media:
                    if isinstance(media, MessageMediaPhoto):
                        file_path = await event.message.download_media()
                        with open(file_path, 'rb') as photo:
                            bot.send_photo(chat_id, photo, caption=text_msg, reply_markup=keyboard)
                        os.remove(file_path)
                    elif isinstance(media, MessageMediaDocument):
                        file_path = await event.message.download_media()
                        with open(file_path, 'rb') as video:
                            bot.send_video(chat_id, video, caption=text_msg, reply_markup=keyboard)
                        os.remove(file_path)
                else:
                    bot.send_message(chat_id, text_msg, reply_markup=keyboard)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
                if media:
                    if isinstance(media, MessageMediaPhoto):
                        file_path = await event.message.download_media()
                        with open(file_path, 'rb') as photo:
                            bot.send_photo(chat_id, photo, caption=text_msg, reply_markup=keyboard)
                        os.remove(file_path)
                    elif isinstance(media, MessageMediaDocument):
                        file_path = await event.message.download_media()
                        with open(file_path, 'rb') as video:
                            bot.send_video(chat_id, video, caption=text_msg, reply_markup=keyboard)
                        os.remove(file_path)
                else:
                    bot.send_message(chat_id, text_msg, reply_markup=keyboard, disable_web_page_preview=True, parse_mode=ParseMode.HTML)


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
                        print(f"Flood wait error for joining channel {tag}. Waiting for {e.seconds} seconds.")
                        await asyncio.sleep(e.seconds + 1)
                        await join_channel(tag)

                for tag in removed_channels:
                    try:
                        await leave_channel(tag)
                    except FloodWaitError as e:
                        print(f"Flood wait error for leaving channel {tag}. Waiting for {e.seconds} seconds.")
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
