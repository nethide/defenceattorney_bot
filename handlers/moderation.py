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





