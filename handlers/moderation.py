from aiogram import F, Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ChatPermissions
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

#/ban
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

#/unban
@router.message(Command("amnesty"))
async def amnesty(message: Message, database: Pool, bot: Bot, command: CommandObject):
    if message.chat.type in ("group", "supergroup"):
        cmd_user = await User.get_data(bot, database, message.from_user.id, message.chat.id)

        if cmd_user.is_user_admin:
            args = command.args.split()

            if not args:
                await message.answer(
                    f"📃 Справка <code>{command.command}</code> \n"
                    f"<code>/{command.command}</code> [ID] \n"
                    f"ℹ️ Описание"
                    f"<blockquote><code>{command.command}</code> отменяет приговор для указанного пользователя.</blockquote>"
                )
                return

            target_user = await User.get_data(bot, database, int(args[0]), message.chat.id)
            mention = f"@{target_user.username}" if target_user.username else html.link(
                target_user.full_name,
                f"tg://user?id={target_user.telegram_id}"
            )

            if target_user.status in ["kicked"]:
                await target_user.unban_user()
                await bot.unban_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_user.telegram_id
                )

                await message.answer(f"⚖️ {mention}[<code>{target_user.telegram_id}</code>] разблокирован(а)")
                return
            else:
                await message.answer(f"❌ Пользователь не казнён.")

# Устаревшая команда. Переделать.
@router.message(Command("tribunal"))
async def execute(message: Message, bot: Bot):
    chat_type = message.chat.type

    if chat_type == ChatType.GROUP or chat_type == ChatType.SUPERGROUP:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        user = message.from_user

        if member.status == ChatMemberStatus.ADMINISTRATOR and member.can_restrict_members:
            try:
                text = message.reply_to_message.text
            except AttributeError:
                await message.answer(f"{user.mention_html(name=f"{user.full_name}")}, вы не указали на сообщение ❌")
                return
            if not text:
                await message.answer(f"{user.mention_html(name=f"{user.full_name}")}, в сообщении нет текста с ID ❌")
                return

            user_ids = findall(r'\b\d{6,}\b', text)

            if not user_ids:
                await message.answer(
                    f"{user.mention_html(name=f"{user.full_name}")}, в сообщении нет id ❌")
                return

            user_ids = list(set([int(uid) for uid in user_ids]))

            status_msg = await message.answer(
                f"⌛ Выношу приговор для {await members_plural(len(user_ids))}!\n"
            )

            banned_count = 0
            failed_count = 0

            for user_id in user_ids:
                try:
                    await bot.ban_chat_member(
                        chat_id=message.chat.id,
                        user_id=user_id
                    )
                    banned_count += 1

                    await sleep(0.1)

                except Exception as e:
                    error_text = str(e).lower()
                    if "user is an administrator" in error_text:
                        failed_count += 1
                    elif "user not found" in error_text:
                        failed_count += 1
                    elif "not enough rights" in error_text:
                        await message.answer(
                            f"{user.mention_html(name=f"{user.full_name}")}, у бота недостаточно прав ❌")
                        return
                    else:
                        failed_count += 1

            report = (
                f"📃 Итоги суда"
                f"<blockquote>🪓 Наказаны: {await members_plural(banned_count)} \n"
                f"❌ Ошибок: {failed_count}</blockquote>"
                f""
                f"Список обвиняемых (id):"
                f"<blockquote expandable>{user_ids}</blockquote>"
            )

            await status_msg.edit_text(report)

            try:
                await message.reply_to_message.delete()
            except:
                pass


# Старая команда мута. Переделать.
@router.message(Command("quiet"))
async def silence(message: Message, bot: Bot, command: CommandObject):
    cmd_user = message.from_user
    print(type(cmd_user))

    permissions_mute = ChatPermissions(
        can_send_messages=False,
        can_send_audios=False,
        can_send_documents=False,
        can_send_photos=False,
        can_send_videos=False,
        can_send_video_notes=False,
        can_send_voice_notes=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status != ChatMemberStatus.ADMINISTRATOR or not getattr(member, "can_restrict_members", False):
        await message.answer("❌ У вас нет права выдавать наказания")
        return

    if not command.args:
        await message.answer(
            "Форматы:\n"
            f"• Ответом: <code> /{command.command} время причина</code>\n"
            f"• По ID: <code> /{command.command} id время причина</code>"
        )
        return

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

        parts = command.args.split(maxsplit=1)
        time = parts[0]
        reason = parts[1] if len(parts) > 1 else ""

        seconds = await parse_duration_one(time)
        until_date = datetime.now(timezone.utc) + timedelta(seconds=seconds)

        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_user.id,
                permissions=permissions_mute,
                until_date=until_date
            )
        except TelegramBadRequest as e:
            if "user is an administrator of the chat" in e.message:
                await message.answer(
                    f"{cmd_user.mention_html(f"{cmd_user.full_name}")}, вы не можете вы можете вынести приговор коллеге. ")
                return

        await message.answer(
            f"🔇 {target_user.mention_html(name=f"{target_user.full_name}")} обезмолвлен(а)!\n"
            f"⏱ До: <code>{until_date.strftime("%Y-%m-%d %H:%M:%S")}</code>\n"
            f"💬 Причина: <i>{reason or '<code>Не указана</code>'}</i>"
        )
        return

    parts = command.args.split(maxsplit=2)

    if len(parts) < 2:
        await message.answer(f"❌ Формат: {command.command} <code>id</code> <code>время</code> <code>причина</code>")
        return

    user_id_raw = parts[0]
    time = parts[1]
    reason = parts[2] if len(parts) > 2 else ""

    seconds = await parse_duration_one(time)
    until_date = datetime.now(timezone.utc) + timedelta(seconds=seconds)

    try:
        user_id = int(user_id_raw)
    except ValueError:
        await message.answer(f"❌ ID должен быть числом, а не: <code>{user_id_raw}</code>")
        return

    target_user_raw = await bot.get_chat_member(message.chat.id, user_id)
    target_user = target_user_raw.user

    await message.answer(
        f"🔇 {target_user.mention_html(name=f"{target_user.full_name}")} обезмолвлен(а)!\n"
        f"⏱ До: <code>{until_date.strftime("%Y-%m-%d %H:%M:%S")}</code>\n"
        f"💬 Причина: <i>{reason or '<code>Не указана</code>'}</i>"
    )
    return

















