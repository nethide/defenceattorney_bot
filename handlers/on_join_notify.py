from aiogram import Bot, Router, F
from aiogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from config import MONITORED_GROUP_ID, NOTIFICATION_GROUP_ID

router = Router()

@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> IS_MEMBER
    )
)
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    if event.chat.id != MONITORED_GROUP_ID:
        return

    user = event.new_chat_member.user
    chat = event.chat

    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"

    notification_text = f"🆕 <b>Новый участник!</b>\n\n"

    if user.username:
        notification_text += f"👤 <b>Упоминание:</b> @{user.username}\n"

    notification_text += f"👤 <b>Имя:</b> <a href='tg://user?id={user.id}'>{full_name}</a>\n"

    notification_text += f"📝 <b>Полное имя:</b> {full_name}\n"

    notification_text += f"🆔 <b>ID:</b> <code>{user.id}</code>\n"

    if user.username:
        notification_text += f"📱 <b>Username:</b> @{user.username}\n"

    notification_text += f"💬 <b>Группа:</b> {chat.title}"

    if user.is_bot:
        notification_text += f"\n⚠️ <b>Это бот!</b>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚫 Забанить",
                callback_data=f"ban_{user.id}_{chat.id}"
            )
        ]
    ])

    try:
        await bot.send_message(
            chat_id=NOTIFICATION_GROUP_ID,
            text=notification_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")

@router.callback_query(F.data.startswith("ban_"))
async def handle_ban_button(callback: CallbackQuery, bot: Bot):
    try:
        _, user_id, chat_id = callback.data.split("_")
        user_id = int(user_id)
        chat_id = int(chat_id)

        admin_member = await bot.get_chat_member(NOTIFICATION_GROUP_ID, callback.from_user.id)
        if admin_member.status not in ["creator", "administrator"]:
            await callback.answer("❌ Только администраторы могут банить участников!", show_alert=True)
            return

        await bot.ban_chat_member(chat_id, user_id)

        new_text = callback.message.text + f"\n\n✅ <b>Забанен администратором:</b> {callback.from_user.first_name}"

        await callback.message.edit_text(
            text=new_text,
            parse_mode="HTML"
        )

        await callback.answer("✅ Пользователь забанен!", show_alert=True)

    except Exception as e:
        #await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        print(f"Ошибка при бане пользователя: {e}")