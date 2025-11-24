"""ОСНОВНОЙ ФАЙЛ БОТА"""
import asyncio
import logging

# Импорты
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import  BotCommand

# Конфиг
from config import TOKEN

logging.basicConfig(level=logging.INFO, handlers=[
    logging.StreamHandler()
])
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Роутеры (Routers)
from handlers.moderation import router as execute_router

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="execution", description="Запугать ботов"),
    ]
    await bot.set_my_commands(commands)


async def main():
    dp = Dispatcher()
    dp.include_routers(execute_router)
    await setup_bot_commands(bot)
    await asyncio.gather(dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot power off')