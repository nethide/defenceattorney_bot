from aiogram import F, Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ChatPermissions, ChatMemberBanned
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.filters import Command, CommandObject
from asyncio import sleep
from re import findall
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

            command_args = message.text.split(" ")
            until_date = None

            if message.reply_to_message:
                target_user_id = message.reply_to_message.from_user.id

                if len(command_args) > 2:
                    await message.answer(
                        f"📃 Справка <code>{command.command}</code> \n"
                        f"<code>/{command.command}</code> (ответ на сообщение) [время] [причина]\n\n"
                    )
                    return

                if len(command_args) == 1:
                    time = "Навсегда"
                    reason = "Не указана"
                elif len(command_args) == 2:
                    try:
                        time = await parse_duration_one(command_args[1])
                        until_date = datetime.now() + timedelta(seconds=time)
                        reason = "<code>Не указана</code>"
                    except ValueError:
                        time = "Навсегда"
                        reason = command_args[1]
                else:
                    try:
                        time = await parse_duration_one(command_args[1])
                        until_date = datetime.now() + timedelta(seconds=time)
                    except ValueError:
                        await message.answer(
                            f"📃 Справка <code>{command.command}</code> \n"
                            f"<code>/{command.command}</code> (ответ на сообщение) [время] [причина]\n\n"
                        )
                        return
                    reason = command_args[2]

            else:
                if len(command_args) == 1 or len(command_args) > 4:
                    await message.answer(
                            f"📃 Справка <code>{command.command}</code> \n"
                            f"<code>/{command.command}</code> [id] или [username] [время] [причина]\n\n"
                        )
                    return

                try:
                    target_user_id = int(command_args[1])
                except ValueError:
                    await message.answer(
                            f"📃 Справка <code>{command.command}</code> \n"
                            f"<code>/{command.command}</code> [id] или [username] [время] [причина]\n\n"
                        )
                    return

                if len(command_args) == 2:
                    time = "Навсегда"
                    reason = "Не указана"

                elif len(command_args) == 3:

                    try:
                        time = await parse_duration_one(command_args[2])
                        reason = "Не указана"
                        until_date = datetime.now() + timedelta(seconds=time)
                    except ValueError:
                        time = "Навсегда"
                        reason = command_args[2]

                else:

                    try:
                        time = await parse_duration_one(command_args[2])
                        until_date = datetime.now() + timedelta(seconds=time)
                    except AttributeError:
                        await message.answer(
                            f"📃 Справка <code>{command.command}</code> \n"
                            f"<code>/{command.command}</code> [ID] или [username] \n"
                            f"<code>/{command.command}</code> (ответ на сообщение)\n\n"
                            f"ℹ️ Описание"
                            f"<blockquote><code>{command.command}</code> казнит пользователя по id или по ответу на сообщение.</blockquote>"
                        )
                        return

                    reason = command_args[3]

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

            await target_user.ban_user(reason, until_date, cmd_user.telegram_id)
            await bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=target_user.telegram_id,
                until_date=until_date
            )

            if time == "Навсегда" and reason == "Не указана":
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
                f"📅 Срок: До {until_date} \n"
            )

















