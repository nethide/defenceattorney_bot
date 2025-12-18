from asyncpg.pool import Pool
from aiogram import Bot
from aiogram.types import ChatMember
from datetime import datetime
from typing import Any

class User:
    @classmethod
    async def get_data(cls, bot: Bot, pool: Pool, telegram_id: int, group_id: int):
        await pool.execute(
        """
            INSERT INTO users (telegram_id) VALUES ($1)
            ON CONFLICT (telegram_id) DO NOTHING
            """, telegram_id
        )

        await pool.execute(
        """
            INSERT INTO user_groups (telegram_id, group_id) VALUES ($1, $2)
            ON CONFLICT (telegram_id, group_id) DO NOTHING
            """, telegram_id, group_id
        )

        data = await pool.fetchrow(
            """
            SELECT * 
            FROM user_groups
            WHERE telegram_id = $1
            and group_id = $2
            """,
            telegram_id, group_id
        )

        tg_data = await bot.get_chat_member(group_id, telegram_id)

        return cls(bot, pool, telegram_id, group_id, data, tg_data)

    def __init__(self, bot: Bot, pool: Pool, telegram_id: int, group_id: int, data: dict, tg_data: ChatMember):
        self.pool = pool
        self.telegram_id = telegram_id
        self.data = data
        self.group_id = group_id
        self.bot = bot
        self.tg_data = tg_data

    def telegram_id(self):
        return self.telegram_id

    def group_id(self):
        return self.data['group_id']

    @property
    def warnings(self):
        return self.data["warnings_count"]

    @property
    def role(self):
        return self.data["role"]

    @property
    def is_banned(self):
        return self.data["is_banned"]

    @property
    def ban_reason(self):
        return self.data["ban_reason"]

    async def ban_user(self, reason: str, until: Any, moderator_id: str):
        await self.pool.execute(
            """
            UPDATE user_groups
            SET is_banned = true,
            ban_reason = $1
            WHERE telegram_id = $2
            AND group_id = $3
            """, reason, self.telegram_id, self.group_id
        )

        print(until)

        if not until:
            until = None
        else:
            until = until.replace(tzinfo=None)

        await self.pool.execute(
            """
            INSERT INTO moderator_log(group_id, user_id, action, reason, moderator_id, until)
            VALUES($1, $2, $3, $4, $5, $6)
            """, self.data['group_id'], self.data['telegram_id'], 'ban', reason, moderator_id, until
        )

    async def unban_user(self, reason: str, until: Any, moderator_id: str):
        await self.pool.execute(
            """
            UPDATE users_groups
            SET is_banned = false,
            ban_reason = ''
            WHERE telegram_id = $2
            AND group_id = $3
            """, reason, self.telegram_id, self.group_id
        )

        await self.pool.execute(
            """
            DELETE FROM moderator_log
            WHERE group_id = $1,
            user_id = $2
            """, self.data['group_id'], self.data['user_id'],
        )

    async def mute_user(self, reason: str, until: Any, moderator_id: str):
        await self.pool.execute(
            """
            INSERT INTO moderator_log(group_id, user_id, action, reason, moderator_id, until)
            VALUES($1, $2, $3, $4, $5, $6)
            """, self.data['group_id'], self.data['user_id'], 'mute', reason, moderator_id,
            datetime.fromtimestamp(until if until else None)
        )

    async def warn_user(self, reason: str, until: Any, moderator_id: str):
        await self.pool.execute(
            """
            UPDATE users_groups 
            SET warnings_count = warnings_count + 1
            WHERE telegram_id = $1,
            group_id = $2
            """, self.telegram_id, self.group_id
        )

        await self.pool.execute(
            """
            INSERT INTO moderator_log(group_id, user_id, action, reason, moderator_id, until)
            VALUES($1, $2, $3, $4, $5)
            """, self.data['group_id'], self.data['user_id'], 'warn', reason, moderator_id,
            datetime.fromtimestamp(until if until else None)
        )

    async def count_captcha(self):
        await self.pool.execute(
            """
            UPDATE users_groups
            SET captcha_completed = true
            WHERE captcha_completed is false
            """
        )

    @property
    def is_user_admin(self):
        if self.tg_data is None:
            return False
        return self.tg_data.status in ["administrator", "creator"]

    @property
    def username(self):
        if self.tg_data.user.username is None:
            return ""
        return self.tg_data.user.username

    @property
    def full_name(self):
        if self.tg_data.user.full_name is None:
            return ""
        return self.tg_data.user.full_name

    @property
    def status(self):
        return self.tg_data.status







