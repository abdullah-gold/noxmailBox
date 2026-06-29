"""
filters/filters.py — Custom Aiogram filters.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import AdminRepo


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return False
        return await AdminRepo(session).is_admin(user_id)
