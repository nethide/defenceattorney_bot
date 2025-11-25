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
from handlers.on_join_notify import router as on_join_notify

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="execution", description="Массовая казнь."),
        BotCommand(command="execute", description="Забанить пользователя."),
    ]
    await bot.set_my_commands(commands)


async def main():
    dp = Dispatcher()
    dp.include_routers(execute_router, on_join_notify)
    await setup_bot_commands(bot)
    await asyncio.gather(dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot power off')