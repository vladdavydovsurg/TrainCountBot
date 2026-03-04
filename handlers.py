"""Bot handlers for training balance management."""

from __future__ import annotations

import sqlite3

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database import (
    DB_PATH,
    create_chat,
    get_chat,
    has_seen_private_instruction,
    mark_private_instruction_seen,
    update_balance,
    update_message_id,
)
from keyboards import get_balance_keyboard

router = Router()
ADMIN_ID = 7147954358
INSTRUCTION_TEXT = """
<b>TrainCountBot</b>

Бот для учёта тренировок между тренером и клиентом.

Бот позволяет удобно вести баланс оплаченных тренировок прямо в Telegram-группе с клиентом.

<b>Как начать пользоваться ботом</b>

<b>1. Создайте группу с клиентом</b>

Откройте Telegram.

Нажмите ☰ в левом верхнем углу.

Выберите Создать группу.

Добавьте клиента из списка контактов.

Нажмите Создать.

Введите название группы (например: Тренировки — Иван).

Группа готова.

<b>2. Добавьте бота в группу</b>

Откройте созданную группу.

Нажмите на название группы в верхней части экрана.

В разделе Участники нажмите значок:

➕👤

(добавить участника)

В поиске введите:

@TrainCountBot

Выберите бота TrainCountBot и нажмите Добавить.

<b>3. Сделайте бота администратором</b>

Это необходимо, чтобы бот мог закреплять сообщение с балансом тренировок.

Нажмите на название группы.

Нажмите Управление.

Откройте раздел Администраторы.

Нажмите Добавить администратора.

Выберите TrainCountBot.

Подтвердите назначение.

<b>4. Запустите бота</b>

Напишите в группе команду:

/start

После этого бот:

• создаст сообщение с балансом тренировок
• закрепит это сообщение в группе
• покажет кнопки управления тренировками

<b>Как пользоваться ботом</b>

Тренер управляет балансом тренировок с помощью кнопок.

+1 — добавить 1 тренировку
+3 — добавить 3 тренировки
+5 — добавить 5 тренировок
+10 — добавить 10 тренировок
-1 — списать 1 тренировку

Баланс обновляется автоматически после каждого действия.

Кнопка Баланс показывает текущее количество оставшихся тренировок.

<b>Что видит клиент</b>

Клиент может:

• видеть текущий баланс тренировок
• нажимать кнопку Баланс для проверки количества занятий

Клиент не может изменять баланс.

<b>Важно</b>

• Для каждого клиента создаётся отдельная группа.
• Баланс тренировок хранится отдельно для каждой группы.
• Все изменения баланса сохраняются автоматически.

<b>Если бот не закрепляет сообщение</b>

Проверьте:

Бот добавлен в группу.
Бот назначен администратором.
В группе написана команда /start.

После этого бот закрепит сообщение с балансом.

<b>Поделитесь ботом с коллегами</b>

Если бот оказался полезным, отправьте его другим тренерам.

Просто перешлите им ссылку:

https://t.me/TrainCountBot
""".strip()


def _balance_text(balance: int) -> str:
    """Format balance message shown to users."""
    return f"Баланс тренировок: {balance}"


async def send_instruction(message: Message) -> None:
    """Send bot usage instruction in HTML format."""
    await message.answer(INSTRUCTION_TEXT, parse_mode="HTML")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start for private and group chats."""
    if message.from_user is None:
        return

    if message.chat.type == ChatType.PRIVATE:
        # Show instruction only once when trainer opens bot in private chat.
        user_id = message.from_user.id
        if not has_seen_private_instruction(user_id):
            await send_instruction(message)
            mark_private_instruction_seen(user_id)
        return

    # In groups, create chat (if needed), send balance message and pin it.
    chat_id = message.chat.id
    trainer_id = message.from_user.id

    chat = get_chat(chat_id)
    if chat is None:
        # New chat starts with zero balance.
        chat = create_chat(chat_id=chat_id, trainer_id=trainer_id)

    sent_message = await message.answer(
        _balance_text(chat["balance"]),
        reply_markup=get_balance_keyboard(),
    )

    # Pin can fail in some chats (for example, due to missing rights).
    try:
        await sent_message.pin(disable_notification=True)
    except TelegramBadRequest:
        pass

    update_message_id(chat_id, sent_message.message_id)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Send instruction in group chats only for trainer."""
    if message.from_user is None:
        return

    if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return

    chat = get_chat(message.chat.id)
    if chat is None:
        return

    if message.from_user.id != chat["trainer_id"]:
        return

    await send_instruction(message)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Show bot statistics for admin only."""
    if message.from_user is None or message.from_user.id != ADMIN_ID:
        # Ignore non-admin users silently.
        return

    with sqlite3.connect(DB_PATH) as conn:
        trainers_count = conn.execute(
            "SELECT COUNT(DISTINCT trainer_id) FROM chats"
        ).fetchone()[0]
        clients_count = conn.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
        avg_clients_per_trainer = conn.execute(
            "SELECT COUNT(*) * 1.0 / COUNT(DISTINCT trainer_id) FROM chats"
        ).fetchone()[0]

    # Protect from None when table is empty (division by zero).
    avg_value = float(avg_clients_per_trainer or 0.0)

    await message.answer(
        "📊 Статистика бота\n\n"
        f"Тренеров: {trainers_count}\n"
        f"Клиентов: {clients_count}\n"
        f"Клиентов на тренера: {avg_value:.1f}"
    )


@router.callback_query(
    F.data.in_(
        {
            "add_1",
            "add_3",
            "add_5",
            "add_10",
            "minus_1",
            "show_balance",
            "show_instruction",
        }
    )
)
async def balance_callbacks(callback: CallbackQuery) -> None:
    """Handle inline buttons for changing/showing balance."""
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    chat = get_chat(chat_id)

    if chat is None:
        await callback.answer("Сначала нажмите /start", show_alert=True)
        return

    current_balance = chat["balance"]
    data = callback.data

    # Everyone can request current balance.
    if data == "show_balance":
        await callback.answer(f"Текущий баланс: {current_balance}", show_alert=True)
        return

    # Instruction can be requested only by trainer.
    if data == "show_instruction":
        if user_id != chat["trainer_id"]:
            await callback.answer()
            return
        await send_instruction(callback.message)
        await callback.answer()
        return

    # Only trainer can change balance.
    if user_id != chat["trainer_id"]:
        await callback.answer(
            "Только тренер может управлять балансом тренировок",
            show_alert=True,
        )
        return

    if data == "minus_1" and current_balance == 0:
        await callback.answer("Баланс уже равен 0", show_alert=True)
        return

    delta_map = {
        "add_1": 1,
        "add_3": 3,
        "add_5": 5,
        "add_10": 10,
        "minus_1": -1,
    }

    new_balance = current_balance + delta_map[data]
    chat = update_balance(chat_id, new_balance)
    if chat is None:
        await callback.answer("Ошибка обновления баланса", show_alert=True)
        return

    pinned_message_id = chat.get("message_id") or callback.message.message_id
    try:
        await callback.bot.edit_message_text(
            chat_id=chat_id,
            message_id=pinned_message_id,
            text=_balance_text(new_balance),
            reply_markup=get_balance_keyboard(),
        )
    except TelegramBadRequest:
        # Fallback: edit the message from callback if pinned one is unavailable.
        await callback.message.edit_text(
            _balance_text(new_balance),
            reply_markup=get_balance_keyboard(),
        )
        update_message_id(chat_id, callback.message.message_id)

    await callback.answer()