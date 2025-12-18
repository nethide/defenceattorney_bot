from aiogram import F, Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.filters import Command, CommandObject
from asyncio import sleep
from re import findall
from datetime import datetime, timedelta, timezone
from asyncpg.pool import Pool

from models.users import User

router = Router()

@router.message(Command("execution_new"))
async def execution(message: Message, database: Pool, bot: Bot):
    if message.chat.type in ("group", "supergroup"):
        cmd_user = User(bot, database, message.from_user.id, message.chat.id)
        if cmd_user.is_user_admin():
            print(1)

