from aiogram import F, Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ChatPermissions, ChatMemberBanned
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.filters import Command, CommandObject
from asyncio import sleep
from re import findall
from babel.dates import format_datetime
from datetime import datetime, timedelta, timezone
from asyncpg.pool import Pool
from utils.duration_parser import parse_duration_one
from aiogram import html

from models.users import User

router = Router()

@router.message(Command("execution"))
async def execution(message: Message, database: Pool, bot: Bot, command: CommandObject):
    if message.chat.type in ("group", "supergroup"):
        cmd_user = await User.get_data(bot, database, message.from_user.id, message.chat.id)

        if cmd_user.is_user_admin:
            try:
                bot_tg_data = await bot.get_chat_member(message.chat.id, bot.id)
                if not bot_tg_data.status in ["administrator"] or not bot_tg_data.can_restrict_members:
                    await message.answer(f"❌ У меня нет прав для выдачи наказаний.")
                    return
            except Exception:
                await message.answer(f"❌ Не могу проверить свои права.")
                return

            command_args = command.args.split()
            reason = None
            time_seconds = None
            until_date = None

            print(command.args)

            if message.reply_to_message:
                target_user_id = message.reply_to_message.from_user.id
                if len(command_args) >= 1:
                    try:
                        time_seconds = await parse_duration_one(args[0])
                        if len(command_args) > 1:
                            reason = " ".join(command_args[1:])
                    except ValueError:
                        reason = " ".join(command_args)

            else:
                if not command_args:
                    await message.answer(
                        f"📃 Справка <code>{command.command}</code> \n"
                        f"<code>/{command.command}</code> [ID] или [username] \n"
                        f"<code>/{command.command}</code> (ответ на сообщение)\n\n"
                        f"ℹ️ Описание"
                        f"<blockquote><code>{command.command}</code> казнит пользователя по id или по ответу на сообщение.</blockquote>"
                    )
                    return

                try:
                    target_user_id = int(command_args[0])
                except ValueError:
                    await message.answer("❌ Вы не указали ID")
                    return

                if len(command_args) >= 2:
                    try:
                        time_seconds = await parse_duration_one(command_args[1])
                        if len(command_args) > 2:
                            reason = " ".join(command_args[2:])
                    except ValueError:
                        reason = " ".join(command_args[1:])

            if cmd_user.telegram_id == target_user_id:
                await message.answer(f"❌ Вы не можете забанить самого себя!")
                return

            if bot.id == target_user_id:
                await message.answer(f"❌ Я не могу забанить сам себя!")
                return

            target_user = await User.get_data(bot, database, target_user_id, message.chat.id)

            mention = f"@{target_user.username}" if target_user.username else html.link(
                target_user.full_name,
                f"tg://user?id={target_user.telegram_id}"
            )

            if target_user.status in ["kicked"]:
                await message.answer(f"⚖️ Пользователю [{target_user.telegram_id}] уже вынесен приговор.")
                return

            if time_seconds:
                until_date = datetime.now(timezone.utc) + timedelta(seconds=time_seconds)
                readable_date = format_datetime(until_date, "d MMMM HH:mm y'г'", locale='ru')

            await target_user.ban_user(reason, until_date, cmd_user.telegram_id)
            await bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=target_user.telegram_id,
                until_date=until_date
            )

            if time_seconds is None and reason is None:
                await message.answer(f"⚖️ {mention} казнен(а) \n")
                return

            if until_date is None:
                await message.answer(
                    f"⚖️ {mention} казнен(а) \n"
                    f"ℹ️ Причина: {reason} \n"
                )
                return

            await message.answer(
                f"⚖️ {mention} казнен(а) \n"
                f"ℹ️ Причина: {reason} \n"
                f"📅 Срок: До {readable_date} \n"
            )

















