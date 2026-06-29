"""
handlers/common.py — /start and main menu message handlers.
"""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import SUPPORT_USERNAME
from database.repository import AdminRepo, SettingsRepo, UserRepo
from keyboards import admin_main_menu_kb, main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    await UserRepo(session).get_or_create(user.id, user.username)

    is_admin = await AdminRepo(session).is_admin(user.id)
    kb = admin_main_menu_kb() if is_admin else main_menu_kb()

    await message.answer(
        f"👋 Welcome to <b>Mail Market Bot</b>, {user.first_name}!\n\n"
        "Choose an option from the menu below:",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.message(lambda m: m.text == "💰 BALANCE")
async def cmd_balance(message: Message, session: AsyncSession) -> None:
    user = await UserRepo(session).get(message.from_user.id)
    balance = user.balance if user else 0.0
    await message.answer(
        f"💰 <b>Your Balance</b>\n\n"
        f"Current Balance: <b>${balance:.2f}</b>",
        parse_mode="HTML",
    )


@router.message(lambda m: m.text == "💳 DEPOSIT")
async def cmd_deposit(message: Message, session: AsyncSession) -> None:
    text = await SettingsRepo(session).get(
        "deposit_text",
        "💳 <b>How to Deposit</b>\n\nContact support to top up your balance.",
    )
    await message.answer(text, parse_mode="HTML")


@router.message(lambda m: m.text == "🆘 SUPPORT")
async def cmd_support(message: Message, session: AsyncSession) -> None:
    username = await SettingsRepo(session).get("support_username", SUPPORT_USERNAME)
    await message.answer(
        f"🆘 <b>Support</b>\n\n"
        f"Contact our support team:\n"
        f"👉 https://t.me/{username}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
