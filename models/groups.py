from asyncpg.pool import Pool
from aiogram import Bot

class Group:
    @classmethod
    async def get_group_data(cls, bot: Bot, database: Pool, chat_id: int):
        await database.execute(
            """
            INSERT INTO tg_groups(group_id, settings)
            VALUES($1, '{banwords: [], admins: [], is_captcha_active: false, }')
            ON CONFLICT(group_id) DO NOTHING""",
            chat_id
        )

        tg_chat_data = await bot.get_chat(chat_id)

        return cls(bot, database, chat_id, tg_chat_data)

    def __init__(self, bot: Bot, database: Pool, chat_id: int, tg_chat_data):
        self.bot = bot
        self.database = database
        self.chat_id = chat_id
        self.tg_chat_data = tg_chat_data

    @property
    def group_id(self):
        return self.chat_id

    @property
    def group_name(self):
        return self.tg_chat_data.full_name

    @property
    async def group_admins(self):
        return await self.tg_chat_data.get_administrators()


