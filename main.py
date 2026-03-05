"""Entry point for TrainCountBot."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router


async def main() -> None:
    """Initialize app components and start polling."""

    # Инициализация базы данных
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(router)

    # ВАЖНО: удаляем webhook и старые updates
    # Это предотвращает TelegramConflictError
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        # Запуск polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())