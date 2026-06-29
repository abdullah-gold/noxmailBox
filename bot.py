"""
bot.py — Entry point. Sets up the bot, registers routers and middleware.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, INITIAL_ADMIN_IDS, SUPPORT_USERNAME, logger
from database import init_db, AsyncSessionFactory
from database.repository import AdminRepo, SettingsRepo
from handlers import admin_router, buy_router, common_router, my_accounts_router
from middlewares import AntiSpamMiddleware, DbSessionMiddleware


async def on_startup(bot: Bot) -> None:
    """Initialise DB, seed admins and default settings."""
    await init_db()

    async with AsyncSessionFactory() as session:
        admin_repo = AdminRepo(session)
        for admin_id in INITIAL_ADMIN_IDS:
            await admin_repo.add(admin_id)
            logger.info("Seeded admin: %d", admin_id)

        settings_repo = SettingsRepo(session)
        current_support = await settings_repo.get("support_username")
        if not current_support:
            await settings_repo.set("support_username", SUPPORT_USERNAME)

        current_deposit = await settings_repo.get("deposit_text")
        if not current_deposit:
            await settings_repo.set(
                "deposit_text",
                "💳 <b>How to Deposit</b>\n\n"
                "To top up your balance, please contact our support team:\n"
                f"👉 https://t.me/{SUPPORT_USERNAME}\n\n"
                "They will process your payment manually.",
            )

    logger.info("Bot started successfully.")


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(AntiSpamMiddleware())
    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(admin_router)
    dp.include_router(buy_router)
    dp.include_router(my_accounts_router)
    dp.include_router(common_router)

    dp.startup.register(lambda: on_startup(bot))

    logger.info("Starting polling…")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
