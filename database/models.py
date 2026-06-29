"""
database/models.py — SQLAlchemy ORM models.
"""

from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float,
    ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(64), nullable=True)
    balance = Column(Float, default=0.0, nullable=False)
    join_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    purchases = relationship("Account", back_populates="buyer", foreign_keys="Account.buyer_id")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mail_type = Column(String(32), nullable=False)
    service_name = Column(String(64), nullable=False)
    price = Column(Float, nullable=False, default=0.0)

    accounts = relationship("Account", back_populates="service")

    __table_args__ = (
        UniqueConstraint("mail_type", "service_name", name="uq_service"),
    )


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(256), nullable=False)
    password = Column(String(256), nullable=False)
    note = Column(Text, nullable=True)
    mail_type = Column(String(32), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(16), default="available", nullable=False)
    buyer_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    purchase_time = Column(DateTime, nullable=True)

    service = relationship("Service", back_populates="accounts")
    buyer = relationship("User", back_populates="purchases", foreign_keys=[buyer_id])


class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(BigInteger, primary_key=True)


class Settings(Base):
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)
