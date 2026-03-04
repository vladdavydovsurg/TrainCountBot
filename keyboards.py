"""Keyboard builders for bot UI."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_balance_keyboard() -> InlineKeyboardMarkup:
    """Return inline keyboard for changing and showing balance."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="+1", callback_data="add_1"),
                InlineKeyboardButton(text="+3", callback_data="add_3"),
                InlineKeyboardButton(text="+5", callback_data="add_5"),
                InlineKeyboardButton(text="+10", callback_data="add_10"),
            ],
            [
                InlineKeyboardButton(text="-1", callback_data="minus_1"),
            ],
            [
                InlineKeyboardButton(text="Баланс", callback_data="show_balance"),
                InlineKeyboardButton(
                    text="📘 Инструкция", callback_data="show_instruction"
                ),
            ],
        ]
    )