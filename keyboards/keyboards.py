"""
keyboards/keyboards.py — All keyboards used in the bot.
"""

from __future__ import annotations

from typing import Sequence

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models import Account, Service


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛒 BUY MAIL"), KeyboardButton(text="📦 MY ACCOUNTS"))
    builder.row(KeyboardButton(text="💰 BALANCE"), KeyboardButton(text="💳 DEPOSIT"))
    builder.row(KeyboardButton(text="🆘 SUPPORT"))
    return builder.as_markup(resize_keyboard=True)


def admin_main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛒 BUY MAIL"), KeyboardButton(text="📦 MY ACCOUNTS"))
    builder.row(KeyboardButton(text="💰 BALANCE"), KeyboardButton(text="💳 DEPOSIT"))
    builder.row(KeyboardButton(text="🆘 SUPPORT"), KeyboardButton(text="⚙️ ADMIN PANEL"))
    return builder.as_markup(resize_keyboard=True)


def mail_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📧 Hotmail / Outlook", callback_data="buy:hotmail")
    builder.button(text="📨 Gmail", callback_data="buy:gmail")
    builder.button(text="⬅️ Back", callback_data="back:main")
    builder.adjust(1)
    return builder.as_markup()


def services_kb(services: Sequence[Service], mail_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        builder.button(
            text=f"{svc.service_name}  —  ${svc.price:.2f}",
            callback_data=f"service:{svc.id}",
        )
    builder.button(text="⬅️ Back", callback_data="buy:back_mail")
    builder.adjust(1)
    return builder.as_markup()


def confirm_purchase_kb(service_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm Purchase", callback_data=f"confirm:{service_id}")
    builder.button(text="❌ Cancel", callback_data="back:main")
    builder.adjust(1)
    return builder.as_markup()


def accounts_pagination_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"myacc:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"myacc:{page + 1}"))
    builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Main Menu", callback_data="back:main"))
    return builder.as_markup()


def admin_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Service", callback_data="admin:add_service")
    builder.button(text="🗑 Delete Service", callback_data="admin:delete_service")
    builder.button(text="💲 Change Price", callback_data="admin:change_price")
    builder.button(text="📤 Upload XLSX", callback_data="admin:upload_xlsx")
    builder.button(text="📦 View Stock", callback_data="admin:view_stock")
    builder.button(text="💸 Sold Accounts", callback_data="admin:sold_accounts")
    builder.button(text="👥 User Statistics", callback_data="admin:user_stats")
    builder.button(text="📢 Broadcast", callback_data="admin:broadcast")
    builder.button(text="💳 Edit Deposit Text", callback_data="admin:edit_deposit")
    builder.button(text="🔑 Manage Admins", callback_data="admin:manage_admins")
    builder.button(text="💰 Set User Balance", callback_data="admin:set_balance")
    builder.adjust(2)
    return builder.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back to Admin Panel", callback_data="admin:back")
    return builder.as_markup()


def admin_services_kb(services: Sequence[Service], action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        builder.button(
            text=f"[{svc.mail_type.upper()}] {svc.service_name} — ${svc.price:.2f}",
            callback_data=f"{action}:{svc.id}",
        )
    builder.button(text="⬅️ Back", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def admin_mail_type_kb(action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📧 Hotmail / Outlook", callback_data=f"{action}:hotmail")
    builder.button(text="📨 Gmail", callback_data=f"{action}:gmail")
    builder.button(text="⬅️ Back", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def admin_upload_services_kb(services: Sequence[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        builder.button(
            text=f"[{svc.mail_type.upper()}] {svc.service_name}",
            callback_data=f"upsvc:{svc.id}",
        )
    builder.button(text="⬅️ Back", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def admin_manage_admins_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Admin", callback_data="admin:add_admin")
    builder.button(text="🗑 Remove Admin", callback_data="admin:remove_admin")
    builder.button(text="⬅️ Back", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def sold_pagination_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"sold:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"sold:{page + 1}"))
    builder.row(*nav)
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data="admin:back"))
    return builder.as_markup()
