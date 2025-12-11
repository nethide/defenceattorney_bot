"""ОСНОВНОЙ ФАЙЛ БОТА"""
import asyncio
import logging

# Импорты
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Chat, ChatMember
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler_di import ContextSchedulerDecorator

# Конфиг
from config import TOKEN, REDIS

logging.basicConfig(level=logging.INFO, handlers=[
    logging.StreamHandler()
])
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Роутеры (Routers)
from handlers.moderation import router as execute_router
from handlers.on_join_captcha import router as on_join_notify

from middlewares.SchedulerMiddleware import SchedulerMiddleware

async def main():
    jobstores = {
        'default': RedisJobStore(jobs_key='dispatched_trips_jobs',
                                 run_times_key='dispatched_trips_running',
                                 db=2,
                                 port=6379)
    }
    if REDIS:
        scheduler = ContextSchedulerDecorator(AsyncIOScheduler(timezone="Europe/Moscow", jobstores=jobstores))
    else:
        scheduler = ContextSchedulerDecorator(AsyncIOScheduler(timezone="Europe/Moscow"))

    scheduler.ctx.add_instance(bot, declared_class=Bot)
    scheduler.start()

    dp = Dispatcher()
    dp.include_routers(execute_router, on_join_notify)
    dp.update.middleware(SchedulerMiddleware(scheduler))
    await asyncio.gather(dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot power off')