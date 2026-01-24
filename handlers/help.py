from aiogram import F, Bot, Router
from aiogram.types import Message
from aiogram.filters import Command
from models.users import User
from asyncpg.pool import Pool

router = Router()

@router.message(Command('help'))
async def help(message: Message, bot: Bot, database: Pool):
    if message.chat.type in ["group", "supergroup"]:
        cmd_user  = await User.get_data(bot, database, message.from_user.id, message.chat.id)
        if cmd_user.is_user_admin:
            await message.answer(
                f"❔ Что я умею \n \n"
                "Модерация ⚖️"
                f"<blockquote><code>/execution</code> - ban, ответом на сообщение или по ID \n"
                f"<code>/amnesty</code> - unban, по ID \n"
                f"<code>/tribnal</code> - массовый бан, отправьте список ID и ответьте на сообщение этой командой.</blockquote>")