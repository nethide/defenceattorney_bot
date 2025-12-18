from asyncpg.pool import Pool
from aiogram import Bot
from datetime import datetime
from typing import Any

class User:
    @classmethod
    async def load_data(cls, pool: Pool, telegram_id: int, group_id: int):
        is_user_registered_global = await pool.fetchval(
        """
        SELECT EXISTS(
            SELECT 1
            FROM users
            WHERE telegram_id = $1
        )
        """,
        telegram_id)

        if not is_user_registered_global:
            await pool.execute(
                """
                INSERT INTO users
                VALUES($1)
                """,
                telegram_id
            )

        is_user_registered_local = await pool.fetchval(
        """
        SELECT EXISTS(
            SELECT 1
            FROM user_groups
            WHERE telegram_id = $1
            AND group_id = $2
        )
        """,
        telegram_id, group_id)

        if not is_user_registered_local:
            await pool.execute(
                """
                INSERT INTO user_groups(telegram_id, group_id)
                VALUES($1, $2) 
                """,
            telegram_id, group_id
            )

        data = await pool.fetchrow(
            """
            SELECT * 
            FROM users_groups
            WHERE telegram_id = $1
            and group_id = $2
            """,
            telegram_id, group_id
        )

        return cls(pool, telegram_id, group_id, data)

    def __init__(self, pool: Pool, telegram_id: int, group_id: int, data: dict):
        self.pool = pool
        self.telegram_id = telegram_id
        self.data = data

    async def telegram_id(self):
        return self.telegram_id

    async def group_id(self):
        return self.data['group_id']

    async def warnings(self):
        return self.data["warnings_count"]

    async def role(self):
        return self.data["role"]

    async def is_banned(self):
        return self.data["is_banned"]

    async def ban_reason(self):
        return self.data["ban_reason"]

    async def ban_user(self, reason: str, until: Any, moderator_id: str):
        await self.pool.execute(
            """
            UPDATE users_groups
            SET is_banned = true
            AND ban_reason = $1
            WHERE telegram_id = $2
            AND group_id = $3
            """, reason, self.telegram_id, self.group_id
        )

        await self.pool.execute(
            """
            INSERT INTO moderator_log(group_id, user_id, action, reason, moderator_id, until)
            VALUES($1, $2, $3, $4, $5, $6)
            """, self.data['group_id'], self.data['user_id'], 'ban', reason, moderator_id,
            datetime.fromtimestamp(until if until else None)
        )

    async def unban_user(self, reason: str, until: Any, moderator_id: str):
        await self.pool.execute(
            """
            UPDATE users_groups
            SET is_banned = false
            AND ban_reason = ''
            WHERE telegram_id = $2
            AND group_id = $3
            """, reason, self.telegram_id, self.group_id
        )

        await self.pool.execute(
            """
            DELETE FROM moderator_log
            WHERE group_id = $1
            AND user_id = $2
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
            WHERE telegram_id = $1
            AND group_id = $2
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




