"""ОСНОВНОЙ ФАЙЛ БОТА"""
import asyncio
import logging

# Импорты
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler_di import ContextSchedulerDecorator
from asyncpg import create_pool

from config import DATABASE

# Конфиг
from config import TOKEN, REDIS

logging.basicConfig(level=logging.INFO, handlers=[
    logging.StreamHandler()
])
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Роутеры (Routers)
from handlers.moderation import router as moderation_router
from handlers.on_join_captcha import router as on_join_notify

from middlewares.SchedulerMiddleware import SchedulerMiddleware
from middlewares.DatabaseMiddleware import DataBaseMiddleware

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

    pool_connect = await create_pool(DATABASE)

    scheduler.ctx.add_instance(bot, declared_class=Bot)
    scheduler.start()

    dp = Dispatcher()
    dp.message.middleware(DataBaseMiddleware(pool_connect))
    dp.callback_query.middleware(DataBaseMiddleware(pool_connect))
    dp.include_routers(on_join_notify, moderation_router)
    dp.update.middleware(SchedulerMiddleware(scheduler))
    await asyncio.gather(dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot power off')