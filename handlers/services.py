from aiogram import F, Bot, Router
from asyncpg.pool import Pool
from aiogram.types import Message
from aiogram.types import ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, LEFT, KICKED, ADMINISTRATOR
from models.groups import Group

router = Router()

#Бота добавили в чат без прав
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def bot_added_as_member(event: ChatMemberUpdated):
    if event.chat.type in ["group", "supergroup"]:
        await event.bot.send_message(
            event.chat.id,
            f"🫱🏻‍🫲🏻 Доброго времени суток. \n"
            f"<blockquote>Для пользования судом нужно добавить бота в качестве <u>администратора</u>."
            f" Бот не может работать без прав администратора, он покинет эту группу.</blockquote>"
        )
        await event.bot.leave_chat(chat_id=event.chat.id)

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
async def bot_added_as_member(event: ChatMemberUpdated, database: Pool):
    if event.chat.type in ["group", "supergroup"]:
        joined_group = await Group.get_group_data(event.bot, database, event.chat.id)

        await event.bot.send_message(
            chat_id=event.chat.id,
            text=f"👋🏻 Доброго времени суток. "
            f"Спасибо, что добавили меня в \"{joined_group.group_name}\" в качестве администратора.\n\n"
            f"ℹ️ Команда <code>/help</code> поможет вам узнать чем я могу быть полезен."
        )
        print(await joined_group.group_admins)



