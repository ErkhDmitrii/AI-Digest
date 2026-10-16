"""Точка входа микросервиса AI-Дайджест.

Архитектура: AsyncIOScheduler + aiogram polling в едином asyncio loop.
"""
import asyncio
import logging
import sys

from bot.polling import start_polling
from bot.scheduler import init_scheduler
from config.settings import settings
from db.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ai_digest.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("ai-digest")


async def main():
    log.info("Запуск AI-Дайджест v1.0")

    # 1. Инициализация БД
    init_db()

    # 2. Инициализация планировщика (AsyncIOScheduler)
    scheduler = init_scheduler()
    scheduler.start()  # Синхронный — регистрирует джобы в event loop
    log.info("Scheduler запущен, tz=%s", settings.TIMEZONE)

    # 3. Запуск бота (держит event loop активным)
    try:
        log.info("Запуск Telegram-бота...")
        await start_polling()
    except (KeyboardInterrupt, SystemExit):
        log.info("Остановка сервиса...")
        scheduler.shutdown(wait=False)
        log.info("Сервис остановлен")


if __name__ == "__main__":
    asyncio.run(main())
