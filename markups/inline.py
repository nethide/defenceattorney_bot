from aiogram.types import InlineKeyboardButton as keyboard_button
from aiogram.types import InlineKeyboardMarkup as keyboard

async def build_captcha_markup(telegram_id: int) -> keyboard:
    return keyboard(inline_keyboard=[[keyboard_button(text="🫱🏻‍🫲🏻 Я человек", callback_data=f'verify::{telegram_id}'),]])