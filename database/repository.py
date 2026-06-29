"""
database/repository.py — Repository pattern: all DB access goes here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Account, Admin, Service, Settings, User


class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, user_id: int, username: Optional[str] = None) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            user = User(user_id=user_id, username=username, balance=0.0)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        elif username and user.username != username:
            user.username = username
            await self.session.commit()
        return user

    async def get(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def update_balance(self, user_id: int, delta: float) -> float:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        user.balance = round(user.balance + delta, 6)
        await self.session.commit()
        return user.balance

    async def set_balance(self, user_id: int, amount: float) -> None:
        user = await self.session.get(User, user_id)
        if user:
            user.balance = round(amount, 6)
            await self.session.commit()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(User.user_id)))
        return result.scalar_one()

    async def all_ids(self) -> list[int]:
        result = await self.session.execute(select(User.user_id))
        return list(result.scalars().all())


class ServiceRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, mail_type: str, service_name: str, price: float) -> Service:
        svc = Service(mail_type=mail_type, service_name=service_name, price=price)
        self.session.add(svc)
        await self.session.commit()
        await self.session.refresh(svc)
        return svc

    async def get(self, service_id: int) -> Optional[Service]:
        return await self.session.get(Service, service_id)

    async def get_by_mail_type(self, mail_type: str) -> Sequence[Service]:
        result = await self.session.execute(
            select(Service).where(Service.mail_type == mail_type).order_by(Service.service_name)
        )
        return result.scalars().all()

    async def all(self) -> Sequence[Service]:
        result = await self.session.execute(select(Service).order_by(Service.mail_type, Service.service_name))
        return result.scalars().all()

    async def delete(self, service_id: int) -> bool:
        svc = await self.session.get(Service, service_id)
        if svc:
            await self.session.delete(svc)
            await self.session.commit()
            return True
        return False

    async def update_price(self, service_id: int, price: float) -> bool:
        svc = await self.session.get(Service, service_id)
        if svc:
            svc.price = price
            await self.session.commit()
            return True
        return False

    async def stock_count(self, service_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Account.id)).where(
                Account.service_id == service_id,
                Account.status == "available",
            )
        )
        return result.scalar_one()


class AccountRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_insert(self, rows: list[dict], mail_type: str, service_id: int) -> int:
        objs = [
            Account(
                email=r["email"],
                password=r["password"],
                note=r.get("note"),
                mail_type=mail_type,
                service_id=service_id,
                status="available",
            )
            for r in rows
        ]
        self.session.add_all(objs)
        await self.session.commit()
        return len(objs)

    async def purchase(self, service_id: int, buyer_id: int) -> Optional[Account]:
        stmt = (
            select(Account)
            .where(Account.service_id == service_id, Account.status == "available")
            .order_by(Account.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if account is None:
            return None
        account.status = "sold"
        account.buyer_id = buyer_id
        account.purchase_time = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def get_user_purchases(self, user_id: int, offset: int = 0, limit: int = 5) -> tuple[Sequence[Account], int]:
        count_result = await self.session.execute(
            select(func.count(Account.id)).where(Account.buyer_id == user_id)
        )
        total = count_result.scalar_one()
        result = await self.session.execute(
            select(Account)
            .where(Account.buyer_id == user_id)
            .order_by(Account.purchase_time.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def count_sold(self) -> int:
        result = await self.session.execute(
            select(func.count(Account.id)).where(Account.status == "sold")
        )
        return result.scalar_one()

    async def count_available(self) -> int:
        result = await self.session.execute(
            select(func.count(Account.id)).where(Account.status == "available")
        )
        return result.scalar_one()

    async def get_sold_accounts(self, offset: int = 0, limit: int = 20) -> tuple[Sequence[Account], int]:
        count_result = await self.session.execute(
            select(func.count(Account.id)).where(Account.status == "sold")
        )
        total = count_result.scalar_one()
        result = await self.session.execute(
            select(Account)
            .where(Account.status == "sold")
            .order_by(Account.purchase_time.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total


class AdminRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_admin(self, user_id: int) -> bool:
        admin = await self.session.get(Admin, user_id)
        return admin is not None

    async def add(self, user_id: int) -> None:
        if not await self.is_admin(user_id):
            self.session.add(Admin(admin_id=user_id))
            await self.session.commit()

    async def remove(self, user_id: int) -> bool:
        admin = await self.session.get(Admin, user_id)
        if admin:
            await self.session.delete(admin)
            await self.session.commit()
            return True
        return False

    async def all_ids(self) -> list[int]:
        result = await self.session.execute(select(Admin.admin_id))
        return list(result.scalars().all())


class SettingsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str, default: str = "") -> str:
        row = await self.session.get(Settings, key)
        return row.value if row else default

    async def set(self, key: str, value: str) -> None:
        row = await self.session.get(Settings, key)
        if row:
            row.value = value
        else:
            self.session.add(Settings(key=key, value=value))
        await self.session.commit()
