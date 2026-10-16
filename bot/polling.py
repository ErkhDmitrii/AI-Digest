import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError, TelegramAPIError
from config.settings import settings
from bot.handlers import dp, bot

log = logging.getLogger("bot.polling")

async def start_polling():
    """Запускает long-polling бота с обработкой ошибок."""
    log.info("Запуск Telegram-бота (long polling)...")
    
    max_retries = 5  # Максимальное число попыток перезапуска
    retry_delay = 5  # Задержка между попытками (сек)
    
    for attempt in range(max_retries):
        try:
            log.info(f"Попытка подключения №{attempt + 1}")
            
            # Очищаем вебхук и обновления
            await bot.delete_webhook(drop_pending_updates=True)
            
            # Запускаем поллинг
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                retry_after=retry_delay,
                timeout=settings.POLLING_TIMEOUT  # Таймаут поллинга
            )
            
            break  # Успешный запуск, выходим из цикла
            
        except (TelegramNetworkError, TelegramAPIError) as e:
            log.error(f"Ошибка подключения: {str(e)}")
            
            if attempt < max_retries - 1:
                log.info(f"Повторная попытка через {retry_delay} секунд...")
                await asyncio.sleep(retry_delay)
            else:
                log.error("Превышено максимальное число попыток подключения")
                raise
                
        except Exception as e:
            log.error(f"Неизвестная ошибка: {str(e)}")
            raise

# Дополнительные настройки можно добавить в конфиг:
# POLLING_TIMEOUT = 60  # Таймаут запроса в секундах
# RETRY_DELAY = 5  # Задержка между попытками
