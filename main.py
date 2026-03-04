"""Entry point for TrainCountBot."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router


async def main() -> None:
    """Initialize app components and start polling."""
    # Prepare database tables before bot starts receiving updates.
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())