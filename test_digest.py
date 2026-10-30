""""Быстрая отправка черновика в чат админа, чтобы не ждать 00:00 По Грузии"""
import asyncio
import logging

from bot.handlers import bot
from bot.scheduler import scheduled_digest

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        print("Запуск генерации дайджеста...")
        await scheduled_digest()
    except Exception as e:
        print(f"Ошибка при генерации: {e}")
    finally:
        # ЖЕЛЕЗОБЕТОННОЕ ЗАКРЫТИЕ СЕССИИ
        print("Закрытие сессии бота...")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())