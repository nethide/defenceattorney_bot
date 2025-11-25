from aiogram import F, Bot, Router
from aiogram.types import Message
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.filters import Command
from asyncio import sleep
from re import findall
from utils.bots_declination import bots_plural

router = Router()
router.message.filter(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))

@router.message(Command("execution"))
async def execute(message:  Message, bot: Bot):
    chat_type = message.chat.type

    if chat_type == ChatType.GROUP or chat_type == ChatType.SUPERGROUP:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)

        if user.status == ChatMemberStatus.ADMINISTRATOR:
            text = message.reply_to_message.text

            if not text:
                await message.answer("❌ В сообщении нет текста с ID")
                return

            user_ids = findall(r'\b\d{6,}\b', text)

            if not user_ids:
                await message.answer("❌ ID пользователей не найдены")
                return

            user_ids = list(set([int(uid) for uid in user_ids]))

            status_msg = await message.answer(f"""⌛ Суд начинается...
            
Обвиняемые: {await bots_plural(len(user_ids))}
Список обвиняемых (id):
<blockquote expandable>{user_ids}</blockquote>""")

            banned_count = 0
            failed_count = 0
            already_banned = 0

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
                        await message.answer("❌ У бота недостаточно прав для казни 😭")
                        return
                    else:
                        failed_count += 1

            report = f"""⭐ Суд окончен...

📊 Итоги:
<blockquote>🪓 Наказаны: {await bots_plural(banned_count)}
❌ Ошибок: {await bots_plural(failed_count)}
📝 Всего осуждено: {len(user_ids)}</blockquote>

Список обвиняемых (id):
<blockquote expandable>{user_ids}</blockquote>"""

            await status_msg.edit_text(report)

            try:
                await message.reply_to_message.delete()
            except:
                pass


@router.message(Command("execute"))
async def execute_ban(message: Message, bot: Bot):
    """Банит пользователя по ID или по ответу на сообщение"""

    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ["creator", "administrator"]:
            await message.reply("❌ Эта команда доступна только администраторам!")
            return
    except Exception:
        await message.reply("❌ Не могу проверить ваши права!")
        return

    user_id = None
    chat_id = message.chat.id
    user_info = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user = message.reply_to_message.from_user

        full_name = user.first_name
        if user.last_name:
            full_name += f" {user.last_name}"

        user_info = f"{full_name} (ID: {user_id})"

        if user.username:
            user_info += f" @{user.username}"

    else:
        command_args = message.text.split(maxsplit=1)

        if len(command_args) < 2:
            await message.reply(
                "❌ <b>Использование:</b>\n"
                "• <code>/execute [ID]</code> - забанить по ID\n"
                "• <code>/execute</code> (ответ на сообщение) - забанить автора сообщения\n\n"
                "<b>Примеры:</b>\n"
                "• <code>/execute 123456789</code>\n"
                "• Ответьте на сообщение пользователя и напишите <code>/execute</code>",
                parse_mode="HTML"
            )
            return

        try:
            user_id = int(command_args[1])
            user_info = f"ID: {user_id}"
        except ValueError:
            await message.reply("❌ Неверный формат ID! Используйте числовой ID.")
            return

    if user_id == message.from_user.id:
        await message.reply("❌ Вы не можете забанить самого себя!")
        return

    if user_id == bot.id:
        await message.reply("❌ Я не могу забанить сам себя!")
        return

    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if bot_member.status != "administrator" or not bot_member.can_restrict_members:
            await message.reply("❌ У меня нет прав для бана участников!")
            return
    except Exception:
        await message.reply("❌ Не могу проверить свои права!")
        return

    try:
        await bot.ban_chat_member(chat_id, user_id)

        await message.reply(
            f"✅ <b>Пользователь забанен!</b>\n\n"
            f"👤 {user_info}\n"
            f"⚡️ <b>Администратор:</b> {message.from_user.first_name}",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"❌ Ошибка при бане: {str(e)}")




