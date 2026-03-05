from aiogram import BaseMiddleware
from typing import Callable, Dict, Any
from aiogram.types import TelegramObject


class LoggingMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable,
        event: TelegramObject,
        data: Dict[str, Any],
    ):
        print("UPDATE RECEIVED:", event)
        return await handler(event, data)