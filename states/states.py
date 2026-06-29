"""
states/states.py — All FSM state groups.
"""

from aiogram.fsm.state import State, StatesGroup


class BuyFlow(StatesGroup):
    selecting_mail_type = State()
    selecting_service = State()
    confirming = State()


class AdminStates(StatesGroup):
    add_service_mail_type = State()
    add_service_name = State()
    add_service_price = State()
    delete_service_select = State()
    change_price_select = State()
    change_price_value = State()
    upload_mail_type = State()
    upload_service = State()
    upload_xlsx = State()
    view_stock_service = State()
    edit_deposit_text = State()
    broadcast_message = State()
    add_admin_id = State()
    remove_admin_select = State()
    set_balance_user = State()
    set_balance_amount = State()
