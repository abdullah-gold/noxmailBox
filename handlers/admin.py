"""
handlers/admin.py — Full admin panel.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Document, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import SUPPORT_USERNAME
from database.repository import (
    AccountRepo, AdminRepo, ServiceRepo, SettingsRepo, UserRepo,
)
from filters import IsAdmin
from keyboards import (
    admin_back_kb, admin_main_menu_kb, admin_manage_admins_kb,
    admin_mail_type_kb, admin_panel_kb, admin_services_kb,
    admin_upload_services_kb, main_menu_kb, sold_pagination_kb,
)
from services import parse_xlsx
from states import AdminStates
from utils import total_pages

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

SOLD_PER_PAGE = 10


@router.message(lambda m: m.text == "⚙️ ADMIN PANEL")
async def admin_panel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("⚙️ <b>Admin Panel</b>", reply_markup=admin_panel_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "⚙️ <b>Admin Panel</b>", reply_markup=admin_panel_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.add_service_mail_type)
    await callback.message.edit_text(
        "➕ <b>Add Service</b>\n\nSelect mail type:",
        reply_markup=admin_mail_type_kb("addsvc"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("addsvc:"), AdminStates.add_service_mail_type)
async def add_service_mail_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    mail_type = callback.data.split(":")[1]
    await state.update_data(mail_type=mail_type)
    await state.set_state(AdminStates.add_service_name)
    await callback.message.edit_text(
        f"➕ <b>Add Service</b> [{mail_type.upper()}]\n\nEnter service name:",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.add_service_name)
async def add_service_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("❌ Name cannot be empty.")
        return
    await state.update_data(service_name=name)
    await state.set_state(AdminStates.add_service_price)
    await message.answer(f"💲 Enter price for <b>{name}</b> (e.g. 2.50):", parse_mode="HTML")


@router.message(AdminStates.add_service_price)
async def add_service_price(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        price = float(message.text.strip().replace(",", "."))
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Please enter a valid positive number.")
        return

    data = await state.get_data()
    svc = await ServiceRepo(session).create(data["mail_type"], data["service_name"], price)
    await state.clear()
    await message.answer(
        f"✅ Service <b>{svc.service_name}</b> [{svc.mail_type.upper()}] "
        f"added at <b>${svc.price:.2f}</b>.",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin:delete_service")
async def delete_service_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    services = await ServiceRepo(session).all()
    if not services:
        await callback.answer("No services found.", show_alert=True)
        return
    await state.set_state(AdminStates.delete_service_select)
    await callback.message.edit_text(
        "🗑 <b>Delete Service</b>\n\nSelect a service to delete:",
        reply_markup=admin_services_kb(services, "delsvc"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delsvc:"), AdminStates.delete_service_select)
async def delete_service_confirm(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    service_id = int(callback.data.split(":")[1])
    deleted = await ServiceRepo(session).delete(service_id)
    await state.clear()
    if deleted:
        await callback.message.edit_text("✅ Service deleted.", reply_markup=admin_panel_kb())
    else:
        await callback.message.edit_text("❌ Service not found.", reply_markup=admin_panel_kb())
    await callback.answer()


@router.callback_query(F.data == "admin:change_price")
async def change_price_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    services = await ServiceRepo(session).all()
    if not services:
        await callback.answer("No services found.", show_alert=True)
        return
    await state.set_state(AdminStates.change_price_select)
    await callback.message.edit_text(
        "💲 <b>Change Price</b>\n\nSelect a service:",
        reply_markup=admin_services_kb(services, "chprice"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("chprice:"), AdminStates.change_price_select)
async def change_price_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service_id = int(callback.data.split(":")[1])
    svc = await ServiceRepo(session).get(service_id)
    if not svc:
        await callback.answer("Service not found.", show_alert=True)
        return
    await state.update_data(service_id=service_id)
    await state.set_state(AdminStates.change_price_value)
    await callback.message.edit_text(
        f"💲 Enter new price for <b>{svc.service_name}</b> (current: ${svc.price:.2f}):",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.change_price_value)
async def change_price_value(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        price = float(message.text.strip().replace(",", "."))
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Invalid price. Please enter a positive number.")
        return
    data = await state.get_data()
    await ServiceRepo(session).update_price(data["service_id"], price)
    await state.clear()
    await message.answer(
        f"✅ Price updated to <b>${price:.2f}</b>.",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin:upload_xlsx")
async def upload_xlsx_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    services = await ServiceRepo(session).all()
    if not services:
        await callback.answer("Create a service first.", show_alert=True)
        return
    await state.set_state(AdminStates.upload_service)
    await callback.message.edit_text(
        "📤 <b>Upload XLSX</b>\n\nSelect the target service:",
        reply_markup=admin_upload_services_kb(services),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("upsvc:"), AdminStates.upload_service)
async def upload_xlsx_service_selected(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    service_id = int(callback.data.split(":")[1])
    svc = await ServiceRepo(session).get(service_id)
    if not svc:
        await callback.answer("Service not found.", show_alert=True)
        return
    await state.update_data(service_id=service_id, mail_type=svc.mail_type)
    await state.set_state(AdminStates.upload_xlsx)
    await callback.message.edit_text(
        f"📤 Upload XLSX for <b>{svc.service_name}</b> [{svc.mail_type.upper()}]\n\n"
        "Please send the .xlsx file now.\n\n"
        "<i>Columns: A=Email, B=Password, C=Note (optional)</i>",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.upload_xlsx, F.document)
async def upload_xlsx_receive(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    doc: Document = message.document
    if not doc.file_name.lower().endswith(".xlsx"):
        await message.answer("❌ Please upload a valid <b>.xlsx</b> file.", parse_mode="HTML")
        return

    data = await state.get_data()
    service_id: int = data["service_id"]
    mail_type: str = data["mail_type"]

    bot = message.bot
    file = await bot.get_file(doc.file_id)
    file_bytes = await bot.download_file(file.file_path)
    raw = file_bytes.read()

    try:
        rows = parse_xlsx(raw)
    except Exception as exc:
        logger.error("XLSX parse error: %s", exc)
        await message.answer(f"❌ Failed to parse XLSX: {exc}")
        return

    if not rows:
        await message.answer("⚠️ No valid rows found in the file.")
        return

    count = await AccountRepo(session).bulk_insert(rows, mail_type, service_id)
    await state.clear()
    await message.answer(
        f"✅ Successfully imported <b>{count}</b> accounts.",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin:view_stock")
async def view_stock(callback: CallbackQuery, session: AsyncSession) -> None:
    services = await ServiceRepo(session).all()
    if not services:
        await callback.answer("No services found.", show_alert=True)
        return

    lines = ["📦 <b>Stock Overview</b>\n"]
    for svc in services:
        stock = await ServiceRepo(session).stock_count(svc.id)
        lines.append(
            f"• [{svc.mail_type.upper()}] <b>{svc.service_name}</b>  —  "
            f"${svc.price:.2f}  |  📦 {stock} available"
        )
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=admin_back_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:sold_accounts")
async def sold_accounts(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_sold(callback, session, page=0)


@router.callback_query(F.data.startswith("sold:"))
async def sold_paginate(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split(":")[1])
    await _show_sold(callback, session, page)


async def _show_sold(callback: CallbackQuery, session: AsyncSession, page: int) -> None:
    accounts, total = await AccountRepo(session).get_sold_accounts(
        offset=page * SOLD_PER_PAGE, limit=SOLD_PER_PAGE
    )
    tp = total_pages(total, SOLD_PER_PAGE)

    if total == 0:
        await callback.message.edit_text("💸 No sold accounts yet.", reply_markup=admin_back_kb())
        await callback.answer()
        return

    lines = [f"💸 <b>Sold Accounts</b>  (Page {page + 1}/{tp}  |  Total: {total})\n"]
    for acc in accounts:
        svc = acc.service.service_name if acc.service else "—"
        date = acc.purchase_time.strftime("%Y-%m-%d %H:%M") if acc.purchase_time else "—"
        lines.append(
            f"🔹 <code>{acc.email}</code>\n"
            f"   Service: {svc} | Buyer: {acc.buyer_id} | {date}\n"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=sold_pagination_kb(page, tp),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:user_stats")
async def user_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    user_count = await UserRepo(session).count()
    sold = await AccountRepo(session).count_sold()
    available = await AccountRepo(session).count_available()

    await callback.message.edit_text(
        f"👥 <b>Statistics</b>\n\n"
        f"Total Users: <b>{user_count}</b>\n"
        f"Accounts Sold: <b>{sold}</b>\n"
        f"Accounts In Stock: <b>{available}</b>",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.broadcast_message)
    await callback.message.edit_text(
        "📢 <b>Broadcast</b>\n\nSend the message you want to broadcast to all users.\n"
        "Supports HTML formatting.",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.broadcast_message)
async def broadcast_send(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_ids = await UserRepo(session).all_ids()
    bot = message.bot
    success = 0
    fail = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text or message.caption or "", parse_mode="HTML")
            success += 1
        except Exception:
            fail += 1
    await state.clear()
    await message.answer(
        f"📢 Broadcast complete.\n✅ Sent: {success}  ❌ Failed: {fail}",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin:edit_deposit")
async def edit_deposit_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    current = await SettingsRepo(session).get("deposit_text", "Not set.")
    await state.set_state(AdminStates.edit_deposit_text)
    await callback.message.edit_text(
        f"💳 <b>Edit Deposit Text</b>\n\nCurrent:\n{current}\n\n"
        "Send the new deposit text (HTML supported):",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.edit_deposit_text)
async def edit_deposit_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await SettingsRepo(session).set("deposit_text", message.text)
    await state.clear()
    await message.answer("✅ Deposit text updated.", reply_markup=admin_panel_kb())


@router.callback_query(F.data == "admin:manage_admins")
async def manage_admins(callback: CallbackQuery, session: AsyncSession) -> None:
    admin_ids = await AdminRepo(session).all_ids()
    ids_str = ", ".join(str(a) for a in admin_ids) or "None"
    await callback.message.edit_text(
        f"🔑 <b>Manage Admins</b>\n\nCurrent admins: {ids_str}",
        reply_markup=admin_manage_admins_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.add_admin_id)
    await callback.message.edit_text(
        "➕ <b>Add Admin</b>\n\nSend the Telegram user ID to promote:",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.add_admin_id)
async def add_admin_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        new_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be a number.")
        return
    await AdminRepo(session).add(new_id)
    await state.clear()
    await message.answer(
        f"✅ User <code>{new_id}</code> is now an admin.",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin:remove_admin")
async def remove_admin_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.set_state(AdminStates.remove_admin_select)
    await callback.message.edit_text(
        "🗑 <b>Remove Admin</b>\n\nSend the Telegram user ID to demote:",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.remove_admin_select)
async def remove_admin_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        rem_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid user ID.")
        return
    removed = await AdminRepo(session).remove(rem_id)
    await state.clear()
    if removed:
        await message.answer(
            f"✅ User <code>{rem_id}</code> removed from admins.",
            parse_mode="HTML",
            reply_markup=admin_panel_kb(),
        )
    else:
        await message.answer(f"❌ User <code>{rem_id}</code> was not an admin.", parse_mode="HTML")


@router.callback_query(F.data == "admin:set_balance")
async def set_balance_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.set_balance_user)
    await callback.message.edit_text(
        "💰 <b>Set User Balance</b>\n\nEnter the user's Telegram ID:",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.set_balance_user)
async def set_balance_user(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid user ID.")
        return
    user = await UserRepo(session).get(uid)
    if not user:
        await message.answer(f"❌ User <code>{uid}</code> not found.", parse_mode="HTML")
        return
    await state.update_data(target_user_id=uid)
    await state.set_state(AdminStates.set_balance_amount)
    await message.answer(
        f"User <code>{uid}</code> — current balance: <b>${user.balance:.2f}</b>\n\n"
        "Enter the new balance amount:",
        parse_mode="HTML",
    )


@router.message(AdminStates.set_balance_amount)
async def set_balance_amount(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = float(message.text.strip().replace(",", "."))
        if amount < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Invalid amount.")
        return
    data = await state.get_data()
    await UserRepo(session).set_balance(data["target_user_id"], amount)
    await state.clear()
    await message.answer(
        f"✅ Balance for user <code>{data['target_user_id']}</code> set to <b>${amount:.2f}</b>.",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
                             )
