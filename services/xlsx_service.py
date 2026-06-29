"""
services/xlsx_service.py — Parse uploaded XLSX files into account rows.
"""

from __future__ import annotations

import io
import logging
from typing import IO

import openpyxl

logger = logging.getLogger(__name__)


def parse_xlsx(file_data: bytes | IO[bytes]) -> list[dict]:
    if isinstance(file_data, bytes):
        file_data = io.BytesIO(file_data)

    wb = openpyxl.load_workbook(file_data, read_only=True, data_only=True)
    ws = wb.active

    rows: list[dict] = []
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if not row:
            continue
        email = str(row[0]).strip() if row[0] is not None else ""
        password = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        note = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""

        if not email or not password:
            continue
        if email.lower() in ("email", "e-mail", "mail"):
            continue

        rows.append({"email": email, "password": password, "note": note or None})

    wb.close()
    return rows
