"""Entry point for TrainCountBot."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router


async def main() -> None:
    """Initialize app components and start polling."""

    print("BOT STARTING")

    # Инициализация базы данных
    init_db()
    print("DATABASE INITIALIZED")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    print("BOT AND DISPATCHER CREATED")

    # Подключаем роутеры
    dp.include_router(router)
    print("ROUTER CONNECTED")

    # Удаляем webhook и старые updates
    # Это предотвращает TelegramConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    print("WEBHOOK CLEARED")

    try:
        print("START POLLING")
        await dp.start_polling(bot)
    finally:
        print("BOT STOPPING")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())