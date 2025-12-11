from aiogram import Bot, Router, F
from aiogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions, \
    message_id
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from config import MONITORED_GROUP_ID, NOTIFICATION_GROUP_ID
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

from scheduler.captcha_kick import kick_member
from markups.inline import build_captcha_markup

from config import CAPTCHA_TIME

router = Router()

@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> IS_MEMBER
    )
)
async def on_user_join(event: ChatMemberUpdated, bot: Bot, scheduler: AsyncIOScheduler):
    if event.chat.id != MONITORED_GROUP_ID:
        return

    user = event.new_chat_member.user
    chat = event.chat

    permissions_mute = ChatPermissions(
        can_send_messages=False,
        can_send_audios=False,
        can_send_documents=False,
        can_send_photos=False,
        can_send_videos=False,
        can_send_video_notes=False,
        can_send_voice_notes=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    await bot.restrict_chat_member(
        chat_id=chat.id,
        user_id=user.id,
        permissions=permissions_mute
    )

    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"

    message = await event.answer(f"""
Привет, {user.mention_html(full_name)} 👋🏻. Чтобы отправлять сообщения, нажмите на кнопку ниже. У вас {CAPTCHA_TIME} минут ⌛
""", reply_markup=await build_captcha_markup(user.id))

    until_date = datetime.now() + timedelta(minutes=CAPTCHA_TIME)

    scheduler.add_job(kick_member, trigger='date', run_date=until_date,
                            kwargs={'chat_id': chat.id, 'user_id': user.id, 'message_id': message.message_id})

@router.callback_query(F.data.startswith("verify::"))
async def verify_button(callback: CallbackQuery, bot: Bot):
    chat = await bot.get_chat(callback.message.chat.id)
    verify_user_id = int(callback.data.replace("verify::", ""))
    user = callback.from_user

    if verify_user_id != user.id:
        await callback.answer("❌ Эта кнопка не для тебя")
        return

    default_permissions: ChatPermissions | None = chat.permissions

    if default_permissions is None:
        default_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=False,
            can_send_other_messages=True,
            can_add_web_page_previews=False,
        )

    await bot.restrict_chat_member(
        chat_id=callback.message.chat.id,
        user_id=user.id,
        permissions=default_permissions
    )

    await callback.message.delete()

    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"

    notification_text = f"🆕 <b>Новый участник!</b>\n\n"

    if user.username:
        notification_text += f"👤 <b>Упоминание:</b> @{user.username}\n"

    notification_text += f"👤 <b>Имя:</b> {user.mention_html(f"{user.full_name}")}\n"

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