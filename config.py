"""
config.py — Loads and validates all environment variables.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val


# ── Bot ──────────────────────────────────────────────────────────────────────
BOT_TOKEN: str = _require("BOT_TOKEN")

# ── Database ─────────────────────────────────────────────────────────────────
DB_TYPE: str = os.getenv("DB_TYPE", "sqlite").lower()
SQLITE_PATH: str = os.getenv("SQLITE_PATH", "./mail_market.db")

MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB: str = os.getenv("MYSQL_DB", "mail_market")

# ── Admins ────────────────────────────────────────────────────────────────────
_raw_admins = os.getenv("ADMIN_IDS", "")
INITIAL_ADMIN_IDS: list[int] = [
    int(x.strip()) for x in _raw_admins.split(",") if x.strip().isdigit()
]

# ── Support ───────────────────────────────────────────────────────────────────
SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "support")

# ── Anti-spam ─────────────────────────────────────────────────────────────────
COOLDOWN_SECONDS: int = int(os.getenv("COOLDOWN_SECONDS", "3"))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mail_market_bot")


def get_db_url() -> str:
    """Return the SQLAlchemy async database URL based on DB_TYPE."""
    if DB_TYPE == "mysql":
        return (
            f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        )
    return f"sqlite+aiosqlite:///{SQLITE_PATH}"
