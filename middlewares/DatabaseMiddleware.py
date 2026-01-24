from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from asyncpg import pool


class DataBaseMiddleware(BaseMiddleware):
    def __init__(self, connect: pool.Pool):
        super().__init__()
        self.connect = connect

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.connect.acquire() as database:
            data['database'] = database
            return await handler(event, data)
