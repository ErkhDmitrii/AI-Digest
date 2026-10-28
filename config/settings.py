"""Конфигурация приложения — читает .env и предоставляет settings."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # Telegram Bot
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    ADMIN_CHAT_ID: int = field(
        default_factory=lambda: int(os.getenv("ADMIN_CHAT_ID", "0")))
    TARGET_CHANNEL_ID: int = field(
        default_factory=lambda: int(os.getenv("TARGET_CHANNEL_ID", "0")))
    POLLING_TIMEOUT: int = field(default_factory=lambda: int(
        os.getenv("POLLING_TIMEOUT", "60")))

    # Telethon
    TELETHON_API_ID: int = field(
        default_factory=lambda: int(os.getenv("TELETHON_API_ID", "0")))
    TELETHON_API_HASH: str = field(
        default_factory=lambda: os.getenv("TELETHON_API_HASH", ""))
    TELETHON_SESSION: str = field(default_factory=lambda: os.getenv(
        "TELETHON_SESSION", "ai_digest_session"))

    # LLM
    LLM_API_KEY: str = field(
        default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    LLM_BASE_URL: str = field(default_factory=lambda: os.getenv(
        "LLM_BASE_URL", "https://api.openai.com/v1"))
    LLM_MODEL: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))

    # Schedule
    TIMEZONE: str = field(
        default_factory=lambda: os.getenv("TIMEZONE", "Asia/Tbilisi"))
    COLLECT_INTERVAL_HOURS: int = field(
        default_factory=lambda: int(os.getenv("COLLECT_INTERVAL_HOURS", "2")))
    COLLECT_INTERVAL_MINUTES: int = field(
        default_factory=lambda: int(os.getenv("COLLECT_INTERVAL_MINUTES", "0")))
    DIGEST_HOUR: int = field(
        default_factory=lambda: int(os.getenv("DIGEST_HOUR", "8")))

    # DB
    DB_PATH: str = field(
        default_factory=lambda: os.getenv("DB_PATH", "ai_digest.db"))

    # Paths
    PROJECT_ROOT: Path = field(default_factory=lambda: Path(
        __file__).resolve().parent.parent)
    PROMPTS_DIR: Path = field(default_factory=lambda: Path(
        __file__).resolve().parent / "prompts")

    # Whitelist sources (пониженный порог фильтрации)
    WHITELIST_SOURCES: list = field(default_factory=lambda: [
        "parliament.gov.ge",
        "nbg.gov.ge",
        "customs.gov.ge",
        "matsne.gov.ge",
        "economy.ge",
    ])

    # Категории
    CATEGORIES: list = field(default_factory=lambda: [
                             "laws", "banking", "market"])
    CATEGORY_LABELS: dict = field(default_factory=lambda: {
        "laws": "Законы и налоги",
        "banking": "Банки и платежи",
        "market": "Рынок и инфраструктура",
    })

    # Лимиты
    MAX_TELEGRAM_CHARS: int = 4096
    MAX_ITEMS_PER_CATEGORY: int = 5
    MIN_ARTICLE_LENGTH: int = 200
    MAX_ARTICLE_AGE_DAYS: int = 7

    @property
    def prompts(self) -> dict:
        """Загружает промпты из файлов при первом обращении."""
        result = {}
        for prompt_file in self.PROMPTS_DIR.glob("*.txt"):
            with open(prompt_file, encoding="utf-8") as f:
                result[prompt_file.stem] = f.read()
        return result


settings = Settings()
