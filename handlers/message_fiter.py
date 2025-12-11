from aiogram import F, Bot, Router
from aiogram.types import Message

router = Router()

@router.message()
async def message_fiter(message: Message):
    pass