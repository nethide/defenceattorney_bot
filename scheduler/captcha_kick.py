from aiogram import Bot
from aiogram.types import ChatPermissions
import asyncio

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
    can_add_web_page_previews=False,
)

async def kick_member(bot: Bot, chat_id: int, user_id: int, message_id: int):
    member = await bot.get_chat_member(chat_id, user_id)
    if "restricted" in member.status:
        current_permissions = ChatPermissions(
            can_send_messages=member.can_send_messages,
            can_send_audios=member.can_send_audios,
            can_send_documents=member.can_send_documents,
            can_send_photos=member.can_send_photos,
            can_send_videos=member.can_send_videos,
            can_send_video_notes=member.can_send_video_notes,
            can_send_voice_notes=member.can_send_voice_notes,
            can_send_polls=member.can_send_polls,
            can_send_other_messages=member.can_send_other_messages,
            can_add_web_page_previews=member.can_add_web_page_previews,
        )

        if current_permissions == permissions_mute:
            await bot.ban_chat_member(chat_id, user_id)
            await asyncio.sleep(1)
            await bot.unban_chat_member(chat_id, user_id)
            await bot.delete_message(chat_id, message_id)


