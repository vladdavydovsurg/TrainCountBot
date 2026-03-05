import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router
from logging_middleware import LoggingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


async def main() -> None:
    print("BOT STARTING")

    init_db()
    print("DATABASE INITIALIZED")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.update.middleware(LoggingMiddleware())

    dp.include_router(router)
    print("ROUTER CONNECTED")

    await bot.delete_webhook(drop_pending_updates=True)
    print("WEBHOOK CLEARED")

    print("BOT USER:", await bot.get_me())

    print("START POLLING")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())