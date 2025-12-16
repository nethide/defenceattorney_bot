from asyncpg.pool import Pool

class User():
    @classmethod
    async def load_data(cls, pool: Pool, telegram_id: int, group_id: int):
        data = await pool.fetchrow(
            """
            SELECT * 
            FROM users_groups
            WHERE telegram_id = $1
            and group_id = $2
            """,
            telegram_id, group_id
        )

        if not data:
            return None

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



