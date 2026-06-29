"""
handlers/my_accounts.py — MY ACCOUNTS with pagination.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import AccountRepo
from keyboards import accounts_pagination_kb
from utils import format_account_history, total_pages

router = Router()

PER_PAGE = 5


async def _show_accounts(
    target: Message | CallbackQuery,
    session: AsyncSession,
    page: int,
    edit: bool = False,
) -> None:
    user_id = target.from_user.id
    accounts, total = await AccountRepo(session).get_user_purchases(
        user_id, offset=page * PER_PAGE, limit=PER_PAGE
    )

    if total == 0:
        text = "📦 <b>My Accounts</b>\n\nYou haven't purchased any accounts yet."
        kb = None
    else:
        tp = total_pages(total, PER_PAGE)
        lines = [f"📦 <b>My Accounts</b>  (Page {page + 1}/{tp})\n"]
        for i, acc in enumerate(accounts, start=page * PER_PAGE + 1):
            lines.append(format_account_history(acc, i))
            lines.append("")
        text = "\n".join(lines)
        kb = accounts_pagination_kb(page, tp)

    msg = target if isinstance(target, Message) else target.message
    if edit:
        await msg.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await msg.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(lambda m: m.text == "📦 MY ACCOUNTS")
async def my_accounts(message: Message, session: AsyncSession) -> None:
    await _show_accounts(message, session, page=0)


@router.callback_query(F.data.startswith("myacc:"))
async def paginate_accounts(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split(":")[1])
    await _show_accounts(callback, session, page, edit=True)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
