"""
middlewares/middlewares.py — DB session injection and anti-spam middleware.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from config import COOLDOWN_SECONDS
from database.engine import AsyncSessionFactory


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionFactory() as session:
            data["session"] = session
            return await handler(event, data)


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._last_action: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and COOLDOWN_SECONDS > 0:
            now = time.monotonic()
            last = self._last_action.get(user.id, 0)
            if now - last < COOLDOWN_SECONDS:
                return
            self._last_action[user.id] = now
        return await handler(event, data)
