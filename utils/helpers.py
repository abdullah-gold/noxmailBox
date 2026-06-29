"""
utils/helpers.py — Shared formatting and helper utilities.
"""

from __future__ import annotations

import math

from database.models import Account, Service


MAIL_TYPE_LABELS = {
    "gmail": "📨 Gmail",
    "hotmail": "📧 Hotmail / Outlook",
}


def mail_label(mail_type: str) -> str:
    return MAIL_TYPE_LABELS.get(mail_type.lower(), mail_type.capitalize())


def format_account_delivery(account: Account, service: Service | None = None) -> str:
    svc_name = service.service_name if service else "—"
    note = account.note or "—"
    return (
        f"✅ <b>Purchase Successful!</b>\n\n"
        f"📌 Service: <b>{svc_name}</b>  |  {mail_label(account.mail_type)}\n\n"
        f"📧 Email:\n<code>{account.email}</code>\n\n"
        f"🔑 Password:\n<code>{account.password}</code>\n\n"
        f"📝 Note:\n<code>{note}</code>"
    )


def format_account_history(account: Account, index: int) -> str:
    note = account.note or "—"
    date = account.purchase_time.strftime("%Y-%m-%d %H:%M") if account.purchase_time else "—"
    svc = account.service.service_name if account.service else "—"
    return (
        f"<b>#{index}  {svc}</b>  [{mail_label(account.mail_type)}]\n"
        f"📧 <code>{account.email}</code>\n"
        f"🔑 <code>{account.password}</code>\n"
        f"📝 <code>{note}</code>\n"
        f"🕐 {date}"
    )


def total_pages(total: int, per_page: int) -> int:
    return max(1, math.ceil(total / per_page))
