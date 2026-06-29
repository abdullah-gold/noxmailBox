"""
handlers/buy.py — BUY MAIL flow: mail type → service → confirm → deliver.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import AccountRepo, ServiceRepo, UserRepo
from keyboards import confirm_purchase_kb, mail_type_kb, services_kb
from states import BuyFlow
from utils import format_account_delivery, mail_label

router = Router()


@router.message(lambda m: m.text == "🛒 BUY MAIL")
async def buy_mail_start(message: Message, state: FSMContext) -> None:
    await state.set_state(BuyFlow.selecting_mail_type)
    await message.answer(
        "📬 <b>Select mail type:</b>",
        reply_markup=mail_type_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "buy:back_mail")
async def back_to_mail_type(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BuyFlow.selecting_mail_type)
    await callback.message.edit_text(
        "📬 <b>Select mail type:</b>",
        reply_markup=mail_type_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"), BuyFlow.selecting_mail_type)
async def select_mail_type(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    mail_type = callback.data.split(":")[1]
    services = await ServiceRepo(session).get_by_mail_type(mail_type)

    if not services:
        await callback.answer("❌ No services available for this mail type.", show_alert=True)
        return

    await state.update_data(mail_type=mail_type)
    await state.set_state(BuyFlow.selecting_service)

    await callback.message.edit_text(
        f"📌 <b>{mail_label(mail_type)}</b>\n\nSelect a service:",
        reply_markup=services_kb(services, mail_type),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("service:"), BuyFlow.selecting_service)
async def select_service(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    service_id = int(callback.data.split(":")[1])
    svc = await ServiceRepo(session).get(service_id)

    if svc is None:
        await callback.answer("❌ Service not found.", show_alert=True)
        return

    stock = await ServiceRepo(session).stock_count(service_id)
    if stock == 0:
        await callback.answer("❌ Out of stock for this service!", show_alert=True)
        return

    user = await UserRepo(session).get(callback.from_user.id)
    balance = user.balance if user else 0.0

    if balance < svc.price:
        await callback.answer(
            f"❌ Insufficient balance!\n"
            f"Required: ${svc.price:.2f}  |  Your balance: ${balance:.2f}",
            show_alert=True,
        )
        return

    await state.update_data(service_id=service_id)
    await state.set_state(BuyFlow.confirming)

    await callback.message.edit_text(
        f"🛒 <b>Confirm Purchase</b>\n\n"
        f"📌 Service: <b>{svc.service_name}</b>  [{mail_label(svc.mail_type)}]\n"
        f"💲 Price: <b>${svc.price:.2f}</b>\n"
        f"📦 In Stock: <b>{stock}</b>\n\n"
        f"Your balance: <b>${balance:.2f}</b>",
        reply_markup=confirm_purchase_kb(service_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:"), BuyFlow.confirming)
async def confirm_purchase(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    service_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    svc = await ServiceRepo(session).get(service_id)
    if svc is None:
        await callback.answer("❌ Service no longer exists.", show_alert=True)
        await state.clear()
        return

    user_repo = UserRepo(session)
    user = await user_repo.get(user_id)
    if user is None or user.balance < svc.price:
        await callback.answer("❌ Insufficient balance!", show_alert=True)
        return

    await user_repo.update_balance(user_id, -svc.price)
    account = await AccountRepo(session).purchase(service_id, user_id)

    if account is None:
        await user_repo.update_balance(user_id, svc.price)
        await callback.answer("❌ Out of stock! Your balance was not charged.", show_alert=True)
        await state.clear()
        return

    await state.clear()
    await callback.message.edit_text(
        format_account_delivery(account, svc),
        parse_mode="HTML",
    )
    await callback.answer("✅ Account delivered!")


@router.callback_query(F.data == "back:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.delete()
    await callback.answer()
